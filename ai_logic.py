"""
ai_logic.py — Smart Light Room AI Decision Engine
--------------------------------------------------
Layer 2 of the 5-layer architecture.

Functions:
  recommend_mode()       → Rule-based mode selection (6 modes)
  auto_brightness_level() → Smooth people_count → brightness% mapping
  get_full_ai_state()    → Combined state dict for Streamlit
"""

from __future__ import annotations


# ══════════════════════════════════════════════════════════
#  SCENARIOS  (ใช้ใน ui_control.py → Step 3)
#  แต่ละ scenario มี people จริง ระบุได้เลย ไม่ต้องมี sensor
# ══════════════════════════════════════════════════════════

SCENARIOS = [
    {
        "name":      "บรรยายเต็มห้อง",
        "desc":      "นศ. เต็ม 50 คน ไม่มีโปรเจกเตอร์",
        "people":    50,
        "lux":       300,
        "projector": False,
        "hour":      10,
    },
    {
        "name":      "นำเสนองาน",
        "desc":      "เปิดโปรเจกเตอร์ หรีแสงด้านหน้า",
        "people":    40,
        "lux":       280,
        "projector": True,
        "hour":      13,
    },
    {
        "name":      "กลุ่มย่อย",
        "desc":      "นศ. 15–20 คน แสงสม่ำเสมอ",
        "people":    18,
        "lux":       320,
        "projector": False,
        "hour":      14,
    },
    {
        "name":      "แสงธรรมชาติสูง",
        "desc":      "กลางวันสว่าง ลดแสงในห้อง",
        "people":    30,
        "lux":       650,
        "projector": False,
        "hour":      12,
    },
    {
        "name":      "เช้าตรู่",
        "desc":      "คาบเช้า แสงอุ่น นศ. 15 คน",
        "people":    15,
        "lux":       150,
        "projector": False,
        "hour":      8,
    },
    {
        "name":      "ประหยัดไฟ",
        "desc":      "นศ. น้อยมาก เปิดไฟขั้นต่ำ",
        "people":    3,
        "lux":       200,
        "projector": False,
        "hour":      17,
    },
]


# ══════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════

MAX_PEOPLE   = 50
MIN_BRIGHT   = 10   # % — empty room baseline
MAX_BRIGHT   = 100  # % — full room

# Lux thresholds for natural-light detection
LUX_NATURAL_HIGH = 500   # bright outside → dim indoor lights
LUX_NATURAL_LOW  = 150   # dark/evening   → boost indoor lights

# Hour bands
MORNING_START = 6
MORNING_END   = 9
EVENING_START = 17

# People thresholds
PEOPLE_ENERGY_MAX = 5   # ≤ this → energy save mode
PEOPLE_GROUP_MAX  = 25  # ≤ this → group mode candidate


# ══════════════════════════════════════════════════════════
#  AUTO BRIGHTNESS ENGINE
#  Maps people_count (0–50) → brightness % (10–100)
#  Uses smooth anchored curve through 0/25/50 people targets
# ══════════════════════════════════════════════════════════

def auto_brightness_level(people_count: int | float) -> int:
    """
    Calculate target brightness percentage based on number of people.

        Algorithm:
            - Clamp input to [0, MAX_PEOPLE]
            - Use a smooth quadratic curve anchored at:
                    0 people  → 10%
                 25 people  → 60%
                 50 people  → 100%
            - Clamp output to [MIN_BRIGHT, MAX_BRIGHT]

    Returns:
      int — brightness percentage 10–100
    """
    clamped = max(0.0, min(float(MAX_PEOPLE), float(people_count)))

    # Fit through anchor points (0,10), (25,60), (50,100)
    brightness = (-0.008 * (clamped ** 2)) + (2.2 * clamped) + 10.0
    bounded = max(float(MIN_BRIGHT), min(float(MAX_BRIGHT), brightness))
    return int(round(bounded))


def brightness_to_lights(brightness_pct: int, base_lights: list[float]) -> list[float]:
    """
    Scale a 4-element light-intensity list by the auto brightness factor.

    Args:
      brightness_pct : int  — result from auto_brightness_level()
      base_lights    : list — mode's default [l0, l1, l2, l3] (0.0–1.0)

    Returns:
      list[float] — scaled intensities, each clamped to [0.0, 1.0]
    """
    factor = brightness_pct / 100.0
    return [min(1.0, max(0.0, l * factor)) for l in base_lights]


def combined_brightness_level(people_count: int | float, lux: float) -> int:
    """
    Combine occupancy brightness with natural light influence.

    - More people still raises target brightness.
    - Higher lux dims indoor lights more aggressively.
    - Lower lux allows a slight boost so the room does not feel flat.
    """
    people_brightness = auto_brightness_level(people_count)
    lux_value = max(0.0, float(lux))

    if lux_value >= 650:
        lux_factor = 0.68
    elif lux_value >= 500:
        lux_factor = 0.80
    elif lux_value >= 350:
        lux_factor = 0.92
    elif lux_value >= 200:
        lux_factor = 1.00
    elif lux_value >= 120:
        lux_factor = 1.06
    else:
        lux_factor = 1.12

    brightness = people_brightness * lux_factor
    bounded = max(float(MIN_BRIGHT), min(float(MAX_BRIGHT), brightness))
    return int(round(bounded))


# ══════════════════════════════════════════════════════════
#  RULE-BASED MODE RECOMMENDER
# ══════════════════════════════════════════════════════════

