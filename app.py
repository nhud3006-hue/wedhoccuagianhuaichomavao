# ==============================
# STUDY GARDEN AI - HOÀN CHỈNH
# Tích hợp: Groq AI, Spaced Repetition, Cờ vua, Ghi âm, TTS, Camera
# Mật khẩu mặc định: 123456
# ==============================

import streamlit as st
import json
import os
import random
import hashlib
from datetime import datetime, timedelta
import pandas as pd
import time
import asyncio
import uuid

# === THƯ VIỆN AI ===
from groq import Groq

# === THƯ VIỆN TTS ===
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# === THƯ VIỆN XỬ LÝ FILE ===
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

# === THƯ VIỆN CỜ VUA ===
try:
    import chess
    import chess.svg
    CHESS_AVAILABLE = True
except ImportError:
    CHESS_AVAILABLE = False

# ==============================
# CẤU HÌNH TRANG
# ==============================
st.set_page_config(page_title="Study Garden AI", page_icon="🌸", layout="wide")

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
# QUẢN LÝ MẬT KHẨU MẶC ĐỊNH (123456)
# ==============================
PASSWORD_FILE = os.path.join(DATA_FOLDER, "password.json")
if not os.path.exists(PASSWORD_FILE):
    save_json(PASSWORD_FILE, {"password": hash_password("123456")})

# ==============================
# ĐĂNG NHẬP
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
            st.error("Sai mật khẩu. Mật khẩu mặc định: 123456")
    st.stop()

# ==============================
# KHỞI TẠO GROQ CLIENT (dùng st.secrets khuyến khích, nhưng giữ API key cũ để chạy)
# ==============================
GROQ_API_KEY = "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"  # Thay bằng key của bạn hoặc dùng st.secrets
client = Groq(api_key=GROQ_API_KEY)

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
SRS_FILE = os.path.join(DATA_FOLDER, "srs_data.json")

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
DEFAULT_SRS = []

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
srs_data = load_json(SRS_FILE, DEFAULT_SRS)

# ==============================
# HÀM CẬP NHẬT XP & STREAK
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
        if streak["days"] % 5 == 0:
            add_xp(20)
update_streak()

def reward_study(): add_xp(5)
def reward_quiz(): add_xp(10)
def reward_flashcard(): add_xp(8)
def reward_daily(): add_xp(15)

# ==============================
# HUY HIỆU
# ==============================
def unlock_badge(name):
    if name not in badges:
        badges.append(name)
        save_json(BADGE_FILE, badges)

def check_badges():
    if xp_data["level"] >= 2: unlock_badge("🌱 Người khởi đầu")
    if xp_data["level"] >= 5: unlock_badge("🔥 Chăm chỉ")
    if xp_data["level"] >= 10: unlock_badge("👑 Học bá")
    if streak["days"] >= 7: unlock_badge("🏅 Chăm chỉ 7 ngày")
    if streak["days"] >= 30: unlock_badge("👑 Huyền thoại")
    # Badge cho SRS
    if len(srs_data) >= 10:
        unlock_badge("📚 Vua lặp lại")
check_badges()

# ==============================
# TEXT TO SPEECH (pyttsx3 - cũ)
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
# TTS VOICE EDGE (async)
# ==============================
async def edge_tts_speak(text, filename="reply.mp3"):
    if EDGE_TTS_AVAILABLE:
        communicate = edge_tts.Communicate(text, voice="vi-VN-NamMinhNeural")
        await communicate.save(filename)
        return filename
    return None

def run_async_tts(text):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(edge_tts_speak(text))
    except:
        return None

# ==============================
# HÀM TRÍCH XUẤT TÀI LIỆU
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
# HÀM SPACED REPETITION
# ==============================
# Chu kỳ spaced repetition (đơn vị: ngày)
SRS_INTERVALS = [
    5 / (24 * 60),   # 5 phút
    30 / (24 * 60),  # 30 phút
    2 / 24,          # 2 giờ
    8 / 24,          # 8 giờ
    1,               # 1 ngày
    2,               # 2 ngày
    5,               # 5 ngày
    10,              # 10 ngày
    20,              # 20 ngày
    40               # 40 ngày
]

def get_next_review_date(stage, base_time=None):
    if base_time is None:
        base_time = datetime.now()
    if stage >= len(SRS_INTERVALS):
        stage = len(SRS_INTERVALS) - 1
    days = SRS_INTERVALS[stage]
    return base_time + timedelta(days=days)

