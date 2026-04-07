"""
database_pg.py — ระบบจัดการฐานข้อมูล PostgreSQL (Supabase)
รองรับ Python 3.9 และการซิงค์ข้อมูล Master Schedule
"""
import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Union, Tuple

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
from datetime import datetime
from dotenv import load_dotenv

try:
    import streamlit as st
except Exception:
    st = None

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
_POOL = None

def _get_pool():
    global _POOL
    if _POOL is None:
        maxconn = int(os.getenv("PG_POOL_MAXCONN", "12"))
        _POOL = ThreadedConnectionPool(
            minconn=1,
            maxconn=maxconn,
            dsn=DATABASE_URL,
            sslmode="require",
        )
    return _POOL

@contextmanager
def _conn():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)

def _cache_data(ttl_sec: int = 10):
    def _decorator(func):
        if st is None:
            return func
        return st.cache_data(ttl=ttl_sec, show_spinner=False)(func)
    return _decorator

def _clear_cached_reads(*fn_names: str) -> None:
    if st is None:
        return
    for fn_name in fn_names:
        fn = globals().get(fn_name)
        if fn is not None and hasattr(fn, "clear"):
            fn.clear()

# ── helper ────────────────────────────────────────────────────
def _fetch(sql, params=()):
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

def _exec(sql, params=()):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            try:
                return cur.fetchone()
            except Exception:
                return None

# ══════════════════════════════════════════════
#  SAVE ALL
# ══════════════════════════════════════════════
def save_all(lux, people, projector_on, hour,
             mode, emoji, desc, energy_ai, baseline,
             triggered_by="manual", teacher_name=None,
             course_id=None, projector_override=None):
    now          = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ldr_value    = max(0, min(100, int((lux / 800) * 100)))
    pir_detected = 1 if people > 0 else 0
    saving_pct   = round((1 - energy_ai / baseline) * 100, 1)
    saved_w      = baseline - energy_ai
    cost_rate    = 5 / 1000

    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO sensor_logs
                   (timestamp,lux_value,ldr_value,pir_detected,people_count,projector_on,hour)
                   VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (now,lux,ldr_value,pir_detected,people,int(projector_on),hour))
            sensor_id = cur.fetchone()[0]

            cur.execute(
                """INSERT INTO room_modes
                   (timestamp,sensor_log_id,mode_selected,mode_emoji,mode_desc,
                    triggered_by,teacher_name,course_id,projector_override)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (now,sensor_id,mode,emoji,desc,triggered_by,
                 teacher_name,course_id,
                 int(projector_override) if projector_override is not None else None))
            mode_id = cur.fetchone()[0]

            cur.execute(
                """INSERT INTO energy_logs
                   (timestamp,room_mode_id,teacher_name,course_id,
                    energy_baseline,energy_ai,energy_saved_w,energy_saved_pct,
                    cost_baseline,cost_ai)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (now,mode_id,teacher_name,course_id,
                 baseline,energy_ai,saved_w,saving_pct,
                 round(baseline*cost_rate,4), round(energy_ai*cost_rate,4)))
        conn.commit()

    _clear_cached_reads("get_sensor_logs", "get_room_modes", "get_energy_logs", "get_summary")
    return saving_pct

# ══════════════════════════════════════════════
#  READ
# ══════════════════════════════════════════════
@_cache_data(ttl_sec=5)
def get_sensor_logs(limit=50):
    rows = _fetch(
        "SELECT id,timestamp,lux_value,ldr_value,pir_detected,people_count,projector_on,hour "
        "FROM sensor_logs ORDER BY id DESC LIMIT %s", (limit,))
    return [tuple(r.values()) for r in rows]

@_cache_data(ttl_sec=5)
def get_room_modes(limit=50):
    rows = _fetch(
        """SELECT rm.id,rm.timestamp,rm.mode_emoji,rm.mode_selected,rm.mode_desc,
                  rm.triggered_by,rm.teacher_name,c.course_code,rm.projector_override
           FROM room_modes rm
           LEFT JOIN courses c ON rm.course_id=c.id
           ORDER BY rm.id DESC LIMIT %s""", (limit,))
    return [tuple(r.values()) for r in rows]

@_cache_data(ttl_sec=20)
def get_teacher_profiles():
    rows = _fetch(
        "SELECT teacher_name,preferred_mode,preferred_lux,notes,updated_at "
        "FROM teacher_profiles ORDER BY teacher_name")
    return [tuple(r.values()) for r in rows]

def save_teacher_profile(name, mode, lux, notes):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _exec(
        """INSERT INTO teacher_profiles
           (teacher_name,preferred_mode,preferred_lux,notes,created_at,updated_at)
           VALUES(%s,%s,%s,%s,%s,%s)
           ON CONFLICT(teacher_name) DO UPDATE SET
             preferred_mode=EXCLUDED.preferred_mode,
             preferred_lux=EXCLUDED.preferred_lux,
             notes=EXCLUDED.notes, updated_at=EXCLUDED.updated_at""",
        (name,mode,lux,notes,now,now))
    _clear_cached_reads("get_teacher_profiles")

def delete_teacher_profile(name):
    _exec("DELETE FROM teacher_profiles WHERE teacher_name=%s", (name,))
    _clear_cached_reads("get_teacher_profiles")

