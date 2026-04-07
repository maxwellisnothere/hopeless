import os
from supabase import create_client, Client
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

def get_supabase_client():
    url = os.environ.get("VITE_SUPABASE_URL_NEW") 
    key = os.environ.get("VITE_SUPABASE_ANON_KEY_NEW")
    if not url or not key:
        print("❌ ไม่พบ Supabase Config ใน .env")
        return None
    return create_client(url, key)

def sync_to_digital_twin(ai_state, teacher_name="Admin"):
    """ส่งสถานะ AI ไปยัง Supabase ตาราง room_modes"""
    supabase = get_supabase_client()
    if not supabase: return False
    
    try:
        data = {
            "mode_selected": ai_state["mode"],
            "mode_desc": ai_state["reason"],
            "people_count": ai_state["people"],
            "lux_value": ai_state["lux"],
            "projector_on": ai_state["projector"],
            "brightness_level": ai_state["brightness"],
            "teacher_name": teacher_name
        }
        supabase.table("room_modes").insert(data).execute()
        return True
    except Exception as e:
        print(f"❌ Sync Error: {e}")
        return False