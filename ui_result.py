import streamlit as st
from ai_logic import recommend_mode
from database_pg import save_all, log_activity, get_course_by_id
from config import MODE_ICONS
from utils import calc_energy
from typing import Optional, Union # - เพิ่มเพื่อรองรับ Python 3.9

ACCENT_MAP = {
    "PRESENT_MODE":  "#8B5CF6",
    "LECTURE_MODE":  "#3B82F6",
    "GROUP_MODE":    "#10B981",
    "AUTO_DIM":      "#F59E0B",
    "ENERGY_SAVE":   "#06B6D4",
    "MORNING_MODE":  "#EC4899",
}

# - แก้ไข Type Hint จาก str | None เป็น Optional[str]
def render_result(is_admin: bool, actor: Optional[str], actor_role: str, chosen, new_proj: bool):
    st.subheader("AI Result")

    if "last_mode" not in st.session_state:
        st.info("เลือกสถานการณ์เพื่อดูผล AI")
        return

    mode      = st.session_state["last_mode"]
    sc        = st.session_state["last_sc"]
    t_name    = sc.get("teacher_name")
    course_id = sc.get("course_id")
    emoji     = MODE_ICONS.get(mode, "")

    energy_ai, baseline = calc_energy(mode, new_proj, sc.get("brightness_pct", 0 if sc.get("projector") else None))
    saving = round((1 - energy_ai / baseline) * 100, 1)
    acc    = ACCENT_MAP.get(mode, "#3B82F6")

    # Mode badge
    st.markdown(f"""<div style="background:linear-gradient(135deg,#0d1117,#0d1f2d);
        border-radius:14px;padding:18px;text-align:center;
        border:2px solid {acc}44;margin-bottom:12px;">
        <div style="font-size:2rem;font-weight:800;color:#fff;">
          {emoji} {mode.replace('_', ' ')}</div>
        <div style="font-size:.85rem;color:#888;margin-top:4px;">{sc.get('desc', '')}</div>
        </div>""", unsafe_allow_html=True)

    # Projector badge
    if new_proj:
        st.markdown('<div class="proj-on">Projector ON &nbsp;+80W</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="proj-off">Projector OFF</div>', unsafe_allow_html=True)

    st.markdown("---")

    # KPI mini cards
    r1, r2, r3 = st.columns(3)
    clr = "green" if saving >= 30 else "yellow" if saving >= 15 else "red"
    r1.markdown(f'<div class="kpi-card"><div class="kpi-val yellow">{energy_ai}W</div><div class="kpi-lbl">AI พลังงาน</div></div>', unsafe_allow_html=True)
    r2.markdown(f'<div class="kpi-card"><div class="kpi-val red">{baseline}W</div><div class="kpi-lbl">Baseline</div></div>', unsafe_allow_html=True)
    r3.markdown(f'<div class="kpi-card"><div class="kpi-val {clr}">-{saving}%</div><div class="kpi-lbl">ประหยัด</div></div>', unsafe_allow_html=True)

    st.markdown("")
    m1, m2 = st.columns(2)
    m1.metric("Lux",  sc["lux"])
    m2.metric("คน",   sc["people"])
    m1.metric("Hour", f"{sc['hour']:02d}:00")
    m2.metric("Proj", "ON " if new_proj else "OFF ")

    if course_id:
        # 1. ตรวจสอบก่อนว่าเป็นตัวเลขหรือไม่ เพื่อป้องกัน psycopg2 Error
        if str(course_id).isdigit():
            cd = get_course_by_id(int(course_id))
        else:
            # 2. ถ้าไม่ใช่ตัวเลข (เช่น "mw77sg635") ให้ลองหาด้วย Course Code แทน
            # *ต้องไปเพิ่มฟังก์ชัน get_course_by_code ใน database_pg.py ด้วยนะคะ
            from database_pg import get_course_by_code
            cd = get_course_by_code(str(course_id))

        if cd:
            st.markdown(
                f'<div class="chip">{cd[2]} — {cd[3]}</div>'
                f'<div class="chip">{cd[4]}h/wk</div>',
                unsafe_allow_html=True
            )

    if t_name:
        st.markdown(f'<div class="chip">{t_name}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Save button (manual save only)
    save_clicked = st.button("บันทึก", use_container_width=True, type="primary")

    if save_clicked:
        desc_ai = sc.get("mode_desc")
        if not desc_ai:
            _, _, desc_ai, _, _ = recommend_mode(sc["lux"], sc["people"], new_proj, sc["hour"])
        sv = save_all(
            sc["lux"], sc["people"], new_proj, sc["hour"],
            mode, emoji, desc_ai, energy_ai, baseline,
            triggered_by=sc.get("triggered_by", "manual"),
            teacher_name=t_name,
            course_id=course_id,
            projector_override=int(new_proj),
        )
        cinfo = ""
        if course_id:
            cd = get_course_by_id(course_id)
            if cd:
                cinfo = f" | {cd[2]}"
        log_activity(
            t_name or "System", actor_role, "MODE_CHANGE",
            f"{emoji}{mode} Lux={sc['lux']} Ppl={sc['people']} "
            f"Proj={'ON' if new_proj else 'OFF'} {sc['hour']:02d}:00 -{sv}%{cinfo}",
        )
        st.success(f"บันทึกแล้ว — ประหยัด {sv}%")