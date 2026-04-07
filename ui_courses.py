"""
ui_courses.py — หน้าตารางเรียน (Course Grid)
ดึงข้อมูลจาก master_schedule (Real-time Sync) พร้อมระบบจำลองเวลา (Simulation Filter)
"""
import streamlit as st
from database_pg import get_master_schedule, get_teacher_profiles
from typing import Optional, List

# ── สีและไอคอนประจำโหมดวิชา ──────────────────────────────────
PROJ_COLOR = {True: "#8B5CF6", False: "#3B82F6"}
PROJ_LABEL = {True: "🎥 ใช้โปรเจกเตอร์", False: "📋 ไม่มีโปรเจกเตอร์"}

def _teacher_note(teacher_name: str, profiles: List) -> str:
    for p in profiles:
        if p[0] == teacher_name:
            return p[3] or ""
    return ""

# ══════════════════════════════════════════════════════════════
#  MAIN RENDER
# ══════════════════════════════════════════════════════════════

def render_course_grid(is_admin: bool, actor: Optional[str]):
    # ── CSS สำหรับ card ─────────────────────────────
    st.markdown("""
    <style>
    .course-card {
        background: linear-gradient(135deg, #0d1117, #0d1f2d);
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 20px 18px 16px;
        margin-bottom: 4px;
        transition: border-color .2s;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .course-card:hover { border-color: #3B82F6; }
    .cc-code {
        font-size: .72rem; font-weight: 700; letter-spacing: .12em;
        color: #60A5FA; text-transform: uppercase; margin-bottom: 4px;
    }
    .cc-name {
        font-size: 1.05rem; font-weight: 800; color: #f1f5f9;
        line-height: 1.3; margin-bottom: 8px;
    }
    .cc-teacher {
        font-size: .82rem; color: #94a3b8; margin-bottom: 6px;
    }
    .cc-badge {
        display: inline-block;
        padding: 2px 10px; border-radius: 20px;
        font-size: .72rem; font-weight: 700;
        margin-right: 4px; margin-top: 4px;
    }
    .cc-proj-on  { background:#8B5CF622; color:#A78BFA; border:1px solid #8B5CF644; }
    .cc-proj-off { background:#3B82F622; color:#60A5FA; border:1px solid #3B82F644; }
    .cc-day      { background:#10B98122; color:#34D399; border:1px solid #10B98144; }
    .cc-note     { font-size:.72rem; color:#64748b; margin-top:8px; font-style:italic; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("## 📚 ตารางเรียน (Master Schedule)")
    
    # ── 🕒 ตัวกรองเวลา (Simulation Filter) ──
    use_sim = st.toggle("🕒 เปิดโหมดจำลองเวลา (แสดงเฉพาะวิชาที่กำลังสอนในเวลานี้)")
    
    sim_day = None
    sim_time = None
    
    if use_sim:
        with st.container(border=True):
            st.markdown("**เลือกวันและเวลาที่ต้องการจำลอง:**")
            col1, col2 = st.columns(2)
            # ตัวเลือกตามรูปแบบที่เก็บในฐานข้อมูล
            days_options = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            time_options = [f"{str(h).zfill(2)}:00" for h in range(8, 18)]
            
            sim_day = col1.selectbox("วัน (Day)", days_options)
            sim_time = col2.selectbox("เวลา (Time)", time_options)

    st.divider()

    if is_admin:
        st.caption("แสดงตารางสอนในระบบที่ซิงค์จากฐานข้อมูลกลาง")
    else:
        st.caption(f"ตารางสอนของ **{actor}**")

    profiles = get_teacher_profiles()

    if is_admin:
        all_schedules = get_master_schedule(None)
        if not all_schedules:
            st.info("ไม่พบข้อมูลในตาราง master_schedule")
            return
            
        # 💡 กรองข้อมูลตามเวลาที่เลือก (ถ้าเปิดโหมดจำลอง)
        if use_sim:
            all_schedules = [s for s in all_schedules if s[1] == sim_day and s[2] == sim_time]
            if not all_schedules:
                st.warning(f"ไม่มีการเรียนการสอนในวัน {sim_day} เวลา {sim_time} น.")
                return

        # กรองเอาเฉพาะชื่ออาจารย์ที่ไม่เป็นค่าว่าง
        teachers = sorted(set(r[6] for r in all_schedules if r[6]))
        
        # จัดการข้อมูลที่ไม่มีชื่ออาจารย์ (Fallback)
        no_teacher_schedules = [r for r in all_schedules if not r[6]]
        if no_teacher_schedules:
            with st.expander(f"🏢 ไม่ระบุอาจารย์ ({len(no_teacher_schedules)} คาบ)", expanded=True):
                _render_cards(no_teacher_schedules, profiles)

        for teacher in teachers:
            t_schedules = [r for r in all_schedules if r[6] == teacher]
            with st.expander(f"👨‍🏫 {teacher} ({len(t_schedules)} คาบ)", expanded=True):
                _render_cards(t_schedules, profiles)
    else:
        my_schedules = get_master_schedule(actor)
        if not my_schedules:
            st.info("ไม่พบตารางสอนของคุณในระบบ")
            return
            
        # 💡 กรองข้อมูลตามเวลาที่เลือก (ถ้าเปิดโหมดจำลอง)
        if use_sim:
            my_schedules = [s for s in my_schedules if s[1] == sim_day and s[2] == sim_time]
            if not my_schedules:
                st.warning(f"คุณไม่มีการสอนในวัน {sim_day} เวลา {sim_time} น.")
                return
                
        _render_cards(my_schedules, profiles)

def _render_cards(schedules: List, profiles: List):
    """Render cards based on master_schedule data structure."""
    cols_per_row = 3
    for i in range(0, len(schedules), cols_per_row):
        row = schedules[i:i+cols_per_row]
        cols = st.columns(cols_per_row, gap="medium")
        for col, item in zip(cols, row):
            # โครงสร้างจาก database_pg.py: (id, day, start_time, end_time, code, name, teacher, proj)
            sid, sday, stime, _end_time, scode, sname, steacher, sproj = item
            
            # ป้องกันค่าที่เป็น None
            scode = scode or "N/A"
            sname = sname or "Unknown Course"
            steacher = steacher or "ไม่ระบุ"
            sproj = bool(sproj) if sproj is not None else True
            
            proj_cls = "cc-proj-on" if sproj else "cc-proj-off"
            proj_lbl = "🎥 โปรเจกเตอร์" if sproj else "📋 ไม่มีโปรเจกเตอร์"
            note = _teacher_note(steacher, profiles)

            with col:
                st.markdown(f"""
                <div class="course-card">
                  <div>
                    <div class="cc-code">{scode}</div>
                    <div class="cc-name">{sname}</div>
                    <div class="cc-teacher">👨‍🏫 {steacher}</div>
                    <div>
                      <span class="cc-badge cc-day">📅 {sday} @ {stime} น.</span>
                    </div>
                    <div>
                      <span class="cc-badge {proj_cls}">{proj_lbl}</span>
                    </div>
                    {f'<div class="cc-note">💬 {note}</div>' if note else ''}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("เริ่มการสอน →", key=f"launch_sc_{sid}", use_container_width=True):
                    # เก็บสถานะการสอนที่เลือก
                    st.session_state["active_course_id"] = sid
                    st.session_state["active_teacher"] = steacher
                    st.session_state["_proj_pending"] = sproj
                    st.session_state["launch_course"] = {
                        "id": sid, "teacher": steacher, "code": scode,
                        "name": sname, "day": sday, "time": stime, "proj": sproj,
                    }
                    st.session_state["page"] = "main"
                    st.rerun()