def add_srs_card(content):
    global srs_data
    new_card = {
        "id": str(uuid.uuid4()),
        "content": content,
        "stage": 0,
        "next_review": get_next_review_date(0).isoformat()
    }
    srs_data.append(new_card)
    save_json(SRS_FILE, srs_data)
    return new_card

def review_srs_card(card_id, remembered):
    global srs_data
    for card in srs_data:
        if card["id"] == card_id:
            if remembered:
                card["stage"] += 1
                if card["stage"] >= len(SRS_INTERVALS):
                    card["stage"] = len(SRS_INTERVALS) - 1
            else:
                card["stage"] = 0
            card["next_review"] = get_next_review_date(card["stage"]).isoformat()
            break
    save_json(SRS_FILE, srs_data)

def get_due_srs_cards():
    now = datetime.now()
    due = []
    for card in srs_data:
        try:
            next_dt = datetime.fromisoformat(card["next_review"])
            if next_dt <= now:
                due.append(card)
        except:
            pass
    return due

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
        "🌳 Cây tri thức",
        "📞 Gọi AI",
        "📹 Video AI",
        "🔄 Lặp lại ngắt quãng",
        "♟️ Cờ vua AI"
    ]
)
st.sidebar.markdown("---")
st.sidebar.success(random.choice(["🐰 Hôm nay cùng cố gắng nhé", "🌸 Mỗi ngày tiến bộ 1%", "🐱 Bạn đang làm rất tốt"]))
st.sidebar.info(random.choice(["🐰 Nghỉ chút rồi học tiếp nhé", "🐰 Mình tin bạn làm được"]))

# Hiển thị thông báo nhắc SRS trong sidebar
due_srs = get_due_srs_cards()
if due_srs:
    st.sidebar.warning(f"🔄 Bạn có {len(due_srs)} thẻ cần ôn tập ngay!", icon="⏰")
else:
    st.sidebar.success("✅ Không có thẻ nào quá hạn. Nghỉ ngơi thôi!")

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
    if due_srs:
        st.warning(f"📚 Hôm nay bạn có {len(due_srs)} thẻ cần ôn theo phương pháp lặp lại ngắt quãng. Hãy vào mục '🔄 Lặp lại ngắt quãng' để học ngay!")

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
        # Đếm giờ không block quá nặng
        progress_bar = st.progress(0)
        for i in range(minute * 60):
            time.sleep(1)
            progress_bar.progress((i+1)/(minute*60))
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
    if xp_data["level"] >= pet["level"] * 2:
        pet["level"] += 1
        save_json(PET_FILE, pet)
        st.success("🐰 Thỏ đã lớn hơn!")

# ==============================
# CỬA HÀNG
# ==============================
elif menu == "🛍️ Cửa hàng":
    st.title("🛍️ Cửa hàng thỏ")
    shop_items = [
        {"name": "🐰 Nơ hồng", "cost": 100},
        {"name": "🌸 Vòng hoa", "cost": 150},
        {"name": "🥕 Cà rốt vàng", "cost": 200},
        {"name": "👑 Vương miện", "cost": 500}
    ]
    for item in shop_items:
        col1, col2 = st.columns([4,1])
        col1.write(item["name"])
        col2.write(f"{item['cost']} XP")
        if col2.button("Mua", key=item["name"]):
            if xp_data["xp"] >= item["cost"]:
                add_xp(-item["cost"])
                st.success(f"Đã mua {item['name']}!")
                st.rerun()
            else:
                st.warning("Không đủ XP")

# ==============================
# THỐNG KÊ
# ==============================
elif menu == "📈 Thống kê":
    st.title("📈 Thống kê học tập")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Level", xp_data["level"])
    col2.metric("XP", xp_data["xp"])
    col3.metric("Chuỗi học", streak["days"])
    col4.metric("Flashcard", len(flashcards))
    df_stats = pd.DataFrame({
        "Chỉ số": ["XP", "Level", "Streak"],
        "Giá trị": [xp_data["xp"], xp_data["level"], streak["days"]]
    })
    st.bar_chart(df_stats.set_index("Chỉ số"))

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
# LỊCH HỌC
# ==============================
elif menu == "📅 Lịch học":
    st.title("📅 Kế hoạch tuần")
    days_list = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
    # Lưu lịch học vào file
    schedule_file = os.path.join(DATA_FOLDER, "schedule.json")
    schedule = load_json(schedule_file, {})
    for d in days_list:
        new_val = st.text_input(d, value=schedule.get(d, ""))
        if new_val != schedule.get(d, ""):
            schedule[d] = new_val
            save_json(schedule_file, schedule)

