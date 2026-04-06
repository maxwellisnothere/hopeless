import streamlit as st
import streamlit.components.v1 as components
from utils import build_scene_html, calc_energy
from config import BASELINE_W
from ai_logic import auto_brightness_level


def render_scene(allow_projector_toggle: bool = True, height: int = 520):
    # ─────────────────────────────────────────────
    # HEADER
    # ─────────────────────────────────────────────
    st.markdown("ห้องเรียน 3D")

    cur_mode = st.session_state.get("last_mode", "LECTURE_MODE")
    cur_sc   = st.session_state.get("last_sc", {})
    cur_teacher = cur_sc.get("teacher_name") or st.session_state.get("active_teacher") or ""
    proj_state = st.session_state.get("m_proj_state", cur_sc.get("projector", False))

    # ─────────────────────────────────────────────
    # PROJECTOR CONTROL
    # ─────────────────────────────────────────────
    new_proj = bool(proj_state)
    st.session_state["proj_override"][cur_mode] = new_proj

    st.caption(f"🎥 โปรเจกเตอร์: {'ON' if new_proj else 'OFF'}")

    # ─────────────────────────────────────────────
    # ENERGY CALC
    # ─────────────────────────────────────────────
    cur_saving = int(
        round((1 - calc_energy(cur_mode, new_proj, cur_sc.get("brightness_pct"))[0] / BASELINE_W) * 100)
    )

    # ─────────────────────────────────────────────
    # BUILD SCENE HTML
    # ─────────────────────────────────────────────
    scene_html = build_scene_html(
        cur_mode   = cur_mode,
        new_proj   = new_proj,
        cur_people = cur_sc.get("people", 25),
        cur_lux    = cur_sc.get("lux", 300),
        cur_teacher = cur_teacher,
        cur_brightness = cur_sc.get("brightness_pct", 0 if cur_sc.get("projector") else auto_brightness_level(cur_sc.get("people", 25))),
        cur_saving = cur_saving,
    )

    # ─────────────────────────────────────────────
    # 🔥 FULL WIDTH WRAPPER (สำคัญมาก)
    # ─────────────────────────────────────────────
    full_html = f"""
    <div style="
        width:100%;
        height:{height}px;
        border-radius:18px;
        overflow:hidden;
        background:#020617;
        border:1px solid #1e293b;
    ">
        {scene_html}
    </div>
    """

    components.html(full_html, height=height, scrolling=False)

    return new_proj