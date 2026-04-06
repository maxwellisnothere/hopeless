import streamlit as st
from database_pg import get_teacher_profiles, log_activity


def render_header():
    st.title("Smart Classroom Lighting")
    st.markdown(
        "<div style='color: #888; margin-top: -15px;'>"
        "<b>CPE495 – Group F</b> | AI-Powered Lighting Control System"
        "</div>",
        unsafe_allow_html=True,
    )


def render_status_badge(is_admin: bool, actor: str | None):
    lc = st.session_state.get("launch_course")
    if lc:
        st.markdown(
            f'<div class="status-badge status-teacher">'
            f'📚 <b>{lc["code"]}</b> — {lc["name"]} | 👨‍🏫 {lc["teacher"]}'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-badge status-admin">ระบบกำลังทำงาน — เลือกวิชาจากหน้าตารางเรียน</div>',
            unsafe_allow_html=True,
        )