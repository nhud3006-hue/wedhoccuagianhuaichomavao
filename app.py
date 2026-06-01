# ==============================
# STUDY GARDEN AI
# Version 2.0 - Hoàn chỉnh
# ==============================

import streamlit as st
import json
import os
import random
import hashlib
from datetime import datetime
import pandas as pd
import time

# === Thư viện AI (có thể thiếu, xử lý lỗi) ===
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

# === Các thư viện xử lý tài liệu (có thể thiếu, báo lỗi khi dùng) ===
try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False

# ==============================
# CẤU HÌNH TRANG
# ==============================
st.set_page_config(page_title="Study Garden AI", page_icon="🌸", layout="wide")

# ==============================
# CSS GIAO DIỆN
# ==============================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #EAF6FF, #F5FBFF, #FFFFFF);
}
.main-card {
    background: white;
    padding: 20px;
    border-radius: 25px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    margin-bottom: 15px;
}
.cute-title {
    font-size: 32px;
    font-weight: 700;
    color: #5B9BD5;
}
.stButton button {
    border-radius: 20px;
    background: #74b9ff;
    color: white;
    border: none;
    font-weight: 700;
}
.stButton button:hover {
    background: #5aa9ff;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# THƯ MỤC DỮ LIỆU
# ==============================
DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# ==============================
# HÀM ĐỌC/GHI JSON
# ==============================
def save_json(path, data):
    with open(path, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf8") as f:
            return json.load(f)
    return default

# ==============================
# HÀM HASH MẬT KHẨU
# ==============================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==============================
# QUẢN LÝ PASSWORD
# ==============================
PASSWORD_FILE = os.path.join(DATA_FOLDER, "password.json")
if not os.path.exists(PASSWORD_FILE):
    save_json(PASSWORD_FILE, {"password": hash_password("123456")})

# ==============================
# LOGIN
# ==============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 class='cute-title' style='text-align:center'>🌸 Study Garden AI 🌸</h1>", unsafe_allow_html=True)
    st.write("🐰 Chào mừng trở lại")
    pwd = st.text_input("Mật khẩu", type="password")
    if st.button("Đăng nhập"):
        data = load_json(PASSWORD_FILE, {})
        if hash_password(pwd) == data.get("password", ""):
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Sai mật khẩu")
    st.stop()

# ==============================
# KHỞI TẠO GROQ CLIENT
# ==============================
if "GROQ_API_KEY" in st.secrets and GROQ_AVAILABLE:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    client = None
    if not GROQ_AVAILABLE:
        st.sidebar.warning("⚠️ Chưa cài thư viện groq. Cài bằng: pip install groq")
    elif "GROQ_API_KEY" not in st.secrets:
        st.sidebar.warning("⚠️ Thiếu GROQ_API_KEY trong Secrets. Một số tính năng AI sẽ không hoạt động.")

# ==============================
# CÁC FILE DỮ LIỆU
# ==============================
TASK_FILE = os.path.join(DATA_FOLDER, "tasks.json")
XP_FILE = os.path.join(DATA_FOLDER, "xp.json")
STREAK_FILE = os.path.join(DATA_FOLDER, "streak.json")
PET_FILE = os.path.join(DATA_FOLDER, "pet.json")
FLASHCARD_FILE = os.path.join(DATA_FOLDER, "flashcards.json")
JOURNAL_FILE = os.path.join(DATA_FOLDER, "journal.json")
MEMORY_FILE = os.path.join(DATA_FOLDER, "learning_memory.json")
BADGE_FILE = os.path.join(DATA_FOLDER, "badges.json")
EVIDENCE_FILE = os.path.join(DATA_FOLDER, "evidence.json")
SHOP_FILE = os.path.join(DATA_FOLDER, "shop.json")

# ==============================
# DỮ LIỆU MẶC ĐỊNH
# ==============================
DEFAULT_XP = {"xp": 0, "level": 1}
DEFAULT_TASKS = []
DEFAULT_STREAK = {"days": 0, "last": ""}
DEFAULT_PET = {"level": 1}
DEFAULT_FLASHCARDS = []
DEFAULT_JOURNAL = []
DEFAULT_MEMORY = {"strengths": [], "weaknesses": []}
DEFAULT_BADGES = []
DEFAULT_EVIDENCE = [
    {"title": "Lão Hạc", "author": "Nam Cao", "content": "Tình phụ tử và lòng tự trọng của người nông dân."},
    {"title": "Vợ Nhặt", "author": "Kim Lân", "content": "Khát vọng sống trong hoàn cảnh đói khát."},
    {"title": "Chiếc Thuyền Ngoài Xa", "author": "Nguyễn Minh Châu", "content": "Cái nhìn đa chiều về cuộc sống."},
    {"title": "Rừng Xà Nu", "author": "Nguyễn Trung Thành", "content": "Tinh thần đấu tranh bất khuất."}
]
DEFAULT_SHOP = [
    {"name": "🐰 Nơ hồng", "cost": 100},
    {"name": "🌸 Vòng hoa", "cost": 150},
    {"name": "🥕 Cà rốt vàng", "cost": 200},
    {"name": "👑 Vương miện", "cost": 500}
]

# ==============================
# LOAD DỮ LIỆU
# ==============================
tasks = load_json(TASK_FILE, DEFAULT_TASKS)
xp_data = load_json(XP_FILE, DEFAULT_XP)
streak = load_json(STREAK_FILE, DEFAULT_STREAK)
pet = load_json(PET_FILE, DEFAULT_PET)
flashcards = load_json(FLASHCARD_FILE, DEFAULT_FLASHCARDS)
journals = load_json(JOURNAL_FILE, DEFAULT_JOURNAL)
memory_data = load_json(MEMORY_FILE, DEFAULT_MEMORY)
badges = load_json(BADGE_FILE, DEFAULT_BADGES)
evidences = load_json(EVIDENCE_FILE, DEFAULT_EVIDENCE)
shop_items = DEFAULT_SHOP  # chưa lưu lại, nhưng có thể mở rộng

# ==============================
# HÀM CẬP NHẬT XP & LEVEL
# ==============================
def add_xp(amount):
    global xp_data
    xp_data["xp"] += amount
    need = xp_data["level"] * 100
    while xp_data["xp"] >= need:
        xp_data["xp"] -= need
        xp_data["level"] += 1
        need = xp_data["level"] * 100
    save_json(XP_FILE, xp_data)

def update_streak():
    today = datetime.now().strftime("%Y-%m-%d")
    if streak["last"] != today:
        streak["days"] += 1
        streak["last"] = today
        save_json(STREAK_FILE, streak)
        # Thưởng XP cho việc duy trì chuỗi
        if streak["days"] % 5 == 0:
            add_xp(20)

update_streak()

# ==============================
# HÀM THƯỞNG XP (CÁC TÍNH NĂNG)
# ==============================
def reward_study(): add_xp(5)
def reward_quiz(): add_xp(10)
def reward_flashcard(): add_xp(8)
def reward_daily(): add_xp(15)

# ==============================
# HÀM MỞ KHÓA HUY HIỆU
# ==============================
def unlock_badge(name):
    if name not in badges:
        badges.append(name)
        save_json(BADGE_FILE, badges)

def check_badges():
    if xp_data["level"] >= 2:
        unlock_badge("🌱 Người khởi đầu")
    if xp_data["level"] >= 5:
        unlock_badge("🔥 Chăm chỉ")
    if xp_data["level"] >= 10:
        unlock_badge("👑 Học bá")
    if streak["days"] >= 7:
        unlock_badge("🏅 Chăm chỉ 7 ngày")
    if streak["days"] >= 30:
        unlock_badge("👑 Huyền thoại")

check_badges()

# ==============================
# HÀM TEXT TO SPEECH (NẾU CÓ)
# ==============================
def speak_text(text):
    if TTS_AVAILABLE:
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 170)
            engine.say(text)
            engine.runAndWait()
        except:
            pass

# ==============================
# HÀM XỬ LÝ TÀI LIỆU
# ==============================
def extract_text_from_file(uploaded_file):
    if uploaded_file is None:
        return ""
    filename = uploaded_file.name.lower()
    text = ""
    try:
        if filename.endswith(".pdf") and PDF_AVAILABLE:
            pdf = PdfReader(uploaded_file)
            for page in pdf.pages:
                text += page.extract_text() or ""
        elif filename.endswith(".docx") and DOCX_AVAILABLE:
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif filename.endswith(".pptx") and PPTX_AVAILABLE:
            prs = Presentation(uploaded_file)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
        elif filename.endswith(".txt"):
            text = uploaded_file.read().decode("utf-8")
        else:
            st.warning("Định dạng file không được hỗ trợ hoặc thiếu thư viện")
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
    return text

# ==============================
# SIDEBAR MENU
# ==============================
st.sidebar.title("🌸 Study Garden")
menu = st.sidebar.radio(
    "Menu",
    [
        "🏠 Trang chủ",
        "🎯 Nhiệm vụ",
        "📚 Học tập AI",
        "🍅 Pomodoro",
        "🎴 Flashcard",
        "📔 Nhật ký",
        "🤖 Gia sư AI",
        "📖 Dẫn chứng",
        "🏆 Thành tích",
        "🐰 Thú cưng",
        "🛍️ Cửa hàng",
        "📈 Thống kê",
        "👑 Hành trình",
        "📅 Lịch học",
        "🛣️ Lộ trình AI",
        "🌳 Cây tri thức"
    ]
)

st.sidebar.markdown("---")
welcome_msgs = ["🐰 Hôm nay cùng cố gắng nhé", "🌸 Mỗi ngày tiến bộ 1%", "🐱 Bạn đang làm rất tốt"]
st.sidebar.success(random.choice(welcome_msgs))
st.sidebar.info(random.choice(["🐰 Nghỉ chút rồi học tiếp nhé", "🐰 Mình tin bạn làm được"]))

# ==============================
# TRANG CHỦ
# ==============================
if menu == "🏠 Trang chủ":
    st.markdown("<h1 class='cute-title'>🌸 Study Garden AI</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("⭐ XP", xp_data["xp"])
    col2.metric("🌱 Level", xp_data["level"])
    col3.metric("🔥 Chuỗi học", streak["days"])
    st.markdown("---")
    st.subheader("🐰 Chào ngày mới")
    st.info("Mỗi ngày tiến bộ 1%, tương lai sẽ khác.")

# ==============================
# NHIỆM VỤ
# ==============================
elif menu == "🎯 Nhiệm vụ":
    st.title("🎯 Nhiệm vụ hôm nay")
    new_task = st.text_input("Thêm nhiệm vụ")
    if st.button("➕ Thêm") and new_task:
        tasks.append({"name": new_task, "done": False})
        save_json(TASK_FILE, tasks)
        st.rerun()
    for i, task in enumerate(tasks):
        done = st.checkbox(task["name"], value=task["done"], key=f"task_{i}")
        if done != task["done"]:
            tasks[i]["done"] = done
            save_json(TASK_FILE, tasks)
            if done:
                add_xp(2)
            st.rerun()
    st.markdown("---")
    if st.button("🎲 Quay nhiệm vụ"):
        pending = [t["name"] for t in tasks if not t["done"]]
        if pending:
            st.success(f"📚 Làm trước: {random.choice(pending)}")
        else:
            st.info("Đã hoàn thành hết nhiệm vụ")

# ==============================
# HỌC TẬP AI
# ==============================
elif menu == "📚 Học tập AI":
    st.title("📚 Học tập AI")
    if not client:
        st.error("AI chưa sẵn sàng. Vui lòng cài đặt GROQ_API_KEY.")
    else:
        uploaded = st.file_uploader("Tải tài liệu (PDF, DOCX, PPTX, TXT)", type=["pdf","docx","pptx","txt"])
        text_content = extract_text_from_file(uploaded) if uploaded else ""
        if uploaded and text_content:
            st.success("Đã đọc tài liệu")
            with st.expander("Xem nội dung trích xuất"):
                st.text(text_content[:2000])
            tab1, tab2, tab3, tab4 = st.tabs(["📖 Tóm tắt", "🧠 Feynman", "🎴 Flashcard", "❓ Quiz"])
            with tab1:
                if st.button("Tạo tóm tắt"):
                    prompt = f"Tóm tắt tài liệu sau ngắn gọn, có gạch đầu dòng:\n{text_content[:8000]}"
                    res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role":"user","content":prompt}])
                    st.write(res.choices[0].message.content)
            with tab2:
                if st.button("Giải thích dễ hiểu (Feynman)"):
                    prompt = f"Giải thích tài liệu như cho học sinh lớp 5:\n{text_content[:8000]}"
                    res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role":"user","content":prompt}])
                    st.write(res.choices[0].message.content)
            with tab3:
                if st.button("Tạo Flashcard"):
                    prompt = f"Hãy tạo 10 flashcard (câu hỏi và đáp án) từ tài liệu:\n{text_content[:8000]}"
                    res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role":"user","content":prompt}])
                    st.write(res.choices[0].message.content)
            with tab4:
                if st.button("Tạo Quiz trắc nghiệm"):
                    prompt = f"Tạo 10 câu hỏi trắc nghiệm có đáp án từ tài liệu:\n{text_content[:8000]}"
                    res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role":"user","content":prompt}])
                    st.write(res.choices[0].message.content)

# ==============================
# POMODORO
# ==============================
elif menu == "🍅 Pomodoro":
    st.title("🍅 Pomodoro")
    minute = st.selectbox("Thời gian (phút)", [25, 30, 45, 60])
    if st.button("🚀 Bắt đầu"):
        st.success(f"Bắt đầu phiên {minute} phút! Hẹn giờ...")
        with st.spinner("Đang chạy..."):
            time.sleep(minute * 60)
        st.balloons()
        st.info("Kết thúc phiên! Nghỉ ngơi 5 phút nhé.")
        add_xp(10)

# ==============================
# FLASHCARD
# ==============================
elif menu == "🎴 Flashcard":
    st.title("🎴 Flashcard")
    with st.form("new_flashcard"):
        question = st.text_input("Câu hỏi")
        answer = st.text_input("Đáp án")
        if st.form_submit_button("💾 Lưu thẻ"):
            if question and answer:
                flashcards.append({"question": question, "answer": answer})
                save_json(FLASHCARD_FILE, flashcards)
                st.success("Đã lưu")
                st.rerun()
    if flashcards:
        for i, card in enumerate(flashcards):
            with st.expander(card["question"]):
                st.success(card["answer"])
    else:
        st.info("Chưa có flashcard nào")

# ==============================
# NHẬT KÝ
# ==============================
elif menu == "📔 Nhật ký":
    st.title("📔 Nhật ký học tập")
    note = st.text_area("Hôm nay học gì?")
    if st.button("💾 Lưu") and note:
        journals.append({"date": datetime.now().strftime("%d/%m/%Y %H:%M"), "content": note})
        save_json(JOURNAL_FILE, journals)
        st.success("Đã lưu")
        st.rerun()
    for item in reversed(journals[-10:]):
        st.markdown(f"<div class='main-card'><b>{item['date']}</b><br>{item['content']}</div>", unsafe_allow_html=True)

# ==============================
# GIA SƯ AI
# ==============================
elif menu == "🤖 Gia sư AI":
    st.title("🤖 Gia sư AI")
    if not client:
        st.error("AI chưa sẵn sàng.")
    else:
        if "tutor_chat" not in st.session_state:
            st.session_state.tutor_chat = []
        for msg in st.session_state.tutor_chat:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        prompt = st.chat_input("Nhập câu hỏi...")
        if prompt:
            st.session_state.tutor_chat.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            with st.spinner("AI đang suy nghĩ..."):
                res = client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                answer = res.choices[0].message.content
            st.session_state.tutor_chat.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.write(answer)
                if st.button("🔊 Đọc", key="tts"):
                    speak_text(answer)

# ==============================
# DẪN CHỨNG VĂN HỌC
# ==============================
elif menu == "📖 Dẫn chứng":
    st.title("📖 Ngân hàng dẫn chứng")
    idx = datetime.now().timetuple().tm_yday % len(evidences)
    ev = evidences[idx]
    st.markdown(f"**📖 Hôm nay:** {ev['title']} - {ev['author']}\n\n{ev['content']}")
    yesterday = evidences[idx-1] if idx > 0 else None
    if yesterday:
        ans = st.text_input("🤔 Hôm qua em học dẫn chứng gì?")
        if st.button("Kiểm tra"):
            if yesterday["title"].lower() in ans.lower():
                st.success("🎉 Chính xác! +20 XP")
                add_xp(20)
            else:
                st.error(f"Đáp án: {yesterday['title']}")

# ==============================
# THÀNH TÍCH (HUY HIỆU)
# ==============================
elif menu == "🏆 Thành tích":
    st.title("🏆 Bộ sưu tập huy hiệu")
    if badges:
        for b in badges:
            st.success(b)
    else:
        st.info("Chưa mở khóa huy hiệu nào. Hãy chăm chỉ học tập!")

# ==============================
# THÚ CƯNG
# ==============================
elif menu == "🐰 Thú cưng":
    st.title("🐰 Thỏ học tập")
    st.markdown("# 🐰")
    st.write(f"Level thỏ: {pet['level']}")
    # Tăng level thỏ dựa trên level người dùng
    if xp_data["level"] >= pet["level"] * 2:
        pet["level"] += 1
        save_json(PET_FILE, pet)
        st.success("🐰 Thỏ đã lớn hơn!")

# ==============================
# CỬA HÀNG
# ==============================
elif menu == "🛍️ Cửa hàng":
    st.title("🛍️ Cửa hàng thỏ")
    for item in shop_items:
        col1, col2 = st.columns([4,1])
        col1.write(item["name"])
        col2.write(f"{item['cost']} XP")
        if col2.button("Mua", key=item["name"]):
            if xp_data["xp"] >= item["cost"]:
                add_xp(-item["cost"])
                st.success(f"Đã mua {item['name']}! (Trừ {item['cost']} XP)")
                st.rerun()
            else:
                st.warning("Không đủ XP")

# ==============================
# THỐNG KÊ NÂNG CAO
# ==============================
elif menu == "📈 Thống kê":
    st.title("📈 Thống kê học tập")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Level", xp_data["level"])
    col2.metric("XP", xp_data["xp"])
    col3.metric("Chuỗi học", streak["days"])
    col4.metric("Flashcard", len(flashcards))
    st.bar_chart(pd.DataFrame({
        "Chỉ số": ["XP", "Level", "Streak"],
        "Giá trị": [xp_data["xp"], xp_data["level"], streak["days"]]
    }).set_index("Chỉ số"))

# ==============================
# HÀNH TRÌNH
# ==============================
elif menu == "👑 Hành trình":
    st.title("👑 Hành trình học tập")
    st.markdown(f"**Level:** {xp_data['level']}  |  **XP:** {xp_data['xp']}  |  **Chuỗi ngày:** {streak['days']}")
    if xp_data["level"] < 5:
        st.info("🌱 Tân binh học tập")
    elif xp_data["level"] < 10:
        st.info("🔥 Người chăm chỉ")
    elif xp_data["level"] < 20:
        st.success("⭐ Học giả trẻ")
    else:
        st.success("👑 Học bá huyền thoại")

# ==============================
# LỊCH HỌC (ĐƠN GIẢN)
# ==============================
elif menu == "📅 Lịch học":
    st.title("📅 Kế hoạch tuần")
    days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
    for d in days:
        st.text_input(d, key=d)

# ==============================
# LỘ TRÌNH AI
# ==============================
elif menu == "🛣️ Lộ trình AI":
    st.title("🛣️ AI Lộ trình")
    if not client:
        st.error("AI chưa sẵn sàng.")
    else:
        goal = st.text_input("Mục tiêu học tập của bạn")
        if st.button("Tạo lộ trình") and goal:
            prompt = f"Hãy tạo lộ trình học tập chi tiết theo tuần cho mục tiêu: {goal}"
            res = client.chat.completions.create(model="llama-3.1-70b-versatile", messages=[{"role":"user","content":prompt}])
            st.write(res.choices[0].message.content)

# ==============================
# CÂY TRI THỨC
# ==============================
elif menu == "🌳 Cây tri thức":
    st.title("🌳 Cây tri thức")
    level = xp_data["level"]
    if level < 3:
        st.markdown("# 🌱")
    elif level < 8:
        st.markdown("# 🌿")
    elif level < 15:
        st.markdown("# 🌳")
    else:
        st.markdown("# 🌲")
    st.write(f"Cấp độ cây: {level}")

# ==============================
# KẾT THÚC
# ==============================