def recommend_mode(
    lux: float,
    people_count: int,
    projector_on: bool,
    hour: int,
) -> tuple:
    """
    Recommend a lighting mode based on sensor inputs.

    Returns tuple of 5 values (matching app.py unpacking):
      (mode_key, emoji, description, people_count, baseline_saving)

    Priority order:
      1. Projector on              → PRESENT_MODE
      2. Morning + people > 0      → MORNING_MODE
      3. Very few people (≤5)      → ENERGY_SAVE
      4. High natural lux (≥500)   → AUTO_DIM
      5. Small group (≤25)         → GROUP_MODE
      6. Default                   → LECTURE_MODE
    """
    is_morning = MORNING_START <= hour < MORNING_END

    # Mode metadata: (key, emoji, description, baseline_saving%)
    META = {
        "PRESENT_MODE": ("PRESENT_MODE", "", "Projector on · Dim front lights",     45),
        "LECTURE_MODE": ("LECTURE_MODE", "", "Full brightness · No projector",       10),
        "GROUP_MODE":   ("GROUP_MODE",   "", "Even lighting · Collaboration",        25),
        "AUTO_DIM":     ("AUTO_DIM",     "", "Natural light detected · Dimming",     50),
        "ENERGY_SAVE":  ("ENERGY_SAVE",  "", "Few people · Most lights off",         70),
        "MORNING_MODE": ("MORNING_MODE", "", "Early class · Warm sunrise light",     20),
    }

    # Rules
    if projector_on:
        key = "PRESENT_MODE"
    elif is_morning and people_count > 0:
        key = "MORNING_MODE"
    elif people_count <= PEOPLE_ENERGY_MAX:
        key = "ENERGY_SAVE"
    elif lux >= LUX_NATURAL_HIGH:
        key = "AUTO_DIM"
    elif people_count <= PEOPLE_GROUP_MAX:
        key = "GROUP_MODE"
    else:
        key = "LECTURE_MODE"

    mode_key, emoji, desc, baseline = META[key]
    return (mode_key, emoji, desc, people_count, baseline)


# ══════════════════════════════════════════════════════════
#  COMBINED STATE — single call for Streamlit
# ══════════════════════════════════════════════════════════

def get_full_ai_state(
    people_count: int,
    lux: float,
    projector_on: bool,
    hour: int,
    brightness_pct: int | float | None = None,
) -> dict:
    """
    One-stop function that returns everything the UI needs.

    Returns:
      {
        "mode"          : str   — recommended mode key
        "brightness"    : int   — auto brightness % (10–100)
        "lights_scaled" : list  — 4-element scaled light intensities
        "projector"     : bool
        "people"        : int
        "lux"           : float
        "hour"          : int
        "saving_est"    : int   — estimated energy saving %
        "reason"        : str   — human-readable explanation
      }
    """
    mode, _, _, _, _ = recommend_mode(lux, people_count, projector_on, hour)
    brightness  = int(round(brightness_pct)) if brightness_pct is not None else (0 if projector_on else auto_brightness_level(people_count))

    # Base light intensities per mode (mirrors scene_template.html MODES)
    BASE_LIGHTS = {
        "PRESENT_MODE" : [0.10, 0.65, 0.65, 0.10],
        "LECTURE_MODE" : [0.88, 1.00, 1.00, 0.88],
        "GROUP_MODE"   : [0.72, 0.72, 0.72, 0.72],
        "AUTO_DIM"     : [0.32, 0.10, 0.10, 0.32],
        "ENERGY_SAVE"  : [0.00, 0.42, 0.00, 0.00],
        "MORNING_MODE" : [0.82, 1.00, 1.00, 0.82],
    }

    base    = BASE_LIGHTS.get(mode, [0.88, 1.0, 1.0, 0.88])
    scaled  = brightness_to_lights(brightness, base)
    avg_int = sum(scaled) / 4.0
    saving  = int(round((1.0 - avg_int) * 100))

    # Human-readable reason
    reasons = {
        "PRESENT_MODE" : f"Projector ON — dimming side lights, brightness {brightness}%",
        "LECTURE_MODE" : f"Full class ({people_count} people) — maximum brightness {brightness}%",
        "GROUP_MODE"   : f"Small group ({people_count} people) — even lighting at {brightness}%",
        "AUTO_DIM"     : f"High natural light ({lux:.0f} lux) — auto-dimming to {brightness}%",
        "ENERGY_SAVE"  : f"Low occupancy ({people_count} people) — energy save at {brightness}%",
        "MORNING_MODE" : f"Morning class ({hour:02d}:xx) — warm light at {brightness}%",
    }

    return {
        "mode"         : mode,
        "brightness"   : brightness,
        "lights_scaled": scaled,
        "projector"    : projector_on,
        "people"       : people_count,
        "lux"          : lux,
        "hour"         : hour,
        "saving_est"   : saving,
        "reason"       : reasons.get(mode, f"Auto mode — brightness {brightness}%"),
    }


# ══════════════════════════════════════════════════════════
#  QUICK SELF-TEST  (python ai_logic.py)
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("── Auto Brightness Mapping ──")
    for n in [0, 5, 10, 20, 25, 35, 45, 50]:
        b = auto_brightness_level(n)
        bar = "█" * (b // 5) + "░" * (20 - b // 5)
        print(f"  {n:>2} people │ {bar} │ {b:>3}%")

    print("\n── Mode Recommendations ──")
    scenarios = [
        (50, 300, False, 10, "Full lecture"),
        (3,  300, False, 14, "Empty room"),
        (50, 300, True,  14, "Projector on"),
        (15, 300, False,  8, "Morning class"),
        (50, 650, False, 13, "Bright natural light"),
        (20, 300, False, 14, "Small group"),
    ]
    for people, lux, proj, hour, label in scenarios:
        state = get_full_ai_state(people, lux, proj, hour)
        print(f"  {label:<25} → {state['mode']:<15} | {state['brightness']:>3}% bright | save {state['saving_est']:>3}%")
        print(f"    {state['reason']}")