BASELINE_W = 688
PROJ_BONUS = 80

MODE_RATIO = {
    "PRESENT_MODE": .55,
    "MORNING_MODE": .80,
    "ENERGY_SAVE":  .30,
    "AUTO_DIM":     .50,
    "GROUP_MODE":   .75,
    "LECTURE_MODE": .90,
}

MODE_ICONS = {
    "PRESENT_MODE":  "",
    "LECTURE_MODE":  "",
    "GROUP_MODE":    "",
    "AUTO_DIM":      "",
    "ENERGY_SAVE":   "",
    "MORNING_MODE":  "",
}

DEFAULT_SESSION_STATE = {
    "role":             "admin",
    "active_teacher":   None,
    "active_course_id": None,
    "proj_override":    {},
}


def init_session_state(st):
    for key, value in DEFAULT_SESSION_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value