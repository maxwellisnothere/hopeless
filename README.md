💡 Smart Classroom Lighting System (PHAM Controller)
Smart Classroom Lighting เป็นระบบควบคุมและจัดการแสงสว่างอัจฉริยะภายในห้องเรียน ซึ่งเป็นส่วนหนึ่งของระบบ PHAM Digital Twin พัฒนาขึ้นด้วย Python และ Streamlit โดยใช้ตรรกะ AI แบบ Rule-based เพื่อปรับระดับความสว่างและโหมดการทำงานตามสภาพแวดล้อมจริง

!

🌟 Key Features
Intelligent Mode Selection: ระบบแนะนำโหมดการทำงานอัตโนมัติ 6 รูปแบบ (Present, Lecture, Group, Auto Dim, Energy Save, และ Morning Mode)

Dynamic Auto-Brightness: ปรับระดับความสว่างตามจำนวนผู้ใช้งาน (Occupancy) โดยใช้การคำนวณแบบ Polynomial Curve Fitting

Digital Twin Synchronization: ซิงค์สถานะการทำงานไปยังฐานข้อมูล Supabase เพื่อแสดงผลบน React Digital Twin แบบ Real-time

Teacher Profiles & Courses: ระบบจดจำค่าความชอบส่วนตัวของอาจารย์แต่ละท่านและการตั้งค่าเริ่มต้นตามรายวิชา

Energy & Impact Analytics: บันทึกและวิเคราะห์การประหยัดพลังงาน พร้อมคำนวณค่าการลด Carbon Footprint และการประหยัดค่าไฟ

🛠 Technology Stack
หมวดหมู่	เทคโนโลยีที่ใช้
Frontend Framework	Streamlit
Language	Python 3.9+
AI/Logic Engine	Rule-based & Polynomial Regression Logic
Database	SQLite (Local) & Supabase/PostgreSQL (Cloud Sync)
Data Analysis	Pandas, Numpy
🧠 AI Decision Engine
ระบบใช้ 5-layer Architecture ในการประมวลผล โดยหัวใจหลักอยู่ที่ ai_logic.py ซึ่งคำนวณระดับความสว่าง (Brightness) จากจำนวนนักศึกษาที่ตรวจพบดังนี้:

Auto-Brightness Formula

เพื่อให้แสงสว่างเพิ่มขึ้นอย่างนุ่มนวลและเหมาะสม ระบบใช้สมการ:

Brightness=−0.008x 
2
 +2.2x+10.0
(เมื่อ x คือจำนวนผู้ใช้งานในห้อง โดยมีค่าสูงสุดที่ 50 คน)

Operational Modes

Present Mode: เมื่อเปิดโปรเจกเตอร์ ระบบจะหรี่ไฟด้านหน้าอัตโนมัติ

Morning Mode: ปรับแสงให้อุ่น (Warm) ในช่วงเช้า (06:00 - 09:00 น.)

Auto Dim: ปรับลดความสว่างลงเมื่อตรวจพบแสงธรรมชาติ (Natural Light > 500 Lux)

Energy Save: เข้าสู่โหมดประหยัดพลังงานเมื่อมีคนในห้องน้อยกว่า 5 คน

📊 Database Schema (Local & Cloud)
ระบบมีการจัดเก็บข้อมูลอย่างเป็นระบบผ่านตารางหลักดังนี้:

sensor_logs: เก็บค่า Lux, จำนวนคน และสถานะโปรเจกเตอร์

room_modes: บันทึกโหมดที่ถูกเลือกและผู้ที่สั่งการ (Actor)

energy_logs: บันทึก Baseline vs AI Energy เพื่อคำนวณความคุ้มค่า

teacher_profiles: เก็บค่าความชอบ (Preferred Mode) ของอาจารย์รายบุคคล

🚀 Getting Started
Clone the repository:

Bash
git clone https://github.com/maxwellisnothere/hopeless.git
Install dependencies:

Bash
pip install -r requirements.txt
Setup Environment:
สร้างไฟล์ .env และกำหนดค่าการเชื่อมต่อ Supabase/PostgreSQL

Run the application:

Bash
streamlit run app.py
Developed as part of the PHAM Project | Computer Engineering, Sripatum University

หวังว่าเนื้อหาชุดนี้จะช่วยให้หน้า GitHub ของคุณดูน่าเชื่อถือและสะท้อนความสามารถของโปรเจกต์ออกมาได้ดีที่สุดนะคะค่ะ! หากมีส่วนไหนอยากให้ปรับปรุงเพิ่มบอกได้เลยนะ