# ==============================
# LỘ TRÌNH AI
# ==============================
elif menu == "🛣️ Lộ trình AI":
    st.title("🛣️ AI Lộ trình")
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
    lvl = xp_data["level"]
    if lvl < 3:
        st.markdown("# 🌱")
    elif lvl < 8:
        st.markdown("# 🌿")
    elif lvl < 15:
        st.markdown("# 🌳")
    else:
        st.markdown("# 🌲")
    st.write(f"Cấp độ cây: {lvl}")

# ==============================
# GỌI AI (Upload ghi âm + Edge TTS)
# ==============================
elif menu == "📞 Gọi AI":
    st.title("📞 Gọi AI (thử nghiệm)")
    st.info("🎤 Tải file ghi âm giọng nói của bạn (WAV, MP3, M4A). AI sẽ trả lời bằng văn bản và có thể đọc thành giọng (Edge TTS).")
    audio_file = st.file_uploader("Chọn file ghi âm", type=["wav", "mp3", "m4a"])
    if audio_file:
        with open("temp_audio.wav", "wb") as f:
            f.write(audio_file.read())
        st.audio("temp_audio.wav")
        st.warning("⚠️ Tính năng nhận dạng giọng nói chưa được tích hợp. AI sẽ trả lời dựa trên nội dung mẫu.")
        prompt_text = "Người dùng vừa gửi một file ghi âm. Hãy trả lời như một gia sư nam thân thiện, động viên học tập."
        with st.spinner("AI đang xử lý..."):
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt_text}]
            )
            reply = response.choices[0].message.content
        st.success(f"📝 AI trả lời: {reply}")
        if st.button("🔊 Đọc trả lời bằng Edge TTS"):
            with st.spinner("Đang tạo giọng nói..."):
                audio_path = run_async_tts(reply)
                if audio_path and os.path.exists(audio_path):
                    st.audio(audio_path)
                    st.success("Đã phát giọng đọc")
                else:
                    st.error("Không thể tạo giọng nói. Hãy cài thư viện edge-tts (pip install edge-tts)")

# ==============================
# VIDEO AI (Camera + mô tả ảnh)
# ==============================
elif menu == "📹 Video AI":
    st.title("📹 Video AI (chụp ảnh từ camera)")
    st.info("Bật camera, chụp ảnh, AI sẽ mô tả nội dung trong ảnh.")
    image = st.camera_input("Bật camera và chụp ảnh")
    if image:
        st.image(image, width=400, caption="Ảnh vừa chụp")
        if st.button("🧠 Phân tích ảnh với AI"):
            with st.spinner("AI đang xem ảnh..."):
                prompt = "Hãy tưởng tượng bạn nhìn thấy một bức ảnh chụp từ camera. Hãy đưa ra lời khuyên học tập tích cực, động viên người dùng."
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.success(response.choices[0].message.content)
                st.warning("Lưu ý: AI chưa thực sự nhìn thấy ảnh (chỉ mô phỏng). Để nhận diện ảnh thật, cần dùng mô hình vision như GPT-4V.")

