import streamlit as st
from database_pg import get_summary


def render_dashboard():
    st.markdown('<div class="dashboard-header">System Overview</div>', unsafe_allow_html=True)
    st.markdown("""
    <style>
    .kpi-card {
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    </style>
    """, unsafe_allow_html=True)

    total, avg_sv, mode_counts, proj_cnt, tot_saved = get_summary()

    with st.container():
        cols = st.columns(4, gap="medium")

    with cols[0]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">การวิเคราะห์ทั้งหมด</div>
            <div class="kpi-val green">{total} ครั้ง</div>
            <div class="kpi-sub">&nbsp;</div>
        </div>
    """, unsafe_allow_html=True)

    with cols[1]:
        saving_color = "green" if avg_sv >= 30 else "yellow"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">ประหยัดเฉลี่ย</div>
            <div class="kpi-val {saving_color}">{avg_sv}%</div>
            <div class="kpi-sub">Target: 30%</div>
        </div>
    """, unsafe_allow_html=True)

    with cols[2]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">เปิดโปรเจกเตอร์</div>
            <div class="kpi-val red">{proj_cnt} ครั้ง</div>
            <div class="kpi-sub">&nbsp;</div>
        </div>
    """, unsafe_allow_html=True)

    with cols[3]:
        val_display = f"{tot_saved/1000:.2f}" if tot_saved > 9999 else tot_saved
        unit = "kW" if tot_saved > 9999 else "W"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">พลังงานที่ประหยัดได้</div>
            <div class="kpi-val green">{val_display} {unit}</div>
            <div class="kpi-sub">&nbsp;</div>
        </div>
    """, unsafe_allow_html=True)