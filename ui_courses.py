"""
ui_courses.py — หน้าตารางเรียน (Course Grid)
แสดง card รายวิชาทั้งหมด → กดเข้าหน้า Control ทันที
"""
import streamlit as st
from database_pg import get_courses, get_teacher_profiles

# ── สีและไอคอนประจำโหมดวิชา ──────────────────────────────────
PROJ_COLOR = {True: "#8B5CF6", False: "#3B82F6"}
PROJ_LABEL = {True: "🎥 ใช้โปรเจกเตอร์", False: "📋 ไม่มีโปรเจกเตอร์"}

# ── ตาราง: วัน/เวลา (สร้างจาก course_id seed เพื่อให้ดูสมจริง) ──
_DAY_SLOTS = [
    ("จันทร์",   "08:00–10:00"),
    ("อังคาร",   "10:00–12:00"),
    ("พุธ",      "13:00–15:00"),
    ("พฤหัส",   "09:00–11:00"),
    ("ศุกร์",    "14:00–16:00"),
    ("จันทร์",   "13:00–15:00"),
    ("อังคาร",   "08:00–10:00"),
]


def _day_slot(course_id: int) -> tuple[str, str]:
    idx = (course_id - 1) % len(_DAY_SLOTS)
    return _DAY_SLOTS[idx]


def _teacher_note(teacher_name: str, profiles: list) -> str:
    for p in profiles:
        if p[0] == teacher_name:
            return p[3] or ""
    return ""


# ══════════════════════════════════════════════════════════════
#  MAIN RENDER
# ══════════════════════════════════════════════════════════════

def render_course_grid(is_admin: bool, actor: str | None):
    """
    แสดงหน้าตารางเรียนแบบ card grid
    - is_admin=True  → เห็นทุกวิชา แบ่งกลุ่มตามอาจารย์
    - is_admin=False → เห็นเฉพาะวิชาของ actor
    """

    # ── CSS เพิ่มเติมสำหรับ card ─────────────────────────────
    st.markdown("""
    <style>
    .course-card {
        background: linear-gradient(135deg, #0d1117, #0d1f2d);
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 20px 18px 16px;
        margin-bottom: 4px;
        transition: border-color .2s;
        min-height: 210px;
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
    .cc-h        { background:#F59E0B22; color:#FCD34D; border:1px solid #F59E0B44; }
    .cc-note     { font-size:.72rem; color:#64748b; margin-top:8px; font-style:italic; }

    </style>
    """, unsafe_allow_html=True)

    # ── Header ───────────────────────────────────────────────
    st.markdown("## 📚 ตารางเรียน")
    if is_admin:
        st.caption("แสดงรายวิชาทั้งหมดในระบบ — กดการ์ดเพื่อเข้าควบคุมแสงห้องนั้น")
    else:
        st.caption(f"รายวิชาของ **{actor}** — กดการ์ดเพื่อเข้าควบคุมแสง")

    st.divider()

    # ── โหลดข้อมูล ────────────────────────────────────────────
    profiles = get_teacher_profiles()

    if is_admin:
        # จัดกลุ่มตามอาจารย์
        all_courses = get_courses(None)   # (id, teacher, code, name, h, proj)
        teachers = sorted(set(r[1] for r in all_courses))

        for teacher in teachers:
            t_courses = [r for r in all_courses if r[1] == teacher]
            note = _teacher_note(teacher, profiles)

            with st.expander(f"👨‍🏫 {teacher}  ({len(t_courses)} วิชา)", expanded=True):
                _render_cards(t_courses, teacher, profiles, is_admin, actor, admin_view=True)
    else:
        # Teacher: เห็นเฉพาะวิชาตัวเอง
        my_courses = get_courses(actor)   # (id, code, name, h, proj)
        if not my_courses:
            st.info("ยังไม่มีวิชา — ให้ Admin เพิ่มวิชาให้ก่อน")
            return
        # แปลงให้มี teacher field ด้วย
        expanded = [(r[0], actor, r[1], r[2], r[3], r[4]) for r in my_courses]
        _render_cards(expanded, actor, profiles, is_admin, actor, admin_view=False)




# ══════════════════════════════════════════════════════════════
#  CARD GRID
# ══════════════════════════════════════════════════════════════

def _render_cards(courses, teacher, profiles, is_admin, actor, admin_view=False):
    """Render N cards in 3-column grid."""
    if not courses:
        st.caption("ไม่มีวิชา")
        return

    cols_per_row = 3
    rows = [courses[i:i+cols_per_row] for i in range(0, len(courses), cols_per_row)]

    for row in rows:
        cols = st.columns(cols_per_row, gap="medium")
        for col, course in zip(cols, row):
            # course = (id, teacher, code, name, h, proj)
            cid, cteacher, ccode, cname, chours, cproj = course
            day, slot = _day_slot(cid)
            proj_cls   = "cc-proj-on" if cproj else "cc-proj-off"
            proj_lbl   = "🎥 โปรเจกเตอร์" if cproj else "📋 ไม่มีโปรเจกเตอร์"
            note = _teacher_note(cteacher, profiles)

            with col:
                st.markdown(f"""
                <div class="course-card">
                  <div>
                    <div class="cc-code">{ccode}</div>
                    <div class="cc-name">{cname}</div>
                    <div class="cc-teacher">👨‍🏫 {cteacher}</div>
                    <div>
                      <span class="cc-badge cc-day">📅 {day} {slot}</span>
                      <span class="cc-badge cc-h">⏱ {chours}h/wk</span>
                    </div>
                    <div>
                      <span class="cc-badge {proj_cls}">{proj_lbl}</span>
                    </div>
                    {f'<div class="cc-note">💬 {note}</div>' if note else ''}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(
                    "เข้าควบคุมแสง →",
                    key=f"enter_course_{cid}",
                    use_container_width=True,
                ):
                    # 🔥 เข้าหน้าหลักทันที ไม่มี modal
                    st.session_state["active_course_id"] = cid
                    st.session_state["active_teacher"]   = cteacher
                    st.session_state["_proj_pending"]    = bool(cproj)
                    st.session_state["launch_course"] = {
                        "id": cid, "teacher": cteacher, "code": ccode,
                        "name": cname, "hours": chours, "proj": bool(cproj),
                    }
                    st.session_state["page"] = "main"
                    st.rerun()

