from pathlib import Path
import json
from functools import lru_cache
from config import BASELINE_W, PROJ_BONUS, MODE_RATIO
from typing import Union, Optional, Tuple # - เพิ่มเพื่อรองรับ Python 3.9

BASE_DIR = Path(__file__).parent


@lru_cache(maxsize=1)
def load_app_styles() -> str:
    style_path = BASE_DIR / "assets" / "app_styles.css"
    return style_path.read_text(encoding="utf-8")

# - แก้ไขบรรทัดนี้ให้รองรับ Python 3.9
def calc_energy(mode: str, proj: bool, brightness_pct: Optional[Union[int, float]] = None) -> Tuple[int, int]:
    base = BASELINE_W * MODE_RATIO.get(mode, .90)
    if brightness_pct is not None:
        base *= max(0.1, min(1.0, float(brightness_pct) / 100.0))
    energy = int(round(min(base + (PROJ_BONUS if proj else 0), BASELINE_W)))
    return energy, BASELINE_W


@lru_cache(maxsize=1)
def _load_scene_template() -> str:
    template_path = BASE_DIR / "templates" / "scene_template.html"
    return template_path.read_text(encoding="utf-8")


def build_scene_html(
    cur_mode: str,
    new_proj: bool,
    cur_people: int,
    cur_lux: int,
    cur_teacher: str,
    cur_brightness: int,
    cur_saving: int,
) -> str:
    template = _load_scene_template()

    replacements = {
        "__PRESENT_PROJ_ON__": "true" if (new_proj and cur_mode == "PRESENT_MODE") else "false",
        "__CUR_MODE__":        cur_mode,
        "__CUR_PROJ_ON__":     "true" if new_proj else "false",
        "__CUR_PEOPLE__":      str(cur_people),
        "__CUR_LUX__":         str(cur_lux),
        "__CUR_TEACHER__":     json.dumps(cur_teacher or ""),
        "__CUR_BRIGHT__":      str(cur_brightness),
        "__CUR_SAVING__":      str(cur_saving),
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    return template