# ==============================
# LẶP LẠI NGẮT QUÃNG (SPACED REPETITION)
# ==============================
elif menu == "🔄 Lặp lại ngắt quãng":
    st.title("🔄 Lặp lại ngắt quãng – Phương pháp khoa học")
    st.markdown("""
    **📌 Nguyên lý:** Ôn tập đúng thời điểm vàng giúp ghi nhớ sâu hơn.
    - 📈 Chu kỳ: 5 phút → 30 phút → 2 giờ → 8 giờ → 1 ngày → 2 ngày → 5 ngày → 10 ngày → 20 ngày → 40 ngày.
    - ✅ Khi nhớ → tiến đến mốc tiếp theo.
    - ❌ Khi quên → quay lại mốc 5 phút.
    """)
    
    # Thêm thẻ mới
    with st.expander("➕ Thêm nội dung cần ghi nhớ"):
        new_content = st.text_area("Nội dung (công thức, sự kiện, từ vựng, ...)")
        if st.button("📌 Lưu thẻ") and new_content:
            add_srs_card(new_content)
            st.success("Đã thêm vào hệ thống lặp lại! Bạn sẽ được nhắc đúng lúc.")
            st.rerun()
    
    # Hiển thị danh sách thẻ cần ôn ngay
    due_cards = get_due_srs_cards()
    st.subheader(f"📚 Ôn tập ngay – {len(due_cards)} thẻ cần xem lại")
    if not due_cards:
        st.info("🎉 Tuyệt vời! Hiện tại không có thẻ nào cần ôn. Hãy thêm thẻ mới để bắt đầu.")
    else:
        for card in due_cards:
            with st.container():
                st.markdown(f"**📝 Nội dung:** {card['content']}")
                st.caption(f"🔁 Giai đoạn {card['stage']+1}/{len(SRS_INTERVALS)} | Hạn ôn: {datetime.fromisoformat(card['next_review']).strftime('%H:%M %d/%m/%Y')}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Đã nhớ", key=f"remember_{card['id']}"):
                        review_srs_card(card['id'], remembered=True)
                        add_xp(3)
                        st.success("+3 XP! Tiến tới mốc tiếp theo.")
                        st.rerun()
                with col2:
                    if st.button("❌ Quên rồi", key=f"forget_{card['id']}"):
                        review_srs_card(card['id'], remembered=False)
                        st.warning("Đã reset chu kỳ. Hãy học lại sau 5 phút.")
                        st.rerun()
                st.markdown("---")
    
    # Hiển thị tất cả thẻ
    with st.expander("🗂️ Tất cả thẻ đang theo dõi"):
        for card in srs_data:
            next_time = datetime.fromisoformat(card['next_review']).strftime('%H:%M %d/%m/%Y')
            st.write(f"**{card['content']}** – Stage {card['stage']+1} – Ôn lúc: {next_time}")
    # === THỐNG KÊ SRS ===
    with st.expander("📊 Thống kê hiệu quả ôn tập"):
        total_cards = len(srs_data)
        mastered = sum(1 for c in srs_data if c["stage"] >= len(SRS_INTERVALS)-2)  # từ stage 8 trở lên
        due_count = len(get_due_srs_cards())
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Tổng số thẻ", total_cards)
        col_b.metric("Thẻ thành thạo", mastered)
        col_c.metric("Thẻ cần ôn", due_count)
        
        # Biểu đồ tiến độ
        stage_counts = [0]*len(SRS_INTERVALS)
        for c in srs_data:
            stage_counts[min(c["stage"], len(SRS_INTERVALS)-1)] += 1
        st.bar_chart(pd.DataFrame({
            "Giai đoạn": [f"{i+1}" for i in range(len(SRS_INTERVALS))],
            "Số thẻ": stage_counts
        }).set_index("Giai đoạn"))
