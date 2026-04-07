import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "classroom.db")
# ══════════════════════════════════════════════
#  INIT
# ══════════════════════════════════════════════
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1) sensor_logs
    c.execute('''CREATE TABLE IF NOT EXISTS sensor_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT,
        lux_value INTEGER, ldr_value INTEGER, pir_detected INTEGER,
        people_count INTEGER, projector_on INTEGER, hour INTEGER)''')

    # 2) room_modes
    c.execute('''CREATE TABLE IF NOT EXISTS room_modes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT,
        sensor_log_id INTEGER, mode_selected TEXT, mode_emoji TEXT,
        mode_desc TEXT, triggered_by TEXT, teacher_name TEXT,
        course_id INTEGER, projector_override INTEGER)''')
    _migrate(c, "room_modes", [
        ("teacher_name",       "TEXT"),
        ("course_id",          "INTEGER"),
        ("projector_override", "INTEGER"),
    ])

    # 3) teacher_profiles
    c.execute('''CREATE TABLE IF NOT EXISTS teacher_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_name TEXT UNIQUE,
        preferred_mode TEXT, preferred_lux INTEGER, notes TEXT,
        created_at TEXT, updated_at TEXT)''')

    # 4) courses — วิชาที่อาจารย์สอน
    c.execute('''CREATE TABLE IF NOT EXISTS courses (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_name  TEXT,
        course_code   TEXT,
        course_name   TEXT,
        hours_per_week INTEGER,
        default_projector INTEGER DEFAULT 0,
        created_at    TEXT,
        UNIQUE(teacher_name, course_code))''')

    # 5) energy_logs
    c.execute('''CREATE TABLE IF NOT EXISTS energy_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT,
        room_mode_id INTEGER, teacher_name TEXT, course_id INTEGER,
        energy_baseline INTEGER, energy_ai INTEGER,
        energy_saved_w INTEGER, energy_saved_pct REAL,
        cost_baseline REAL, cost_ai REAL)''')
    _migrate(c, "energy_logs", [
        ("teacher_name", "TEXT"),
        ("course_id",    "INTEGER"),
    ])

    # 6) activity_log
    c.execute('''CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT,
        actor TEXT, role TEXT, action TEXT, detail TEXT)''')

    # Seed teacher_profiles
    c.execute("SELECT COUNT(*) FROM teacher_profiles")
    if c.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.executemany('''INSERT INTO teacher_profiles
            (teacher_name,preferred_mode,preferred_lux,notes,created_at,updated_at)
            VALUES (?,?,?,?,?,?)''', [
            ("อ.สมชาย","PRESENT_MODE",300,"สอนโปรแกรมมิ่ง ใช้โปรเจกเตอร์บ่อย",now,now),
            ("อ.สุดา", "LECTURE_MODE",400,"สอนคณิตศาสตร์ เน้นกระดาน",          now,now),
            ("อ.วิชัย","GROUP_MODE",  350,"สอนแบบ Workshop",                   now,now),
            ("อ.นภา",  "AUTO_DIM",   500,"ชอบแสงธรรมชาติ",                    now,now),
        ])

    # Seed courses
    c.execute("SELECT COUNT(*) FROM courses")
    if c.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.executemany('''INSERT OR IGNORE INTO courses
            (teacher_name,course_code,course_name,hours_per_week,default_projector,created_at)
            VALUES (?,?,?,?,?,?)''', [
            ("อ.สมชาย","CPE201","Programming Fundamentals",3,1,now),
            ("อ.สมชาย","CPE495","Senior Project",         2,1,now),
            ("อ.สุดา", "MTH101","Calculus I",              3,0,now),
            ("อ.สุดา", "MTH201","Linear Algebra",          3,0,now),
            ("อ.วิชัย","CPE301","Data Structures",         3,1,now),
            ("อ.นภา",  "CPE401","AI Fundamentals",         2,1,now),
        ])

    conn.commit()
    conn.close()

