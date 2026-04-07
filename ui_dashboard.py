import streamlit as st
from database_pg import get_summary
from database_pg import get_ai_anomaly_status

def render_dashboard():
    # ── 1. ดึงข้อมูลสถิติจาก Database ──
    stats = get_summary()

    # ฉีด CSS เพื่อให้การ์ดดูสวยและ Professional
    st.markdown("""
    <style>
    .kpi-card {
        background: #151515;
        border: 1px solid #333;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        transition: transform 0.3s ease;
    }
    .kpi-card:hover { border-color: #bef264; transform: translateY(-5px); }
    .kpi-label { font-size: 0.75rem; font-weight: 900; color: #888; text-transform: uppercase; letter-spacing: 0.1em; }
    .kpi-val { font-size: 2rem; font-weight: 900; margin: 10px 0; font-family: 'JetBrains Mono', monospace; }
    .kpi-sub { font-size: 0.7rem; color: #555; font-weight: bold; }
    .green { color: #bef264; }
    .yellow { color: #facc15; }
    .blue { color: #3b82f6; }
    .purple { color: #a855f7; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div style="margin-bottom: 2rem;"><h2 style="color:white; margin-bottom:0;">🏢 PHAM System Analytics</h2><p style="color:#666; font-size:0.9rem;">SPU Computer Engineering Smart Building Project</p></div>', unsafe_allow_html=True)
    
    # ── 2. แถวที่ 1: Instantaneous Power (กำลังไฟขณะนี้ - หน่วย kW) ──
    st.markdown("### ⚡ Real-time Power Status")
    col_kpi = st.columns(4, gap="medium")

    with col_kpi[0]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Baseline Power</div>
            <div class="kpi-val yellow">{stats['baseline_kw']} <span style="font-size:1rem">kW</span></div>
            <div class="kpi-sub">POTENTIAL LOAD</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi[1]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Optimized Power</div>
            <div class="kpi-val green">{stats['optimized_kw']} <span style="font-size:1rem">kW</span></div>
            <div class="kpi-sub">ACTUAL AI USAGE</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi[2]:
        saving_color = "green" if stats['avg_saving'] >= 13 else "yellow"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Efficiency Gain</div>
            <div class="kpi-val {saving_color}">{stats['avg_saving']}%</div>
            <div class="kpi-sub">AVG. SAVINGS</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi[3]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">AI Analysis</div>
            <div class="kpi-val blue">{stats['total']:,}</div>
            <div class="kpi-sub">TOTAL CYCLES</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── 3. แถวที่ 2: Environmental Impact (ยอดสะสม - หน่วย kWh) ──
    st.markdown("### 🌍 Environmental & Financial Impact (Cumulative)")
    col_impact = st.columns(3, gap="medium")

    with col_impact[0]:
        st.markdown(f"""
        <div class="kpi-card" style="border-bottom: 4px solid #10B981; background: linear-gradient(180deg, #151515 0%, #064e3b 300%);">
            <div class="kpi-label" style="color: #10B981;">MONEY SAVED</div>
            <div class="kpi-val" style="color: #fff; font-size: 2.2rem;">฿{stats['money_saved']:,.2f}</div>
            <div class="kpi-sub" style="color: #10B981;">BASED ON ฿4.5/kWh</div>
        </div>
        """, unsafe_allow_html=True)

    with col_impact[1]:
        st.markdown(f"""
        <div class="kpi-card" style="border-bottom: 4px solid #3B82F6; background: linear-gradient(180deg, #151515 0%, #1e3a8a 300%);">
            <div class="kpi-label" style="color: #3B82F6;">CARBON REDUCTION</div>
            <div class="kpi-val" style="color: #fff; font-size: 2.2rem;">{stats['carbon_kg']:,} <span style="font-size:1rem">kg CO₂e</span></div>
            <div class="kpi-sub" style="color: #3B82F6;">~{stats['trees']} TREES EQUIVALENT</div>
        </div>
        """, unsafe_allow_html=True)

    with col_impact[2]:
        st.markdown(f"""
        <div class="kpi-card" style="border-bottom: 4px solid #8B5CF6; background: linear-gradient(180deg, #151515 0%, #4c1d95 300%);">
            <div class="kpi-label" style="color: #8B5CF6;">ENERGY SAVED</div>
            <div class="kpi-val" style="color: #fff; font-size: 2.2rem;">{stats['total_saved_kw']:,} <span style="font-size:1rem">kWh</span></div>
            <div class="kpi-sub" style="color: #8B5CF6;">TOTAL PERFORMANCE</div>
        </div>
        """, unsafe_allow_html=True)

    # ── 4. แถวที่ 3: AI Insights & Projector ──
    st.divider()
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("""
            <div style="background:#1a1a1a; padding:20px; border-radius:15px; border:1px solid #333;">
                <h4 style="margin-top:0; color:#bef264;">🧠 AI Intelligence Insight</h4>
                <p style="color:#aaa; font-size:0.9rem;">
                    โมเดล Machine Learning วิเคราะห์ความสัมพันธ์ของข้อมูลด้วยความแม่นยำ <b>R² = 0.966</b> <br>
                    พบว่าจำนวนผู้ใช้งาน (Occupancy) และการตั้งค่า Setpoint มีผลต่อการใช้พลังงานสูงสุด <br>
                    ระบบได้ทำการปรับปรุงค่าความเย็นแบบ Adaptive เพื่อรักษาจุดสมดุลระหว่างความสบายและพลังงาน
                </p>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div style="background:#1a1a1a; padding:20px; border-radius:15px; border:1px solid #333; height:100%;">
                <div class="kpi-label">Projector Usage</div>
                <div style="font-size:2.5rem; font-weight:900; color:#3b82f6; margin:10px 0;">{stats['proj_count']} <span style="font-size:1rem">Times</span></div>
                <div class="kpi-sub">TOTAL ACTIVATIONS</div>
            </div>
        """, unsafe_allow_html=True)