# ── Master Schedule (New) ──────────────────────
@_cache_data(ttl_sec=20)
def get_master_schedule(teacher_name: Optional[str] = None):
    """ดึงข้อมูลจากตาราง master_schedule โดยอ่าน JSON ในคอลัมน์ subject"""
    sql = """
        SELECT 
            ms.id, 
            ms.day, 
            ms.time as start_time, 
            ms.time as end_time, 
            ms.subject->>'code' as course_code, 
            ms.subject->>'name' as course_name, 
            c.teacher_name, 
            c.default_projector as proj_default
        FROM master_schedule ms
        LEFT JOIN courses c ON (ms.subject->>'code') = c.course_code
    """
    
    if teacher_name:
        sql += " WHERE c.teacher_name = %s"
        rows = _fetch(sql + " ORDER BY ms.day, ms.time", (teacher_name,))
    else:
        rows = _fetch(sql + " ORDER BY c.teacher_name, ms.day, ms.time")
        
    return [tuple(r.values()) for r in rows]

@_cache_data(ttl_sec=20)
def get_courses(teacher_name=None):
    if teacher_name:
        rows = _fetch(
            "SELECT id,course_code,course_name,hours_per_week,default_projector "
            "FROM courses WHERE teacher_name=%s ORDER BY course_code", (teacher_name,))
    else:
        rows = _fetch(
            "SELECT id,teacher_name,course_code,course_name,hours_per_week,default_projector "
            "FROM courses ORDER BY teacher_name,course_code")
    return [tuple(r.values()) for r in rows]

def save_course(teacher_name, code, name, hours, default_proj):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _exec(
        """INSERT INTO courses
           (teacher_name,course_code,course_name,hours_per_week,default_projector,created_at)
           VALUES(%s,%s,%s,%s,%s,%s)
           ON CONFLICT(teacher_name,course_code) DO UPDATE SET
             course_name=EXCLUDED.course_name,
             hours_per_week=EXCLUDED.hours_per_week,
             default_projector=EXCLUDED.default_projector""",
        (teacher_name, code.strip().upper(), name.strip(), hours, int(default_proj), now))
    _clear_cached_reads("get_courses", "get_course_by_id")

def delete_course(course_id):
    _exec("DELETE FROM courses WHERE id=%s", (course_id,))
    _clear_cached_reads("get_courses", "get_course_by_id", "get_room_modes", "get_energy_logs")

@_cache_data(ttl_sec=20)
def get_course_by_id(course_id):
    rows = _fetch(
        "SELECT id,teacher_name,course_code,course_name,hours_per_week,default_projector "
        "FROM courses WHERE id=%s", (course_id,))
    return tuple(rows[0].values()) if rows else None

@_cache_data(ttl_sec=5)
def get_energy_logs(limit=50):
    rows = _fetch(
        """SELECT e.id,e.timestamp,e.teacher_name,c.course_code,c.course_name,
                  e.energy_baseline,e.energy_ai,e.energy_saved_w,e.energy_saved_pct,
                  e.cost_baseline,e.cost_ai
           FROM energy_logs e
           LEFT JOIN courses c ON e.course_id=c.id
           ORDER BY e.id DESC LIMIT %s""", (limit,))
    return [tuple(r.values()) for r in rows]

def get_summary():
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM sensor_logs) AS total,
                    (SELECT COALESCE(AVG(energy_saved_pct), 0) FROM energy_logs) AS avg_saving,
                    (
                        SELECT COALESCE(json_agg(m), '[]'::json)
                        FROM (
                            SELECT mode_selected, COUNT(*) AS count
                            FROM room_modes
                            GROUP BY mode_selected
                            ORDER BY count DESC
                        ) m
                    ) AS mode_counts,
                    (SELECT COUNT(*) FROM sensor_logs WHERE projector_on=1) AS proj_count,
                    (SELECT COALESCE(SUM(energy_saved_w), 0) FROM energy_logs) AS total_saved_w
                """
            )
            row = cur.fetchone() or {}

    mode_counts_raw = row.get("mode_counts") or []
    mode_counts = [(m.get("mode_selected"), m.get("count", 0)) for m in mode_counts_raw]
    total = int(row.get("total", 0) or 0)
    avg_saving = float(row.get("avg_saving", 0) or 0)
    proj_count = int(row.get("proj_count", 0) or 0)
    total_saved_w = int(row.get("total_saved_w", 0) or 0)
    return total, round(avg_saving, 1), mode_counts, proj_count, total_saved_w

def log_activity(actor, role, action, detail=""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _exec(
        "INSERT INTO activity_log (timestamp,actor,role,action,detail) VALUES(%s,%s,%s,%s,%s)",
        (now,actor,role,action,detail))
    _clear_cached_reads("get_activity_log")

@_cache_data(ttl_sec=5)
def get_activity_log(limit=100):
    rows = _fetch(
        "SELECT id,timestamp,actor,role,action,detail FROM activity_log ORDER BY id DESC LIMIT %s",
        (limit,))
    return [tuple(r.values()) for r in rows]

def clear_all_logs():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sensor_logs")
            cur.execute("DELETE FROM room_modes")
            cur.execute("DELETE FROM energy_logs")
            cur.execute("DELETE FROM activity_log")
        conn.commit()
    _clear_cached_reads("get_sensor_logs", "get_room_modes", "get_energy_logs", "get_activity_log", "get_summary")

def delete_sensor_log(log_id):
    _exec("DELETE FROM sensor_logs WHERE id=%s", (log_id,))
    _clear_cached_reads("get_sensor_logs", "get_room_modes", "get_energy_logs", "get_summary")

def delete_room_mode(mode_id):
    _exec("DELETE FROM room_modes WHERE id=%s", (mode_id,))
    _clear_cached_reads("get_room_modes", "get_energy_logs", "get_summary")

def delete_energy_log(log_id):
    _exec("DELETE FROM energy_logs WHERE id=%s", (log_id,))
    _clear_cached_reads("get_energy_logs", "get_summary")

def delete_activity_log(log_id):
    _exec("DELETE FROM activity_log WHERE id=%s", (log_id,))
    _clear_cached_reads("get_activity_log")

# ══════════════════════════════════════════════
#  SIMULATION SYNC
# ══════════════════════════════════════════════