def _migrate(c, table, columns):
    """Add missing columns safely."""
    existing = [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
    for col, col_type in columns:
        if col not in existing:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")


# ══════════════════════════════════════════════
#  COURSES CRUD
# ══════════════════════════════════════════════
def get_courses(teacher_name=None):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if teacher_name:
        c.execute('''SELECT id,course_code,course_name,hours_per_week,default_projector
                     FROM courses WHERE teacher_name=? ORDER BY course_code''', (teacher_name,))
    else:
        c.execute('''SELECT id,teacher_name,course_code,course_name,hours_per_week,default_projector
                     FROM courses ORDER BY teacher_name,course_code''')
    rows = c.fetchall(); conn.close(); return rows

def save_course(teacher_name, code, name, hours, default_proj):
    init_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''INSERT INTO courses
        (teacher_name,course_code,course_name,hours_per_week,default_projector,created_at)
        VALUES (?,?,?,?,?,?)
        ON CONFLICT(teacher_name,course_code) DO UPDATE SET
            course_name=excluded.course_name,
            hours_per_week=excluded.hours_per_week,
            default_projector=excluded.default_projector''',
        (teacher_name, code.strip().upper(), name.strip(), hours, int(default_proj), now))
    conn.commit(); conn.close()

def delete_course(course_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM courses WHERE id=?", (course_id,))
    conn.commit(); conn.close()

def get_course_by_id(course_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id,teacher_name,course_code,course_name,hours_per_week,default_projector FROM courses WHERE id=?", (course_id,))
    row = c.fetchone(); conn.close(); return row


# ══════════════════════════════════════════════
#  SAVE ALL
# ══════════════════════════════════════════════
def save_all(lux, people, projector_on, hour,
             mode, emoji, desc, energy_ai, baseline,
             triggered_by="manual", teacher_name=None,
             course_id=None, projector_override=None):
    init_db()
    now          = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ldr_value    = max(0, min(100, int((lux / 800) * 100)))
    pir_detected = 1 if people > 0 else 0
    saving_pct   = round((1 - energy_ai / baseline) * 100, 1)
    saved_w      = baseline - energy_ai
    cost_rate    = 5 / 1000

    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute('''INSERT INTO sensor_logs
        (timestamp,lux_value,ldr_value,pir_detected,people_count,projector_on,hour)
        VALUES (?,?,?,?,?,?,?)''',
        (now, lux, ldr_value, pir_detected, people, int(projector_on), hour))
    sensor_id = c.lastrowid

    c.execute('''INSERT INTO room_modes
        (timestamp,sensor_log_id,mode_selected,mode_emoji,mode_desc,
         triggered_by,teacher_name,course_id,projector_override)
        VALUES (?,?,?,?,?,?,?,?,?)''',
        (now, sensor_id, mode, emoji, desc, triggered_by,
         teacher_name, course_id,
         int(projector_override) if projector_override is not None else None))
    mode_id = c.lastrowid

    c.execute('''INSERT INTO energy_logs
        (timestamp,room_mode_id,teacher_name,course_id,
         energy_baseline,energy_ai,energy_saved_w,energy_saved_pct,
         cost_baseline,cost_ai)
        VALUES (?,?,?,?,?,?,?,?,?,?)''',
        (now, mode_id, teacher_name, course_id,
         baseline, energy_ai, saved_w, saving_pct,
         round(baseline * cost_rate, 4), round(energy_ai * cost_rate, 4)))

    conn.commit(); conn.close()
    return saving_pct


# ══════════════════════════════════════════════
#  ACTIVITY LOG
# ══════════════════════════════════════════════
def log_activity(actor, role, action, detail=""):
    init_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO activity_log (timestamp,actor,role,action,detail) VALUES (?,?,?,?,?)",
        (now, actor, role, action, detail))
    conn.commit(); conn.close()

def get_activity_log(limit=100):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT timestamp,actor,role,action,detail
                 FROM activity_log ORDER BY id DESC LIMIT ?''', (limit,))
    rows = c.fetchall(); conn.close(); return rows


