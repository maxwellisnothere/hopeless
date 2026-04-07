import pandas as pd
import streamlit as st
from typing import Optional, Union # - เพิ่มเพื่อรองรับ Python 3.9
from database_pg import (
    get_sensor_logs,
    get_room_modes,
    get_teacher_profiles,
    save_teacher_profile,
    delete_teacher_profile,
    get_energy_logs,
    get_activity_log,
    log_activity,
    get_courses,
    save_course,
    delete_course,
    delete_sensor_log,
    delete_room_mode,
    delete_energy_log,
    delete_activity_log,
)


def render_database_tabs(is_admin: bool, actor: Optional[str], actor_role: str): # - แก้ไข Type Hint
    st.subheader("ฐานข้อมูล")

    admin_sections = [
        "sensor_logs",
        "room_modes",
        "teacher_profiles",
        "Course",
        "energy_logs",
        "activity_log",
    ]
    teacher_sections = [
        "sensor_logs",
        "room_modes",
        "โปรไฟล์ของฉัน",
        "วิชาของฉัน",
        "energy_logs",
    ]

    section_options = admin_sections if is_admin else teacher_sections
    section = st.radio(
        "เลือกตาราง",
        section_options,
        horizontal=True,
        key="db_section_selector",
        label_visibility="collapsed",
    )

    # ── Sensor Logs ────────────────────────────────────────────
    if section == "sensor_logs":
        rows = get_sensor_logs(50)
        if rows:
            df = pd.DataFrame(rows, columns=[
                "ลำดับที่", "เวลา (TimeStamp)", "ค่าความสว่าง", "ตัวต้านทานแปรค่าตามแสง",
                "PIR", "จำนวนคนในห้อง", "Proj", "ชม.",
            ])
            df["PIR"] = df["PIR"].map({1: "✓", 0: ""})
            df["Proj"] = df["Proj"].map({1: "ON", 0: "OFF"})
            st.dataframe(df, use_container_width=True, height=280)

            if is_admin:
                st.markdown("**ลบข้อมูล Sensor Log:**")
                col_del1, col_del2 = st.columns([3, 1])
                with col_del1:
                    selected_id = st.selectbox(
                        "เลือกลำดับที่ต้องการลบ",
                        options=df["ลำดับที่"].tolist(),
                        format_func=lambda x: f"ลำดับที่ {x} - {df[df['ลำดับที่']==x]['เวลา (TimeStamp)'].values[0]}",
                        key="del_sensor",
                    )
                with col_del2:
                    if st.button("🗑️ ลบ", key="btn_del_sensor", type="secondary"):
                        delete_sensor_log(selected_id)
                        log_activity(actor or "Admin", actor_role, "DELETE_SENSOR_LOG", f"ID={selected_id}")
                        st.success(f"ลบ Sensor Log ลำดับที่ {selected_id} แล้ว")
                        st.rerun()
        else:
            st.info("ยังไม่มีข้อมูล")

    # ── Room Modes ─────────────────────────────────────────────
    elif section == "room_modes":
        rows = get_room_modes(50)
        if rows:
            df = pd.DataFrame(rows, columns=[
                "ลำดับที่", "เวลา", "🎭", "โหมด", "คำอธิบาย", "Trigger",
                "อาจารย์", "วิชา", "Proj",
            ])
            df["โหมด"] = df["🎭"] + " " + df["โหมด"].str.replace("_", " ")
            df["อาจารย์"] = df["อาจารย์"].fillna("—")
            df["วิชา"] = df["วิชา"].fillna("—")
            df["Proj"] = df["Proj"].map({1: "ON", 0: "OFF", None: "—"}).fillna("—")

            display_df = df.drop(columns=["🎭"])
            st.dataframe(display_df, use_container_width=True, height=280)

            if is_admin:
                st.markdown("**ลบข้อมูล Room Mode:**")
                col_del1, col_del2 = st.columns([3, 1])
                with col_del1:
                    selected_id = st.selectbox(
                        "เลือกลำดับที่ต้องการลบ",
                        options=df["ลำดับที่"].tolist(),
                        format_func=lambda x: f"ลำดับที่ {x} - {df[df['ลำดับที่']==x]['โหมด'].values[0]} ({df[df['ลำดับที่']==x]['เวลา'].values[0]})",
                        key="del_room_mode",
                    )
                with col_del2:
                    if st.button("🗑️ ลบ", key="btn_del_room_mode", type="secondary"):
                        delete_room_mode(selected_id)
                        log_activity(actor or "Admin", actor_role, "DELETE_ROOM_MODE", f"ID={selected_id}")
                        st.success(f"ลบ Room Mode ลำดับที่ {selected_id} แล้ว")
                        st.rerun()
        else:
            st.info("ยังไม่มีข้อมูล")

    # ── Teacher Profiles ───────────────────────────────────────
    elif section in ["teacher_profiles", "โปรไฟล์ของฉัน"]:
        profs_all = get_teacher_profiles()
        disp = profs_all if is_admin else [r for r in profs_all if r[0] == actor]
        if disp:
            st.dataframe(
                pd.DataFrame(disp, columns=["อาจารย์", "โหมด", "Lux", "หมายเหตุ", "อัปเดต"]),
                use_container_width=True,
                height=180,
            )

        st.markdown(f"**{'เพิ่ม/แก้ไข' if is_admin else 'แก้ไขโปรไฟล์'}**")
        with st.form("ep"):
            e1, e2 = st.columns(2)
            en = e1.text_input("ชื่อ", value="" if is_admin else (actor or ""), disabled=not is_admin)
            em = e2.selectbox("โหมด", ["PRESENT_MODE", "LECTURE_MODE", "GROUP_MODE", "AUTO_DIM", "ENERGY_SAVE", "MORNING_MODE"])
            el = e1.slider("Lux", 100, 700, 350)
            en2 = e2.text_input("หมายเหตุ")
            if st.form_submit_button("บันทึก"):
                nn = en if is_admin else actor
                if nn:
                    save_teacher_profile(nn, em, el, en2)
                    log_activity(actor or "Admin", actor_role, "EDIT_PROFILE", f"{nn}→{em} Lux={el}")
                    st.success(f"{nn}")
                    st.rerun()

        if is_admin and profs_all:
            dn = st.selectbox("ลบ", [r[0] for r in profs_all], key="del_t")
            if st.button(f"ลบ {dn}", type="secondary"):
                delete_teacher_profile(dn)
                log_activity("Admin", "admin", "DELETE_PROFILE", f"ลบ {dn}")
                st.rerun()

    # ── Courses ────────────────────────────────────────────────
    elif section in ["Course", "วิชาของฉัน"]:
        tctx = actor if not is_admin else None
        if is_admin:
            ap = get_teacher_profiles()
            ft = st.selectbox("กรองอาจารย์", ["— ทุกอาจารย์ —"] + [r[0] for r in ap], key="cof")
            tctx = None if ft == "— ทุกอาจารย์ —" else ft

        cs = get_courses(tctx)
        if cs:
            cols_c = ["id", "รหัส", "วิชา", "h/wk", "Proj default"] if tctx else ["id", "อาจารย์", "รหัส", "วิชา", "h/wk", "Proj default"]
            dfc = pd.DataFrame(cs, columns=cols_c)
            dfc["📽️ Proj default"] = dfc["Proj default"].map({1: "", 0: ""})
            st.dataframe(dfc.drop(columns=["id"]), use_container_width=True, height=200)

        if is_admin or actor:
            with st.form("ac"):
                f1, f2 = st.columns(2)
                if is_admin:
                    ap2 = [r[0] for r in get_teacher_profiles()]
                    ct = f1.selectbox("อาจารย์", ap2, key="cts")
                else:
                    ct = actor
                    f1.markdown(f"**{actor}**")
                cc = f2.text_input("รหัสวิชา", placeholder="CPE301")
                cn = f1.text_input("ชื่อวิชา", placeholder="Data Structures")
                ch = f2.slider("ชม./สัปดาห์", 1, 6, 3)
                cp = f1.toggle("Projector default", value=True)
                if st.form_submit_button("บันทึกวิชา"):
                    if cc and cn and ct:
                        save_course(ct, cc, cn, ch, cp)
                        log_activity(actor or "Admin", actor_role, "ADD_COURSE", f"{ct}:{cc}")
                        st.success(f"{cc}")
                        st.rerun()

        if is_admin and cs:
            do = {f"{r[2]}—{r[3]}[{r[1]}]": r[0] for r in cs} if not tctx else {f"{r[1]}—{r[2]}": r[0] for r in cs}
            dl = st.selectbox("ลบวิชา", list(do.keys()), key="dc")
            if st.button("ลบ", type="secondary"):
                delete_course(do[dl])
                log_activity("Admin", "admin", "DELETE_COURSE", dl)
                st.rerun()

    # ── Energy Logs ────────────────────────────────────────────
    elif section == "energy_logs":
        rows = get_energy_logs(50)
        if rows:
            df = pd.DataFrame(rows, columns=[
                "ลำดับที่", "เวลา", "อาจารย์", "รหัส", "วิชา",
                "Baseline(W)", "AI(W)", "ประหยัด(W)",
                "ประหยัด(%)", "ค่าไฟเดิม(฿)", "ค่าไฟ AI(฿)",
            ])
            df["อาจารย์"] = df["อาจารย์"].fillna("—")
            df["รหัส"] = df["รหัส"].fillna("—")
            df["วิชา"] = df["วิชา"].fillna("—")
            if not is_admin and actor:
                df = df[df["อาจารย์"] == actor]

            st.dataframe(df, use_container_width=True, height=280)

            if is_admin and len(df) > 0:
                st.markdown("**ลบข้อมูล Energy Log:**")
                col_del1, col_del2 = st.columns([3, 1])
                with col_del1:
                    selected_id = st.selectbox(
                        "เลือกลำดับที่ต้องการลบ",
                        options=df["ลำดับที่"].tolist(),
                        format_func=lambda x: f"ลำดับที่ {x} - {df[df['ลำดับที่']==x]['เวลา'].values[0]} (ประหยัด {df[df['ลำดับที่']==x]['ประหยัด(%)'].values[0]}%)",
                        key="del_energy",
                    )
                with col_del2:
                    if st.button("🗑️ ลบ", key="btn_del_energy", type="secondary"):
                        delete_energy_log(selected_id)
                        log_activity(actor or "Admin", actor_role, "DELETE_ENERGY_LOG", f"ID={selected_id}")
                        st.success(f"ลบ Energy Log ลำดับที่ {selected_id} แล้ว")
                        st.rerun()

            st.markdown("**กราฟ Baseline vs AI:**")
            dc = df[["เวลา", "Baseline(W)", "AI(W)"]].head(20).iloc[::-1].reset_index(drop=True)
            st.line_chart(dc.set_index("เวลา"))
        else:
            st.info("ยังไม่มีข้อมูล")

    # ── Activity Log (Admin) ──────────────────────────────────
    elif section == "activity_log" and is_admin:
        rows = get_activity_log(100)
        if rows:
            df = pd.DataFrame(rows, columns=["ลำดับที่", "เวลา", "ผู้ดำเนินการ", "Role", "Action", "รายละเอียด"])
            df["Role"] = df["Role"].map({"admin": "👑 admin", "teacher": "👨‍🏫 teacher"}).fillna(df["Role"])

            st.dataframe(df, use_container_width=True, height=280)

            st.markdown("**ลบข้อมูล Activity Log:**")
            col_del1, col_del2 = st.columns([3, 1])
            with col_del1:
                selected_id = st.selectbox(
                    "เลือกลำดับที่ต้องการลบ",
                    options=df["ลำดับที่"].tolist(),
                    format_func=lambda x: f"ลำดับที่ {x} - {df[df['ลำดับที่']==x]['Action'].values[0]} by {df[df['ลำดับที่']==x]['ผู้ดำเนินการ'].values[0]}",
                    key="del_activity",
                )
            with col_del2:
                if st.button("🗑️ ลบ", key="btn_del_activity", type="secondary"):
                    delete_activity_log(selected_id)
                    st.success(f"ลบ Activity Log ลำดับที่ {selected_id} แล้ว")
                    st.rerun()
        else:
            st.info("ยังไม่มี Activity")