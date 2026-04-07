"""
ui_courses.py — หน้าตารางเรียน (Course Grid)
Auto-Sync กับเวลาจำลองล่าสุด (ตัดสวิตช์ทิ้ง + ตัดวิชาซ้ำ 100%)
"""
import streamlit as st
from database_pg import get_master_schedule, get_teacher_profiles, get_latest_sim_time
from typing import Optional, List

PROJ_COLOR = {True: "#8B5CF6", False: "#3B82F6"}
PROJ_LABEL = {True: "🎥 ใช้โปรเจกเตอร์", False: "📋 ไม่มีโปรเจกเตอร์"}

def _teacher_note(teacher_name: str, profiles: List) -> str:
    for p in profiles:
        if p[0] == teacher_name:
            return p[3] or ""
    return ""

def _is_class_active(sim_time_str: str, class_time_str: str) -> bool:
    """เช็คว่าเวลาจำลอง อยู่ในช่วงเวลาที่กำลังเรียนอยู่หรือไม่แบบแม่นยำ"""
    try:
        if not class_time_str or not sim_time_str: return False
        
        sim_h = int(sim_time_str.split(":")[0])
        
        if "-" in class_time_str:
            start_str, end_str = class_time_str.split("-")
            start_h = int(start_str.strip().split(":")[0])
            end_h = int(end_str.strip().split(":")[0])
            # เรียน 08:00 - 11:00 แปลว่าคาบนี้จะโชว์แค่ตอน 8, 9, 10 โมง
            return start_h <= sim_h < end_h
        else:
            start_h = int(class_time_str.strip().split(":")[0])
            return sim_h == start_h
    except Exception:
        return False

# ══════════════════════════════════════════════════════════════
#  MAIN RENDER
# ══════════════════════════════════════════════════════════════

def render_course_grid(is_admin: bool, actor: Optional[str]):
    st.markdown("""
    <style>
    .course-card {
        background: linear-gradient(135deg, #0d1117, #0d1f2d); border: 1px solid #1e293b;
        border-radius: 16px; padding: 20px 18px 16px; margin-bottom: 4px;
        transition: border-color .2s; min-height: 220px; display: flex;
        flex-direction: column; justify-content: space-between;
    }
    .course-card:hover { border-color: #3B82F6; }
    .cc-code { font-size: .72rem; font-weight: 700; color: #60A5FA; margin-bottom: 4px; }
    .cc-name { font-size: 1.05rem; font-weight: 800; color: #f1f5f9; margin-bottom: 8px; }
    .cc-teacher { font-size: .82rem; color: #94a3b8; margin-bottom: 6px; }
    .cc-badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: .72rem; font-weight: 700; margin-right: 4px; }
    .cc-proj-on  { background:#8B5CF622; color:#A78BFA; border:1px solid #8B5CF644; }
    .cc-proj-off { background:#3B82F622; color:#60A5FA; border:1px solid #3B82F644; }
    .cc-day      { background:#10B98122; color:#34D399; border:1px solid #10B98144; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("## 📚 ตารางเรียน (Live Sync)")
    
    sim_day, sim_time = get_latest_sim_time()
    st.success(f"📡 ซิงค์ข้อมูลกับเวลาจำลอง: **{sim_day} | {sim_time} น.**")
    st.divider()

    profiles = get_teacher_profiles()
    all_schedules = get_master_schedule(None if is_admin else actor)
    
    # 💡 1. กรองวิชาที่ "กำลังเรียน" อยู่ในเวลานี้เท่านั้น
    active_schedules = [s for s in all_schedules if s[1] == sim_day and _is_class_active(sim_time, s[2])]

    # 💡 2. ตัดวิชาที่ซ้ำกัน (Deduplication) ทิ้งทั้งหมด
    display_schedules = []
    seen = set()
    for s in active_schedules:
        # กำหนดกุญแจเช็คความซ้ำ (วัน, เวลา, รหัสวิชา, ชื่ออาจารย์)
        key = (s[1], s[2], s[4], s[6])
        if key not in seen:
            seen.add(key)
            display_schedules.append(s)

    if not display_schedules:
        st.warning(f"ขณะนี้ (วัน {sim_day} เวลา {sim_time} น.) ยังไม่มีการสอนในตารางครับ")
        return

    if is_admin:
        teachers = sorted(set(r[6] for r in display_schedules if r[6]))
        no_teacher_schedules = [r for r in display_schedules if not r[6]]
        
        if no_teacher_schedules:
            with st.expander(f"🏢 ไม่ระบุอาจารย์ ({len(no_teacher_schedules)} คาบ)", expanded=True):
                _render_cards(no_teacher_schedules, profiles)

        for teacher in teachers:
            t_schedules = [r for r in display_schedules if r[6] == teacher]
            with st.expander(f"👨‍🏫 {teacher} ({len(t_schedules)} คาบ)", expanded=True):
                _render_cards(t_schedules, profiles)
    else:
        _render_cards(display_schedules, profiles)

def _render_cards(schedules: List, profiles: List):
    cols_per_row = 3
    for i in range(0, len(schedules), cols_per_row):
        row = schedules[i:i+cols_per_row]
        cols = st.columns(cols_per_row, gap="medium")
        for col, item in zip(cols, row):
            sid, sday, stime, _, scode, sname, steacher, sproj = item
            
            scode = scode or "N/A"
            sname = sname or "Course"
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
                      <span class="cc-badge cc-day">📅 {sday} @ {stime}</span>
                      <span class="cc-badge {proj_cls}">{proj_lbl}</span>
                    </div>
                    {f'<div style="font-size:.7rem; color:#64748b; margin-top:8px;">💬 {note}</div>' if note else ''}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # อัปเดตใช้ width="stretch" เพื่อแก้ Error เหลืองๆ ด้วยครับ
                if st.button("เริ่มการสอน →", key=f"launch_sc_{sid}_{scode}", width="stretch"):
                    st.session_state["active_course_id"] = sid
                    st.session_state["active_teacher"] = steacher
                    st.session_state["_proj_pending"] = sproj
                    st.session_state["launch_course"] = {
                        "id": sid, "teacher": steacher, "code": scode,
                        "name": sname, "day": sday, "time": stime, "proj": sproj,
                    }
                    st.session_state["page"] = "main"
                    st.rerun()