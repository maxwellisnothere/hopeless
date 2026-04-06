import streamlit as st

def render_header():
    with st.container():
        hA, hB = st.columns([2.5, 1.5])
        with hA:
            st.title("Smart Classroom Lighting")
            st.markdown("<div style='color: #888; margin-top: -15px;'><b>CPE495 – Group F</b> | AI-Powered Lighting Control & SQLite System</div>", unsafe_allow_html=True)
        with hB:
            rc = st.radio("สิทธิ์การเข้าถึง", ["Admin", "Teacher"], horizontal=True, key="role_radio", label_visibility="collapsed")
            new_role = "admin" if "Admin" in rc else "teacher"
            if st.session_state.get("role") != new_role:
                st.session_state["role"] = new_role
                st.rerun()

def render_kpi(summary):
    total, avg_sv, mode_counts, proj_cnt, tot_saved = summary
    st.markdown("### System Overview")
    cols = st.columns(4, gap="medium")
    
    val_display = f"{tot_saved/1000:.2f} k" if tot_saved > 9999 else tot_saved
    unit = "kW" if tot_saved > 9999 else "W"
    
    with cols[0]:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">การวิเคราะห์ทั้งหมด</div><div class="kpi-val green">{total} ครั้ง</div></div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">ประหยัดเฉลี่ย</div><div class="kpi-val {"green" if avg_sv>=30 else "yellow"}">{avg_sv}%</div></div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">เปิดโปรเจกเตอร์</div><div class="kpi-val red">{proj_cnt} ครั้ง</div></div>', unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">พลังงานที่ประหยัดได้</div><div class="kpi-val green">{val_display} {unit}</div></div>', unsafe_allow_html=True)
    st.divider()