# ==============================
# CỜ VUA AI
# ==============================
elif menu == "♟️ Cờ vua AI":
    st.title("♟️ Cờ vua với AI (Groq)")
    if not CHESS_AVAILABLE:
        st.error("Thiếu thư viện python-chess. Hãy chạy: pip install python-chess")
        st.stop()
    
    # Khởi tạo bàn cờ trong session state
    if "chess_board" not in st.session_state:
        st.session_state.chess_board = chess.Board()
        st.session_state.chess_move_history = []  # lưu các nước đi dạng UCI
        st.session_state.chess_game_over = False
        st.session_state.chess_last_move = None
    
    board = st.session_state.chess_board
    move_history = st.session_state.chess_move_history
    
    # Hiển thị bàn cờ dạng SVG
    board_svg = chess.svg.board(board=board, size=400)
    st.components.v1.html(board_svg, height=450, width=450)
    
    # Hiển thị trạng thái
    if board.is_checkmate():
        winner = "Trắng" if board.turn == chess.BLACK else "Đen"
        st.error(f"🏆 Chiếu hết! {winner} thắng.")
        st.session_state.chess_game_over = True
    elif board.is_stalemate():
        st.warning("♟️ Hết nước đi (stalemate). Hòa.")
        st.session_state.chess_game_over = True
    elif board.is_check():
        st.warning("⚠️ Vua đang bị chiếu!")
    
    if not st.session_state.chess_game_over:
        # Người chơi là quân trắng (đi trước)
        if board.turn == chess.WHITE:
            st.subheader("🏃 Nước đi của bạn")
                        # Nút gợi ý nước đi từ AI
            if st.button("💡 Gợi ý nước đi cho tôi"):
                with st.spinner("AI đang phân tích..."):
                    legal_san = [board.san(m) for m in board.legal_moves]
                    hint_prompt = f"Thế cờ hiện tại (FEN: {board.fen()}). Hãy đề xuất một nước đi tốt nhất cho quân Trắng trong các nước sau: {', '.join(legal_san)}. Chỉ trả lời duy nhất tên nước đi (dạng SAN, ví dụ: e4, Nf3)."
                    hint_res = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": hint_prompt}],
                        temperature=0.3
                    )
                    st.info(f"💡 AI gợi ý: {hint_res.choices[0].message.content.strip()}")
            # Nhập nước đi bằng UCI (ví dụ: e2e4)
            move_uci = st.text_input("Nhập nước đi (UCI, ví dụ: e2e4, g1f3):", key="uci_input")
            if st.button("Thực hiện nước đi"):
                try:
                    move = chess.Move.from_uci(move_uci)
                    if move in board.legal_moves:
                        board.push(move)
                        move_history.append(move_uci)
                        st.session_state.chess_board = board
                        st.rerun()
                    else:
                        st.error("Nước đi không hợp lệ!")
                except:
                    st.error("Định dạng UCI sai. Hãy nhập đúng.")
        else:
            # Lượt AI (quân đen)
            st.subheader("🤖 AI đang suy nghĩ...")
            with st.spinner("AI tính toán nước đi tối ưu..."):
                # Hỏi Groq chọn nước đi hay nhất
                # Lấy danh sách nước đi hợp lệ dạng text
                legal_moves = [board.san(move) for move in board.legal_moves]  # SAN dễ đọc
                board_fen = board.fen()
                prompt = f"""
Bạn là một đại kiện tướng cờ vua. Hãy phân tích thế cờ sau (FEN: {board_fen}) và chọn MỘT nước đi tốt nhất cho quân Đen. 
Các nước đi hợp lệ (dạng SAN): {', '.join(legal_moves)}.
Chỉ trả lời duy nhất một nước đi dưới dạng SAN (ví dụ: Nf6, e5, O-O). Không giải thích gì thêm.
"""
                try:
                    res = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3
                    )
                    ai_move_san = res.choices[0].message.content.strip()
                    # Chuyển SAN -> Move
                    try:
                        ai_move = board.parse_san(ai_move_san)
                        if ai_move in board.legal_moves:
                            board.push(ai_move)
                            move_history.append(board.uci(ai_move))
                            st.session_state.chess_board = board
                            st.success(f"🤖 AI đi: {ai_move_san}")
                            st.rerun()
                        else:
                            # Nếu AI trả lời sai, chọn nước đầu tiên
                            st.warning(f"AI đề xuất {ai_move_san} không hợp lệ, chọn nước ngẫu nhiên.")
                            first_move = list(board.legal_moves)[0]
                            board.push(first_move)
                            move_history.append(board.uci(first_move))
                            st.session_state.chess_board = board
                            st.rerun()
                    except:
                        # Lỗi parse, chọn nước đầu
                        first_move = list(board.legal_moves)[0]
                        board.push(first_move)
                        move_history.append(board.uci(first_move))
                        st.session_state.chess_board = board
                        st.rerun()
                except Exception as e:
                    st.error(f"Lỗi AI: {e}. AI sẽ đi nước đầu tiên.")
                    first_move = list(board.legal_moves)[0]
                    board.push(first_move)
                    move_history.append(board.uci(first_move))
                    st.session_state.chess_board = board
                    st.rerun()
    
    # Nút phân tích ván đấu (hiển thị sau khi kết thúc)
    if st.session_state.chess_game_over or st.button("📊 Phân tích ván đấu (sau khi kết thúc)"):
        if len(move_history) > 0:
            with st.spinner("AI đang phân tích toàn bộ ván cờ..."):
                # Tạo ghi chép các nước đi dạng PGN đơn giản
                game_moves = " ".join(move_history)
                analysis_prompt = f"""
Bạn là một huấn luyện viên cờ vua. Hãy phân tích ván đấu sau (các nước đi theo thứ tự): {game_moves}
Hãy đánh giá từng giai đoạn: khai cuộc, trung cuộc, tàn cuộc.
Chỉ ra điểm mạnh, điểm yếu của người chơi (quân trắng), và đề xuất cách cải thiện.
Kết luận: Người chơi nên luyện tập khía cạnh nào?
Trả lời bằng tiếng Việt, dễ hiểu, chi tiết.
"""
                analysis_res = client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=[{"role": "user", "content": analysis_prompt}]
                )
                st.markdown("### 🧠 Phân tích từ AI")
                st.write(analysis_res.choices[0].message.content)
                # Thưởng XP khi phân tích
                add_xp(20)
                st.success("+20 XP vì đã học hỏi từ ván cờ!")
        else:
            st.info("Chưa có nước đi nào để phân tích.")
    
    # Nút khởi động lại ván mới
    if st.button("🔄 Chơi ván mới"):
        st.session_state.chess_board = chess.Board()
        st.session_state.chess_move_history = []
        st.session_state.chess_game_over = False
        st.rerun()

# ==============================
# KẾT THÚC
# ==============================
