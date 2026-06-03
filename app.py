# ==============================
# STUDY GARDEN AI - HOÀN CHỈNH (PHẦN 1)
# Tích hợp: AI Groq, Ghi âm, TTS, Camera, Cờ vua, Spaced Repetition
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
import math

# === THƯ VIỆN AI ===
from groq import Groq

# === THƯ VIỆN TTS (nếu có) ===
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

# === CÁC THƯ VIỆN KHÁC ===
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

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
    import chess.pgn
    CHESS_AVAILABLE = True
except ImportError:
    CHESS_AVAILABLE = False

try:
    from stockfish import Stockfish
    STOCKFISH_IMPORT = True
except ImportError:
    STOCKFISH_IMPORT = False

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
.notification-badge {
    background-color: #ff6b6b;
    color: white;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 14px;
    display: inline-block;
    margin-left: 10px;
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
# KHỞI TẠO GROQ CLIENT (API key của em)
# ==============================
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

# ==============================
# CÁC FILE DỮ LIỆU HIỆN CÓ
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
check_badges()

# ==============================
# TEXT TO SPEECH & EDGE TTS (giữ nguyên)
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
# HÀM TRÍCH XUẤT TÀI LIỆU (giữ nguyên)
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
# MODULE SPACED REPETITION (LẶP LẠI NGẮT QUÃNG)
# ==============================
# File lưu trữ các thẻ ôn tập
SPACED_FILE = os.path.join(DATA_FOLDER, "spaced_repetition.json")

# Các mốc thời gian theo khoa học (phút, giờ, ngày)
# Dựa trên thuật toán SM-2, sau mỗi lần học đúng, khoảng cách tăng dần.
# Ở đây đơn giản hóa: lần 1: 5 phút, lần 2: 30 phút, lần 3: 12 giờ, lần 4: 1 ngày, lần 5: 2 ngày, lần 6: 4 ngày, lần 7: 7 ngày, lần 8: 14 ngày
INTERVALS = [5, 30, 12*60, 24*60, 48*60, 96*60, 168*60, 336*60]  # đơn vị phút

def init_spaced_data():
    if not os.path.exists(SPACED_FILE):
        save_json(SPACED_FILE, [])

def add_spaced_card(content, tags=""):
    """Thêm một thẻ học mới vào hệ thống lặp lại ngắt quãng"""
    init_spaced_data()
    data = load_json(SPACED_FILE, [])
    now = datetime.now()
    card = {
        "id": len(data) + 1,
        "content": content,
        "tags": tags,
        "created_at": now.isoformat(),
        "last_review": None,
        "next_review": now.isoformat(),  # có thể học ngay
        "interval_index": 0,  # lần học tiếp theo sẽ dùng INTERVALS[0]
        "easiness": 2.5,      # độ dễ (theo SM-2)
        "repetitions": 0
    }
    data.append(card)
    save_json(SPACED_FILE, data)
    return card

def get_due_cards():
    """Trả về danh sách các thẻ cần ôn tập ngay bây giờ"""
    init_spaced_data()
    data = load_json(SPACED_FILE, [])
    now = datetime.now()
    due = []
    for card in data:
        if card["next_review"]:
            next_time = datetime.fromisoformat(card["next_review"])
            if now >= next_time:
                due.append(card)
    return due

def update_card_review(card_id, success):
    """Cập nhật sau khi học: success = True nếu nhớ, False nếu quên"""
    data = load_json(SPACED_FILE, [])
    card = next((c for c in data if c["id"] == card_id), None)
    if not card:
        return
    now = datetime.now()
    if success:
        # Tăng số lần lặp lại
        card["repetitions"] += 1
        # Cập nhật độ dễ (theo công thức SM-2 đơn giản)
        # Ở đây chỉ tăng interval index nếu repetitions chưa vượt quá số mốc
        if card["repetitions"] <= len(INTERVALS):
            interval_minutes = INTERVALS[card["repetitions"] - 1]
        else:
            interval_minutes = INTERVALS[-1] * 2  # tiếp tục nhân đôi
        card["next_review"] = (now + timedelta(minutes=interval_minutes)).isoformat()
        card["last_review"] = now.isoformat()
    else:
        # Nếu quên, reset repetitions về 0 và lịch trình về mốc đầu tiên (5 phút)
        card["repetitions"] = 0
        card["next_review"] = (now + timedelta(minutes=INTERVALS[0])).isoformat()
        card["last_review"] = now.isoformat()
    save_json(SPACED_FILE, data)

def get_next_review_time(card):
    if card["next_review"]:
        return datetime.fromisoformat(card["next_review"])
    return None

def format_interval(minutes):
    if minutes < 60:
        return f"{int(minutes)} phút"
    elif minutes < 1440:
        hours = minutes / 60
        return f"{int(hours)} giờ" if hours == int(hours) else f"{hours:.1f} giờ"
    else:
        days = minutes / 1440
        return f"{int(days)} ngày" if days == int(days) else f"{days:.1f} ngày"

# ============================================
# SPACED REPETITION MODULE
# Học thông minh với lịch nhắc khoa học
# Dành cho Study Garden AI
# ============================================

import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

# === CẤU HÌNH TRANG ===
st.set_page_config(page_title="Spaced Repetition - Học thông minh", page_icon="⏰", layout="wide")

st.markdown("""
<style>
    .sr-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border-left: 5px solid #4CAF50;
    }
    .due-today {
        border-left-color: #FF9800;
        background: #FFF8E1;
    }
    .overdue {
        border-left-color: #F44336;
        background: #FFEBEE;
    }
    .topic-title {
        font-size: 1.2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# === THƯ MỤC LƯU TRỮ ===
DATA_DIR = "sr_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# === HÀM ĐỌC/GHI ===
def load_topics():
    path = os.path.join(DATA_DIR, "topics.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_topics(topics):
    path = os.path.join(DATA_DIR, "topics.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)

def load_schedule():
    path = os.path.join(DATA_DIR, "schedule.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_schedule(schedule):
    path = os.path.join(DATA_DIR, "schedule.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

# === CÁC MỐC THỜI GIAN THEO KHOA HỌC ===
# Dựa trên hệ thống Leitner và nghiên cứu về spaced repetition
# Các interval (phút) sau mỗi lần học thành công
INTERVALS = [5, 30, 120, 480, 1440, 4320, 10080, 43200]  # 5 phút, 30p, 2h, 8h, 1 ngày, 3 ngày, 1 tuần, 30 ngày
INTERVAL_NAMES = ["Lần 1 (5p)", "Lần 2 (30p)", "Lần 3 (2h)", "Lần 4 (8h)", "Lần 5 (1 ngày)", "Lần 6 (3 ngày)", "Lần 7 (1 tuần)", "Lần 8 (30 ngày)"]

def get_next_review_time(last_review, stage):
    """stage: số lần đã học thành công (0-index)"""
    if stage >= len(INTERVALS):
        stage = len(INTERVALS) - 1
    interval_minutes = INTERVALS[stage]
    return last_review + timedelta(minutes=interval_minutes)

def get_overdue_status(last_review, stage):
    """Trả về trạng thái: 'due', 'overdue', 'future'"""
    next_review = get_next_review_time(last_review, stage)
    now = datetime.now()
    if now >= next_review:
        return "due" if now - next_review < timedelta(hours=1) else "overdue"
    return "future"

# === LOGIN ĐƠN GIẢN (để mỗi người dùng riêng) ===
if "sr_user" not in st.session_state:
    st.session_state.sr_user = None

if not st.session_state.sr_user:
    st.title("⏰ Spaced Repetition - Học thông minh")
    st.write("Nhập tên của bạn để bắt đầu (dữ liệu được lưu riêng)")
    user = st.text_input("Tên của bạn")
    if st.button("Bắt đầu"):
        if user:
            st.session_state.sr_user = user
            st.rerun()
    st.stop()

user = st.session_state.sr_user

# === DỮ LIỆU CỦA USER ===
topics = load_topics().get(user, {})
schedule = load_schedule().get(user, {})

# === HÀM LƯU CHO USER ===
def save_user_data():
    all_topics = load_topics()
    all_topics[user] = topics
    save_topics(all_topics)
    all_schedule = load_schedule()
    all_schedule[user] = schedule
    save_schedule(all_schedule)

# === GIAO DIỆN CHÍNH ===
st.sidebar.title(f"👤 {user}")
menu = st.sidebar.radio("Menu", ["📚 Thêm nội dung mới", "📖 Ôn tập hôm nay", "📊 Thống kê", "⚙️ Quản lý"])

# --- 1. THÊM NỘI DUNG MỚI ---
if menu == "📚 Thêm nội dung mới":
    st.title("📚 Thêm chủ đề / nội dung cần ghi nhớ")
    with st.form("new_topic"):
        topic_name = st.text_input("Tên chủ đề (ví dụ: Toán - 1+1=2, Tiếng Anh - từ vựng, Lịch sử - mốc thời gian)")
        content = st.text_area("Nội dung chi tiết (công thức, câu hỏi, ghi chú,...)", height=150)
        submitted = st.form_submit_button("➕ Thêm vào lịch học")
    
    if submitted and topic_name and content:
        if topic_name in topics:
            st.warning("Chủ đề đã tồn tại. Bạn có thể xóa cũ hoặc đổi tên.")
        else:
            now = datetime.now()
            topics[topic_name] = {
                "content": content,
                "stage": 0,  # số lần đã học thành công
                "last_review": now.isoformat(),
                "created": now.isoformat()
            }
            # Ghi vào schedule để biết ngày nào cần ôn
            next_review = get_next_review_time(now, 0)
            date_key = next_review.strftime("%Y-%m-%d")
            if date_key not in schedule:
                schedule[date_key] = []
            schedule[date_key].append(topic_name)
            save_user_data()
            st.success(f"✅ Đã thêm chủ đề '{topic_name}'. Lần ôn đầu tiên sau 5 phút!")

# --- 2. ÔN TẬP HÔM NAY ---
elif menu == "📖 Ôn tập hôm nay":
    st.title("📖 Ôn tập hôm nay")
    today = datetime.now().strftime("%Y-%m-%d")
    due_topics = schedule.get(today, [])
    
    # Nếu không có topic nào theo lịch, hiển thị tất cả topic đang trong trạng thái due/overdue
    if not due_topics:
        # Duyệt qua tất cả topics để tìm topic cần ôn
        due_topics = []
        for name, data in topics.items():
            last_review = datetime.fromisoformat(data["last_review"])
            stage = data["stage"]
            next_review = get_next_review_time(last_review, stage)
            if datetime.now() >= next_review:
                due_topics.append(name)
        due_topics = list(set(due_topics))  # loại trùng
    
    if not due_topics:
        st.info("🎉 Hôm nay không có nội dung nào cần ôn tập. Hãy nghỉ ngơi hoặc thêm chủ đề mới.")
    else:
        st.write(f"Hôm nay cần ôn **{len(due_topics)}** chủ đề:")
        for topic_name in due_topics:
            data = topics.get(topic_name)
            if not data:
                continue
            last_review = datetime.fromisoformat(data["last_review"])
            stage = data["stage"]
            next_review = get_next_review_time(last_review, stage)
            status = get_overdue_status(last_review, stage)
            
            # Hiển thị card
            if status == "overdue":
                st.markdown(f"<div class='sr-card overdue'>", unsafe_allow_html=True)
                st.markdown(f"<span class='topic-title'>⚠️ QUÁ HẠN: {topic_name}</span>", unsafe_allow_html=True)
            elif status == "due":
                st.markdown(f"<div class='sr-card due-today'>", unsafe_allow_html=True)
                st.markdown(f"<span class='topic-title'>🔔 ĐẾN LÚC ÔN: {topic_name}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='sr-card'>", unsafe_allow_html=True)
                st.markdown(f"<span class='topic-title'>📌 {topic_name}</span>", unsafe_allow_html=True)
            
            st.write(f"**Nội dung:** {data['content']}")
            st.write(f"Lần ôn thứ: {stage+1}/{len(INTERVALS)} (Kế tiếp sau: {INTERVAL_NAMES[stage] if stage < len(INTERVALS) else 'Hoàn thành'})")
            st.write(f"Lần học cuối: {last_review.strftime('%H:%M %d/%m/%Y')}")
            st.write(f"Lịch ôn tiếp theo: {next_review.strftime('%H:%M %d/%m/%Y')}")
            
            # Nút "Đã học xong"
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("✅ Đã học xong", key=f"done_{topic_name}"):
                    # Cập nhật stage, last_review, schedule
                    new_stage = min(stage + 1, len(INTERVALS) - 1)
                    topics[topic_name]["stage"] = new_stage
                    topics[topic_name]["last_review"] = datetime.now().isoformat()
                    # Xóa khỏi schedule cũ (ngày hôm nay) – thực tế không cần, nhưng sẽ xóa khi refresh
                    # Tính lịch tiếp theo
                    if new_stage < len(INTERVALS):
                        next_review_new = get_next_review_time(datetime.now(), new_stage)
                        next_date = next_review_new.strftime("%Y-%m-%d")
                        if next_date not in schedule:
                            schedule[next_date] = []
                        if topic_name not in schedule[next_date]:
                            schedule[next_date].append(topic_name)
                    # Xóa topic khỏi schedule của hôm nay (nếu có)
                    today_schedule = schedule.get(today, [])
                    if topic_name in today_schedule:
                        today_schedule.remove(topic_name)
                        schedule[today] = today_schedule
                    save_user_data()
                    st.success(f"✅ Đã ghi nhận! Lần ôn tiếp theo sau {INTERVAL_NAMES[new_stage] if new_stage < len(INTERVALS) else 'đã hoàn thành'}")
                    st.rerun()
            with col2:
                if st.button("❌ Tạm bỏ qua", key=f"skip_{topic_name}"):
                    # Không làm gì, chỉ bỏ qua lần này (không thay đổi stage)
                    st.info("Đã bỏ qua, sẽ nhắc lại trong lần sau.")
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")

# --- 3. THỐNG KÊ (sẽ ở phần 2) ---
elif menu == "📊 Thống kê":
    st.title("📊 Thống kê quá trình học")
    if not topics:
        st.info("Chưa có dữ liệu")
    else:
        # Tính số lần đã học
        stages = [data["stage"] for data in topics.values()]
        df = pd.DataFrame({"Chủ đề": list(topics.keys()), "Số lần ôn": stages})
        st.dataframe(df)
        fig = px.bar(df, x="Chủ đề", y="Số lần ôn", title="Tiến độ ôn tập")
        st.plotly_chart(fig, use_container_width=True)
        
        # Dự đoán lịch ôn sắp tới
        upcoming = []
        for name, data in topics.items():
            last = datetime.fromisoformat(data["last_review"])
            stage = data["stage"]
            if stage < len(INTERVALS):
                next_time = get_next_review_time(last, stage)
                upcoming.append({"Chủ đề": name, "Lần ôn tiếp theo": next_time.strftime("%d/%m/%Y %H:%M"), "Giai đoạn": stage+1})
        if upcoming:
            st.subheader("🗓️ Lịch ôn sắp tới")
            st.dataframe(pd.DataFrame(upcoming))

# --- 4. QUẢN LÝ (xóa, sửa) ---
elif menu == "⚙️ Quản lý":
    st.title("⚙️ Quản lý chủ đề")
    if not topics:
        st.info("Chưa có chủ đề nào.")
    else:
        for name in list(topics.keys()):
            col1, col2, col3 = st.columns([4,1,1])
            col1.write(name)
            if col2.button("✏️ Sửa", key=f"edit_{name}"):
                # Hiện form sửa (đơn giản: dùng session)
                st.session_state.edit_topic = name
            if col3.button("🗑️ Xóa", key=f"del_{name}"):
                # Xóa khỏi topics và schedule
                del topics[name]
                # Xóa trong schedule
                for date in schedule:
                    if name in schedule[date]:
                        schedule[date].remove(name)
                save_user_data()
                st.success(f"Đã xóa '{name}'")
                st.rerun()
        
        if "edit_topic" in st.session_state:
            name = st.session_state.edit_topic
            data = topics[name]
            with st.form("edit_form"):
                new_content = st.text_area("Nội dung mới", value=data["content"])
                if st.form_submit_button("Cập nhật"):
                    topics[name]["content"] = new_content
                    save_user_data()
                    del st.session_state.edit_topic
                    st.success("Đã cập nhật")
                    st.rerun()

# === CHẠY ỨNG DỤNG ===
if __name__ == "__main__":
    # Không cần thêm
    pass