# ══════════════════════════════════════════════
#  READ
# ══════════════════════════════════════════════
def get_sensor_logs(limit=50):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT timestamp,lux_value,ldr_value,pir_detected,
                        people_count,projector_on,hour
                 FROM sensor_logs ORDER BY id DESC LIMIT ?''', (limit,))
    rows = c.fetchall(); conn.close(); return rows

def get_room_modes(limit=50):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT rm.timestamp, rm.mode_emoji, rm.mode_selected,
                        rm.mode_desc, rm.triggered_by, rm.teacher_name,
                        c.course_code, rm.projector_override
                 FROM room_modes rm
                 LEFT JOIN courses c ON rm.course_id = c.id
                 ORDER BY rm.id DESC LIMIT ?''', (limit,))
    rows = c.fetchall(); conn.close(); return rows

def get_teacher_profiles():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT teacher_name,preferred_mode,preferred_lux,notes,updated_at
                 FROM teacher_profiles ORDER BY id''')
    rows = c.fetchall(); conn.close(); return rows

def save_teacher_profile(name, mode, lux, notes):
    init_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''INSERT INTO teacher_profiles
        (teacher_name,preferred_mode,preferred_lux,notes,created_at,updated_at)
        VALUES (?,?,?,?,?,?)
        ON CONFLICT(teacher_name) DO UPDATE SET
            preferred_mode=excluded.preferred_mode,
            preferred_lux=excluded.preferred_lux,
            notes=excluded.notes,
            updated_at=excluded.updated_at''',
        (name, mode, lux, notes, now, now))
    conn.commit(); conn.close()

def get_energy_logs(limit=50):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT e.timestamp, e.teacher_name,
                        c.course_code, c.course_name,
                        e.energy_baseline, e.energy_ai,
                        e.energy_saved_w, e.energy_saved_pct,
                        e.cost_baseline, e.cost_ai
                 FROM energy_logs e
                 LEFT JOIN courses c ON e.course_id = c.id
                 ORDER BY e.id DESC LIMIT ?''', (limit,))
    rows = c.fetchall(); conn.close(); return rows

def get_summary():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sensor_logs")
    total = c.fetchone()[0]
    c.execute("SELECT AVG(energy_saved_pct) FROM energy_logs")
    avg_saving = c.fetchone()[0] or 0
    c.execute("SELECT mode_selected,COUNT(*) FROM room_modes GROUP BY mode_selected ORDER BY 2 DESC")
    mode_counts = c.fetchall()
    c.execute("SELECT COUNT(*) FROM sensor_logs WHERE projector_on=1")
    proj_count = c.fetchone()[0]
    c.execute("SELECT SUM(energy_saved_w) FROM energy_logs")
    total_saved_w = c.fetchone()[0] or 0
    conn.close()
    return total, round(avg_saving,1), mode_counts, proj_count, int(total_saved_w)

def delete_teacher_profile(name):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM teacher_profiles WHERE teacher_name=?", (name,))
    conn.commit(); conn.close()

def clear_all_logs():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM sensor_logs")
    conn.execute("DELETE FROM room_modes")
    conn.execute("DELETE FROM energy_logs")
    conn.execute("DELETE FROM activity_log")
    conn.commit(); conn.close()

def get_monthly_impact_stats():
    """ดึงข้อมูลสรุปรายเดือนสำหรับ SQLite โดยใช้ strftime"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # เพื่อให้ดึงข้อมูลเป็นแบบ Dictionary ได้
    c = conn.cursor()
    
    # ใช้ strftime('%Y-%m', timestamp) แทน date_trunc
    sql = """
        SELECT 
            strftime('%Y-%m', timestamp) as month,
            SUM(energy_baseline) / 1000.0 as baseline_kwh,
            SUM(energy_ai) / 1000.0 as optimized_kwh,
            SUM(energy_saved_w) / 1000.0 as saved_kwh,
            SUM(cost_baseline - cost_ai) as saved_money_thb
        FROM energy_logs
        GROUP BY month 
        ORDER BY month
    """
    c.execute(sql)
    rows = [dict(row) for row in c.fetchall()]
    conn.close()

    # คำนวณ Carbon และต้นไม้
    for r in rows:
        r['carbon_reduction'] = round(float(r['saved_kwh']) * 0.4999, 2)
        r['trees_equivalent'] = round(r['carbon_reduction'] / 25.2, 2)
    return rows