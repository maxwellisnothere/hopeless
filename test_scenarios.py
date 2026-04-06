"""
test_scenarios.py
รันทดสอบ 20 สถานการณ์ วัดผล Accuracy ของ AI
"""
from ai_logic import recommend_mode
from database_pg import save_all

# ─── 20 สถานการณ์ทดสอบ พร้อม Expected Mode ───────────────────
TEST_CASES = [
    # (lux, people, projector, hour, expected_mode, scenario_name)
    (250, 35, True,  13, "PRESENT_MODE",  "อาจารย์นำเสนอสไลด์ ตอนบ่าย"),
    (200, 40, True,  10, "PRESENT_MODE",  "นำเสนอโปรเจกต์ ตอนสาย"),
    (300, 30, True,  14, "PRESENT_MODE",  "สอนออนไลน์ผ่านโปรเจกเตอร์"),
    (350, 12, True,  11, "PRESENT_MODE",  "โปรเจกเตอร์เปิด คนพอมี"),

    (300, 40, False, 10, "LECTURE_MODE",  "สอนบนกระดาน คนเต็มห้อง"),
    (250, 38, False, 13, "LECTURE_MODE",  "บรรยายปกติ ตอนบ่าย"),
    (280, 35, False, 15, "LECTURE_MODE",  "คนเยอะ ไม่มีโปรเจกเตอร์"),

    (350, 20, False, 14, "GROUP_MODE",    "ทำงานกลุ่ม 20 คน"),
    (400, 15, False, 13, "GROUP_MODE",    "แบ่งกลุ่ม ทำ Workshop"),
    (320, 18, False, 16, "GROUP_MODE",    "นักศึกษากระจายทำงาน"),

    (600, 30, False, 12, "AUTO_DIM",      "แดดจัดช่วงเที่ยง"),
    (650, 25, False, 11, "AUTO_DIM",      "แสงธรรมชาติสว่างมาก"),
    (700, 20, False, 13, "AUTO_DIM",      "แสงภายนอกสูงมาก"),

    (200,  3, False, 17, "ENERGY_SAVE",   "ห้องเกือบว่าง ใกล้เลิก"),
    (150,  2, False, 18, "ENERGY_SAVE",   "คนเหลือน้อยมาก"),
    (250,  0, False, 16, "ENERGY_SAVE",   "ห้องว่าง ไม่มีคน"),
    (180,  4, False, 17, "ENERGY_SAVE",   "คนน้อยมาก เย็น"),

    (150, 15, False,  8, "MORNING_MODE",  "เช้า นักศึกษาเพิ่งเข้า"),
    (120, 20, False,  9, "MORNING_MODE",  "ช่วงเช้า คนเริ่มมา"),
    (160, 10, False,  8, "MORNING_MODE",  "เช้าตรู่ เพิ่งเปิดห้อง"),
]

def run_tests(save_to_db=True):
    print("=" * 65)
    print("Smart Classroom AI — Accuracy Test (20 Scenarios)")
    print("=" * 65)

    passed = 0
    results = []

    for i, (lux, people, proj, hour, expected, name) in enumerate(TEST_CASES, 1):
        mode, emoji, desc, energy, baseline = recommend_mode(lux, people, proj, hour)
        is_pass = mode == expected
        status = "PASS" if is_pass else "FAIL"
        if is_pass:
            passed += 1

        print(f"  {status} #{i:02d} | {emoji} {mode:<15} | คาดหวัง: {expected:<15} | {name}")

        if save_to_db:
            save_all(lux, people, proj, hour, mode, emoji, desc, energy, baseline, "test")

        results.append({
            "no": i,
            "name": name,
            "expected": expected,
            "got": mode,
            "pass": is_pass,
            "lux": lux,
            "people": people,
            "projector": proj,
            "hour": hour,
            "energy": energy,
            "saving": round((1 - energy/baseline)*100, 1)
        })

    accuracy = (passed / len(TEST_CASES)) * 100
    avg_saving = sum(r["saving"] for r in results) / len(results)

    print("=" * 65)
    print(f"\n  Accuracy : {passed}/{len(TEST_CASES)} = {accuracy:.1f}%  {'ผ่านเป้า >85%' if accuracy >= 85 else 'ยังไม่ถึงเป้า'}")
    print(f"  ประหยัดเฉลี่ย : {avg_saving:.1f}%  {'ผ่านเป้า >30%' if avg_saving >= 30 else 'ยังไม่ถึงเป้า'}")
    print(f"  บันทึก DB   : {'บันทึกแล้ว' if save_to_db else 'ข้าม'}")
    print("=" * 65)

    return results, accuracy, avg_saving

if __name__ == "__main__":
    run_tests(save_to_db=True)