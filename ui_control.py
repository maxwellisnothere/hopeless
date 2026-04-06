import random
import time
import streamlit as st
from ai_logic import SCENARIOS
from database_pg import get_teacher_profiles, get_courses, log_activity


MANUAL_MODE_OPTIONS = [
    "LECTURE_MODE",
    "PRESENT_MODE",
    "GROUP_MODE",
    "AUTO_DIM",
    "ENERGY_SAVE",
    "MORNING_MODE",
]

MANUAL_MODE_LABELS = {
    "LECTURE_MODE": "Lecture Mode — สว่างเต็มห้อง",
    "PRESENT_MODE": "Present Mode — โปรเจกเตอร์/สไลด์",
    "GROUP_MODE": "Group Mode — แสงสม่ำเสมอ",
    "AUTO_DIM": "Auto Dim — ลดแสงเมื่อแสงธรรมชาติมาก",
    "ENERGY_SAVE": "Energy Save — ประหยัดไฟ",
    "MORNING_MODE": "Morning Mode — แสงเช้า",
}

MANUAL_MODE_DESC = {
    "LECTURE_MODE": "Full brightness · No projector",
    "PRESENT_MODE": "Projector on · Dim front lights",
    "GROUP_MODE": "Even lighting · Collaboration",
    "AUTO_DIM": "Natural light detected · Dimming",
    "ENERGY_SAVE": "Few people · Most lights off",
    "MORNING_MODE": "Early class · Warm sunrise light",
}


def render_control_panel(is_admin: bool, actor: str | None, actor_role: str):
    
    if "selected_mode_btn" not in st.session_state:
        st.session_state["selected_mode_btn"] = None
        
    st.subheader("Control")
    chosen = None

    def mode_button(label, key):
        is_active = st.session_state["selected_mode_btn"] == key

        border_style = "2px solid #3b82f6" if is_active else "1px solid rgba(255,255,255,0.15)"
        glow = "0 0 12px rgba(59,130,246,0.6)" if is_active else "none"

        st.markdown(f"""
        <div style="
            border:{border_style};
            border-radius:12px;
            padding:4px;
            margin-bottom:8px;
            box-shadow:{glow};
        ">
        """, unsafe_allow_html=True)

        clicked = st.button(label, key=key, use_container_width=True)

        if clicked:
            st.session_state["selected_mode_btn"] = key

        st.markdown("</div>", unsafe_allow_html=True)

        return clicked

    def set_brightness_preset(preset: int) -> None:
        st.session_state["m_brightness"] = preset

    def reset_brightness_to_default() -> None:
        if st.session_state.get("m_proj_state"):
            st.session_state["m_brightness"] = 0
        else:
            default_bright = st.session_state.get("manual_default_brightness", 100)
            st.session_state["m_brightness"] = default_bright

    def sync_projector_brightness() -> None:
        if st.session_state.get("m_proj_state"):
            st.session_state["m_brightness"] = 0
        else:
            default_bright = st.session_state.get("manual_default_brightness", 100)
            st.session_state["m_brightness"] = default_bright

   

    # ✅ กัน error default_bright หาย
    default_bright = st.session_state.get("manual_default_brightness", 100)

    # ──  ──────────────────────────────────
    st.markdown("**โปรเจกเตอร์**")
    proj_state = st.toggle(
        "🎥 เปิด/ปิดโปรเจกเตอร์",
        value=st.session_state.get("m_proj_state", False),
        key="m_proj_state",
        on_change=sync_projector_brightness,
    )

    # ── สถานการณ์ ─────────────────────────────────────
    st.markdown("**Step 4 — เลือกสถานการณ์สำหรับห้อง**")
    sc_cols = st.columns(2)
    for i, sc in enumerate(SCENARIOS):
        if sc_cols[i % 2].button(sc["name"], use_container_width=True, key=f"sc_{i}"):
            st.session_state["selection_changed"] = False
            st.session_state["chosen_override"] = {
                **sc,
                "triggered_by": "scenario",
                "teacher_name": actor if not is_admin else None,
                "course_id":    st.session_state.get("active_course_id"),
            }

    st.markdown("---")

    # ── Manual Lighting ───────────────────────────────────────
    st.markdown("**Manual — ปรับแสงไฟ / โหมดการนำเสนอ**")
    st.caption("โหมดนี้ไม่ผูกกับจำนวนคนแล้ว เลือกโหมดแสงเองได้โดยตรง")

    manual_mode = st.selectbox(
        "โหมดแสง/การนำเสนอ",
        MANUAL_MODE_OPTIONS,
        format_func=lambda mode_key: MANUAL_MODE_LABELS.get(mode_key, mode_key),
        key="manual_mode",
    )

    proj_state = st.session_state.get("m_proj_state", proj_state)
    bright_default = 0 if proj_state else default_bright
    bright_label = "แสงเพิ่มเติมโหมดโปรเจกเตอร์ (%)" if proj_state else "หลอด Bright (%)"

    m_brightness = st.slider(
        bright_label,
        10,
        100,
        st.session_state.get("m_brightness", bright_default),
        key="m_brightness",
    )
    if proj_state:
        st.caption("โหมดโปรเจกเตอร์เริ่มที่ 0% และเพิ่มแสงเสริมได้ตามต้องการ")
    else:
        st.caption(f"ปรับลด/เพิ่มแสงได้จากค่า default {default_bright}%")

    bright_cols = st.columns(4)
    for idx, preset in enumerate([25, 50, 75, 100]):
        bright_cols[idx].button(
            f"{preset}%",
            use_container_width=True,
            key=f"bright_{preset}",
            on_click=set_brightness_preset,
            args=(preset,),
        )

    st.button(
        "↩กลับค่าแสงตามจำนวนนักศึกษา",
        use_container_width=True,
        key="reset_bright",
        on_click=reset_brightness_to_default,
    )

    m_hour = 10

    if "chosen_override" in st.session_state:
        chosen = st.session_state.pop("chosen_override")

    return chosen