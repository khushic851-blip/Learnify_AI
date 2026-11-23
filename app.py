import streamlit as st
import requests
import json
import re
import html
import sqlite3
import hashlib
import secrets
from datetime import datetime

# =========================================================
# LEARNIFY AI
# Login + History + Local AI + Notes + Visuals + Quiz
# =========================================================

st.set_page_config(
    page_title="Learnify AI",
    page_icon="📚",
    layout="wide"
)

DB_FILE = "learnify.db"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"


# =========================================================
# STYLE
# =========================================================

st.markdown("""
<style>
:root {
    --lf-ink: #18233f;
    --lf-muted: #68748b;
    --lf-primary: #5b5ce2;
    --lf-primary-dark: #4546c8;
    --lf-border: #e4e8f2;
    --lf-surface: #ffffff;
    --lf-bg: #f5f7fc;
}
.stApp {
    background:
        radial-gradient(ellipse at 8% 0%, rgba(91,92,226,.09), transparent 34%),
        radial-gradient(ellipse at 95% 12%, rgba(31,183,166,.07), transparent 28%),
        var(--lf-bg);
    color: var(--lf-ink);
}
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.stAppViewContainer .main .block-container {
    max-width: 1240px;
    padding: 2rem 2.2rem 4rem;
}
.learnify-title {
    color: var(--lf-ink);
    font-size: clamp(2.1rem, 4vw, 3rem);
    line-height: 1.12;
    font-weight: 800;
    letter-spacing: -1.5px;
}
.subtitle {
    color: var(--lf-muted);
    font-size: 1.05rem;
    margin: .55rem 0 1.6rem;
}
.hero {
    position: relative;
    overflow: hidden;
    padding: 2.1rem 2.25rem;
    border-radius: 26px;
    background: linear-gradient(125deg, #fff 0%, #f0f2ff 58%, #edf8f8 100%);
    border: 1px solid #e1e6f5;
    box-shadow: 0 14px 40px rgba(37, 50, 92, .06);
    margin: 1.25rem 0 1.6rem;
}
.hero h2 { color: var(--lf-ink); font-size: 1.8rem; letter-spacing: -.6px; }
.hero p { color: #53617a; font-size: 1rem; line-height: 1.75; max-width: 850px; }
.card, .history-item, .quiz-question {
    padding: 1.25rem 1.4rem;
    border-radius: 18px;
    background: var(--lf-surface);
    border: 1px solid var(--lf-border);
    box-shadow: 0 5px 18px rgba(30, 45, 85, .035);
    margin: .8rem 0;
}
.card h3 { color: var(--lf-ink); margin-bottom: .55rem; }
.card p, .card small { color: #59667d; line-height: 1.7; }
.word {
    padding: .9rem 1rem;
    background: #f4f5ff;
    border: 1px solid #e7e8ff;
    border-radius: 13px;
    margin: .55rem 0;
    color: #34405a;
}
.diagram-box {
    padding: 1rem 1.2rem;
    border-radius: 15px;
    background: #fff;
    border: 1px solid #dfe5f5;
    text-align: center;
    font-weight: 650;
    color: var(--lf-ink);
    box-shadow: 0 4px 14px rgba(30,45,85,.04);
    margin: .35rem 0;
}
.arrow { text-align: center; color: var(--lf-primary); font-size: 1.4rem; font-weight: 800; margin: .25rem 0; }
.badge, .ai-badge {
    display: inline-flex;
    align-items: center;
    padding: .45rem .85rem;
    border-radius: 999px;
    font-size: .78rem;
    font-weight: 750;
    letter-spacing: .04em;
}
.badge { background: #eeefff; color: #4d4fd1; }
.ai-badge { background: #e8f8f1; color: #137b58; margin: .5rem 0 1rem; }
.quiz-question { background: #fdfdff; border-left: 4px solid var(--lf-primary); }
.auth-box { max-width: 620px; margin: 3.5rem auto; padding: 2.1rem; border-radius: 24px; background: rgba(255,255,255,.88); border: 1px solid var(--lf-border); box-shadow: 0 18px 55px rgba(33,47,88,.08); }
div[data-testid="stMetric"] {
    background: rgba(255,255,255,.9);
    border: 1px solid var(--lf-border);
    padding: 1rem 1.15rem;
    border-radius: 17px;
    box-shadow: 0 5px 16px rgba(30,45,85,.035);
}
div[data-testid="stMetricLabel"] { color: var(--lf-muted); }
div[data-testid="stMetricValue"] { color: var(--lf-ink); font-weight: 750; }
.stButton > button, .stFormSubmitButton > button {
    border: 1px solid #dfe3ef;
    border-radius: 12px;
    min-height: 2.8rem;
    font-weight: 600;
    color: #283653;
    background: #fff;
    transition: all .18s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    border-color: #a9abf0;
    color: var(--lf-primary-dark);
    background: #f8f8ff;
    transform: translateY(-1px);
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    color: #fff;
    background: linear-gradient(135deg, #6264e8, #4e50ce);
    border: 0;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
    color: #fff;
    background: linear-gradient(135deg, #5557d9, #4143bb);
}
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    border-radius: 11px;
    border-color: #dfe4ef;
    background: #fbfcff;
}
.stTabs [data-baseweb="tab-list"] { gap: .45rem; border-bottom: 1px solid var(--lf-border); }
.stTabs [data-baseweb="tab"] { border-radius: 10px 10px 0 0; padding: .65rem 1rem; }
hr { border-color: var(--lf-border); }
div[data-testid="stAlert"] { border-radius: 13px; }
@media (max-width: 700px) {
    .stAppViewContainer .main .block-container { padding: 1.1rem 1rem 3rem; }
    .hero { padding: 1.4rem; border-radius: 19px; }
    .auth-box { margin: 1.2rem auto; padding: 1.25rem; }
}

.top-brand { display:flex; align-items:center; gap:.45rem; font-size:1.45rem; font-weight:850; letter-spacing:-.7px; color:var(--lf-ink); padding:.2rem 0 .7rem; }
.brand-ai { color:var(--lf-primary); }
.user-chip { display:inline-flex; align-items:center; justify-content:center; background:#fff; border:1px solid var(--lf-border); border-radius:999px; padding:.55rem .9rem; color:#526079; font-size:.9rem; margin-top:.1rem; }
.top-divider { height:1px; background:var(--lf-border); margin:.2rem 0 1.4rem; }
.dashboard-welcome { margin:.5rem 0 1rem; }
.eyebrow { color:var(--lf-primary); font-size:.73rem; font-weight:800; letter-spacing:.12em; margin-bottom:.55rem; }
.dashboard-welcome .subtitle { margin:.55rem 0 0; }
.dashboard-hero { display:flex; align-items:center; justify-content:space-between; min-height:210px; }
.dashboard-hero h2 { font-size:clamp(1.65rem,3vw,2.25rem); margin:.9rem 0 .45rem; }
.dashboard-hero p { max-width:700px; }
.hero-mark { color:rgba(91,92,226,.17); font-size:9rem; line-height:1; font-weight:900; padding:0 1rem; }
.section-heading { color:var(--lf-ink); font-size:1.15rem; font-weight:800; margin:1.55rem 0 .85rem; }
.stat-card, .panel-card, .empty-state { background:#fff; border:1px solid var(--lf-border); border-radius:18px; padding:1.1rem 1.2rem; box-shadow:0 6px 20px rgba(30,45,85,.035); min-height:140px; }
.stat-icon { font-size:1.3rem; margin-bottom:.55rem; }
.stat-value { color:var(--lf-ink); font-size:2rem; font-weight:850; line-height:1.1; }
.stat-label { color:#34415d; font-weight:750; margin-top:.25rem; }
.stat-hint, .muted-copy { color:var(--lf-muted); font-size:.83rem; margin-top:.3rem; line-height:1.55; }
.panel-title { font-weight:800; color:var(--lf-ink); margin-bottom:.65rem; }
.progress-number { color:var(--lf-primary); font-size:1.8rem; font-weight:850; margin:.2rem 0 .7rem; }
.progress-number span { color:var(--lf-muted); font-size:.82rem; font-weight:500; }
.progress-track { width:100%; height:10px; border-radius:99px; background:#edf0f8; overflow:hidden; }
.progress-fill { height:100%; border-radius:99px; background:linear-gradient(90deg,#6264e8,#35b7a4); }
.action-panel { min-height:140px; }
.action-panel .stButton { margin-top:.5rem; }
.chapter-card { display:flex; align-items:center; gap:.9rem; background:#fff; border:1px solid var(--lf-border); border-radius:15px; padding:1rem; margin:.65rem 0 .35rem; }
.chapter-icon { display:flex; align-items:center; justify-content:center; width:44px; height:44px; border-radius:13px; background:#f0f1ff; font-size:1.35rem; flex-shrink:0; }
.chapter-info { min-width:0; }
.chapter-info b { display:block; color:var(--lf-ink); overflow-wrap:anywhere; }
.chapter-info span { display:block; color:var(--lf-muted); font-size:.8rem; margin-top:.25rem; }
.empty-state { text-align:center; padding:2rem 1.2rem; min-height:170px; }
.empty-icon { font-size:2rem; margin-bottom:.5rem; }
.empty-state b { color:var(--lf-ink); }
.empty-state p { color:var(--lf-muted); font-size:.88rem; margin:.4rem 0 0; }
.activity-item { display:flex; gap:.8rem; padding:.9rem .2rem; border-bottom:1px solid #edf0f6; }
.activity-dot { width:9px; height:9px; background:#6869e8; border-radius:50%; margin:.4rem .1rem 0 .2rem; flex-shrink:0; box-shadow:0 0 0 4px #f0f0ff; }
.activity-item b { color:var(--lf-ink); font-size:.9rem; }
.activity-topic { color:#526079; font-size:.85rem; margin-top:.15rem; }
.activity-meta { color:#8993a7; font-size:.74rem; margin-top:.2rem; }
@media (max-width: 700px) { .hero-mark { display:none; } .dashboard-hero { min-height:0; } .stat-card { min-height:125px; } }


/* Premium lavender workspace + persistent navigation */
:root {
    --lf-ink: #292642;
    --lf-muted: #77738f;
    --lf-primary: #7666d8;
    --lf-primary-dark: #6252c4;
    --lf-border: #e9e6f3;
    --lf-surface: #ffffff;
    --lf-bg: #f8f7fc;
}
.stApp {
    background: #f8f7fc;
    color: var(--lf-ink);
}
section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #ece9f5;
}
section[data-testid="stSidebar"] > div {
    padding: 1.25rem .9rem 1rem;
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
}
.sidebar-brand {
    display:flex; align-items:center; gap:.65rem;
    color:#302b49; font-size:1.35rem; font-weight:850;
    letter-spacing:-.7px; padding:.35rem .35rem .15rem;
}
.sidebar-brand em { color:#7666d8; font-style:normal; }
.sidebar-logo {
    display:inline-flex; align-items:center; justify-content:center;
    width:38px; height:38px; border-radius:12px;
    color:#fff; background:linear-gradient(145deg,#a99af2,#7565d8);
    font-size:1.25rem;
}
.sidebar-caption {
    color:#9893aa; font-size:.62rem; font-weight:800;
    letter-spacing:.12em; padding:.3rem .4rem 1.6rem;
}
.sidebar-section-label {
    color:#9994aa; font-size:.66rem; font-weight:800;
    letter-spacing:.11em; padding:.45rem .45rem .5rem;
}
.sidebar-library-label { padding-top:1.55rem; }
.sidebar-empty {
    color:#9691a6; font-size:.8rem; line-height:1.5;
    padding:.35rem .5rem;
}
.sidebar-user {
    display:flex; align-items:center; gap:.7rem;
    border:1px solid #eeeaf7; background:#faf9fd;
    border-radius:14px; padding:.7rem; margin:.8rem 0 .55rem;
}
.sidebar-avatar {
    width:34px; height:34px; display:flex; align-items:center;
    justify-content:center; border-radius:11px;
    background:#efecfb; color:#7666d8; font-size:1.1rem;
}
.sidebar-user b { display:block; color:#39344f; font-size:.83rem; }
.sidebar-user small { display:block; color:#938da4; font-size:.7rem; margin-top:.1rem; }
.sidebar-spacer { height:1.4rem; }
section[data-testid="stSidebar"] .stButton > button {
    text-align:left; justify-content:flex-start;
    min-height:2.55rem; border-radius:10px;
    border-color:transparent; background:transparent;
    color:#615d75; font-weight:600; padding-left:.85rem;
    box-shadow:none;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background:#f4f1fc; color:#6252c4; border-color:#eeeafb;
    transform:none;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background:#f0edfb; color:#6252c4;
    border:1px solid #e7e1fa; box-shadow:none;
}
.app-topline {
    display:flex; align-items:center; justify-content:space-between;
    border-bottom:1px solid #ece9f4; padding:.1rem 0 1rem; margin-bottom:1.5rem;
}
.app-topline .top-brand { padding:0; font-size:1.12rem; }
.topline-note { color:#9994aa; font-size:.82rem; }
.learnify-title { color:#302b49; letter-spacing:-1.1px; }
.subtitle, .muted-copy, .stat-hint { color:#817c96; }
.hero {
    background:linear-gradient(120deg,#fff 0%,#f1effc 100%);
    border:1px solid #e9e4f7; box-shadow:none;
}
.hero h2 { color:#302b49; }
.badge { background:#f0edfb; color:#6858c9; }
.ai-badge { background:#f0edfb; color:#6858c9; }
.stat-card, .panel-card, .empty-state, .card, .history-item, .quiz-question {
    border-color:#ebe8f3; box-shadow:0 3px 14px rgba(55,43,95,.025);
}
.stat-card { border-radius:15px; }
.progress-fill { background:#8878e4; }
.activity-dot { background:#8878e4; box-shadow:0 0 0 4px #f0edfb; }
.word { background:#f7f5fd; border-color:#ebe7f7; }
.diagram-box { border-color:#e9e5f4; box-shadow:none; }
.quiz-question { border-left-color:#8878e4; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    background:#7666d8; border:1px solid #7666d8;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
    background:#6656c8; border-color:#6656c8;
}
@media (max-width: 700px) {
    .topline-note { display:none; }
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "logged_in": False,
    "user_id": None,
    "username": None,
    "page": "auth",
    "chapters": [],
    "current_chapter": None,
    "current_topic": None,
    "topic_section": "basic"
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            material_json TEXT,
            quiz_answers_json TEXT,
            quiz_submitted INTEGER DEFAULT 0,
            quiz_score INTEGER DEFAULT 0,
            quiz_total INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(chapter_id) REFERENCES chapters(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic_id INTEGER,
            action TEXT NOT NULL,
            score INTEGER,
            total INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================================================
# PASSWORD SECURITY
# =========================================================

def hash_password(password):
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password, stored):
    try:
        salt, saved_hash = stored.split("$", 1)

        current_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            120000
        ).hex()

        return secrets.compare_digest(
            current_hash,
            saved_hash
        )
    except Exception:
        return False


# =========================================================
# AUTHENTICATION
# =========================================================

def create_user(username, password):
    username = username.strip()

    if len(username) < 3:
        return False, "Username must be at least 3 characters."

    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    conn = get_db()

    try:
        conn.execute(
            """
            INSERT INTO users
            (username, password_hash, created_at)
            VALUES (?, ?, ?)
            """,
            (
                username,
                hash_password(password),
                datetime.now().isoformat(timespec="seconds")
            )
        )

        conn.commit()
        return True, "Account created successfully."

    except sqlite3.IntegrityError:
        return False, "That username already exists."

    finally:
        conn.close()


def login_user(username, password):
    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username.strip(),)
    ).fetchone()

    conn.close()

    if user and verify_password(
        password,
        user["password_hash"]
    ):
        return dict(user)

    return None


def logout():
    for key in [
        "logged_in",
        "user_id",
        "username",
        "chapters",
        "current_chapter",
        "current_topic"
    ]:
        if key == "logged_in":
            st.session_state[key] = False
        elif key in ["chapters"]:
            st.session_state[key] = []
        else:
            st.session_state[key] = None

    st.session_state.page = "auth"
    st.rerun()


# =========================================================
# LOAD USER DATA
# =========================================================

def load_user_data():
    user_id = st.session_state.user_id

    conn = get_db()

    chapter_rows = conn.execute(
        """
        SELECT *
        FROM chapters
        WHERE user_id = ?
        ORDER BY id
        """,
        (user_id,)
    ).fetchall()

    chapters = []

    for chapter_row in chapter_rows:

        topic_rows = conn.execute(
            """
            SELECT *
            FROM topics
            WHERE chapter_id = ?
            ORDER BY id
            """,
            (chapter_row["id"],)
        ).fetchall()

        topics = []

        for row in topic_rows:

            material = None

            if row["material_json"]:
                try:
                    material = json.loads(
                        row["material_json"]
                    )
                except Exception:
                    material = None

            quiz_answers = {}

            if row["quiz_answers_json"]:
                try:
                    quiz_answers = json.loads(
                        row["quiz_answers_json"]
                    )
                except Exception:
                    quiz_answers = {}

            topics.append({
                "id": row["id"],
                "name": row["name"],
                "material": material,
                "quiz_answers": quiz_answers,
                "quiz_submitted": bool(row["quiz_submitted"]),
                "quiz_score": row["quiz_score"],
                "quiz_total": row["quiz_total"],
                "generated_quiz": (
                    material.get("active_quiz")
                    if isinstance(material, dict)
                    else None
                ),
                "quiz_settings": (
                    material.get(
                        "quiz_settings",
                        {"count": 5, "difficulty": "Easy"}
                    )
                    if isinstance(material, dict)
                    else {"count": 5, "difficulty": "Easy"}
                )
            })

        chapters.append({
            "id": chapter_row["id"],
            "name": chapter_row["name"],
            "subject": chapter_row["subject"],
            "topics": topics
        })

    conn.close()

    st.session_state.chapters = chapters


# =========================================================
# DATABASE HELPERS
# =========================================================

def save_material(topic):
    conn = get_db()

    material = topic.get("material") or {}

    if topic.get("quiz_settings") is not None:
        material["quiz_settings"] = topic["quiz_settings"]

    if topic.get("generated_quiz") is not None:
        material["active_quiz"] = topic["generated_quiz"]

    conn.execute(
        """
        UPDATE topics
        SET material_json = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            json.dumps(material),
            datetime.now().isoformat(timespec="seconds"),
            topic["id"]
        )
    )

    conn.commit()
    conn.close()


def save_quiz_state(topic):
    conn = get_db()

    conn.execute(
        """
        UPDATE topics
        SET quiz_answers_json = ?,
            quiz_submitted = ?,
            quiz_score = ?,
            quiz_total = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            json.dumps(topic.get("quiz_answers", {})),
            1 if topic.get("quiz_submitted") else 0,
            topic.get("quiz_score", 0),
            topic.get("quiz_total", 0),
            datetime.now().isoformat(timespec="seconds"),
            topic["id"]
        )
    )

    conn.commit()
    conn.close()


def add_history(action, topic_id=None, score=None, total=None):
    conn = get_db()

    conn.execute(
        """
        INSERT INTO history
        (user_id, topic_id, action, score, total, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            st.session_state.user_id,
            topic_id,
            action,
            score,
            total,
            datetime.now().isoformat(timespec="seconds")
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# LOCAL AI
# =========================================================

def ask_ollama(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.3
            }
        },
        timeout=240
    )

    if response.status_code != 200:
        raise Exception(response.text)

    raw = response.json().get("response", "")

    try:
        return json.loads(raw)

    except json.JSONDecodeError:

        match = re.search(
            r"\{.*\}",
            raw,
            re.DOTALL
        )

        if match:
            return json.loads(
                match.group(0)
            )

        raise Exception(
            "The local AI returned an invalid response. Please try again."
        )


def generate_material(topic, subject):
    prompt = f"""
You are Learnify AI, a high-quality study assistant.

Create study material for:

Subject: {subject}
Topic: {topic}

The student wants material that feels like a smart student made it:
simple, friendly, organized, exam useful and easy to revise.

Return ONLY valid JSON. Do not use Markdown code fences.

Use exactly this structure:

{{
  "title": "topic title",
  "basic_idea": "easy explanation in simple language",
  "step_by_step": [
    "short step 1",
    "short step 2",
    "short step 3"
  ],
  "example": "easy real-life or academic example",
  "key_points": [
    "important point 1",
    "important point 2",
    "important point 3"
  ],
  "difficult_words": [
    {{"word": "term", "meaning": "very simple meaning"}}
  ],
  "memory_trick": "useful mnemonic or memory trick",
  "exam_points": [
    "important exam point 1",
    "important exam point 2"
  ],
  "types": [
    {{
      "name": "type name",
      "meaning": "simple meaning",
      "example": "short example"
    }}
  ],
  "diagram": {{
    "useful": true,
    "title": "simple diagram title",
    "steps": [
      "first box",
      "second box",
      "third box"
    ]
  }},
}}

Rules:
- Explain difficult terms simply.
- Keep each point concise.
- Types should contain important classifications if the topic has them.
- If there are no meaningful types, use [].
- Create a useful 3-8 step diagram when appropriate.
- If a diagram is not useful, set useful to false and steps to [].
- Do not generate quiz questions in this notes request; quizzes are generated separately when the student chooses the quiz size and difficulty.
- answer is the zero-based index of the correct option.
"""


    return ask_ollama(prompt)


# =========================================================
# QUIZ GENERATOR
# =========================================================

def generate_quiz(topic, subject, count, difficulty):
    prompt = f"""
You are Learnify AI, an exam-focused quiz generator.

Subject: {subject}
Topic: {topic}
Difficulty: {difficulty}
Number of questions: {count}

Create exactly {count} MCQs based ONLY on the topic.
Difficulty must be {difficulty}.
Use clear student-friendly language.

Return ONLY valid JSON. No Markdown and no code fences.

Format:
{{
  "quiz": [
    {{
      "question": "question",
      "options": ["option A", "option B", "option C", "option D"],
      "answer": 0,
      "explanation": "short explanation"
    }}
  ]
}}

Rules:
- Exactly {count} questions.
- Exactly 4 options per question.
- "answer" is the zero-based index (0, 1, 2, or 3) of the correct option.
- Avoid duplicate questions.
- Easy = direct concepts and simple recall.
- Moderate = understanding, application, comparison, or small scenarios.
- Difficult = deeper application, tricky concepts, multi-step reasoning, or close options.
- Keep explanations short and useful.
"""
    result = ask_ollama(prompt)
    quiz = result.get("quiz", [])

    if not isinstance(quiz, list) or len(quiz) != count:
        raise Exception(
            f"AI returned {len(quiz) if isinstance(quiz, list) else 0} questions instead of {count}."
        )

    return quiz


# =========================================================
# VISUAL DIAGRAM
# =========================================================

def show_diagram(diagram):

    if not diagram or not diagram.get("useful"):
        st.info(
            "No separate diagram is needed for this topic."
        )
        return

    steps = diagram.get("steps", [])

    if not steps:
        st.info(
            "No separate diagram is needed for this topic."
        )
        return

    st.markdown(
        f"### 📊 {diagram.get('title', 'Visual Diagram')}"
    )

    for i, step in enumerate(steps):

        st.markdown(
            f'<div class="diagram-box">{html.escape(str(step))}</div>',
            unsafe_allow_html=True
        )

        if i < len(steps) - 1:
            st.markdown(
                '<div class="arrow">↓</div>',
                unsafe_allow_html=True
            )


# =========================================================
# AUTH PAGE
# =========================================================

def auth_page():

    st.markdown(
        '<div class="auth-box">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="learnify-title">📚 Learnify AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Your personal AI study buddy'
        '</div>',
        unsafe_allow_html=True
    )

    login_tab, register_tab = st.tabs(
        ["🔐 Login", "✨ Create Account"]
    )

    with login_tab:

        st.subheader("Welcome back 👋")

        with st.form("login_form"):

            username = st.text_input(
                "Username"
            )

            password = st.text_input(
                "Password",
                type="password"
            )

            submitted = st.form_submit_button(
                "Login",
                use_container_width=True
            )

            if submitted:

                user = login_user(
                    username,
                    password
                )

                if user:

                    st.session_state.logged_in = True
                    st.session_state.user_id = user["id"]
                    st.session_state.username = user["username"]

                    load_user_data()

                    st.session_state.page = "home"

                    st.success(
                        "Login successful!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Incorrect username or password."
                    )

    with register_tab:

        st.subheader("Create your Learnify account 🚀")

        with st.form("register_form"):

            new_username = st.text_input(
                "Choose a username"
            )

            new_password = st.text_input(
                "Create password",
                type="password"
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password"
            )

            submitted = st.form_submit_button(
                "Create Account",
                use_container_width=True
            )

            if submitted:

                if new_password != confirm_password:

                    st.error(
                        "Passwords do not match."
                    )

                else:

                    success, message = create_user(
                        new_username,
                        new_password
                    )

                    if success:

                        st.success(
                            "Account created! You can now log in."
                        )

                    else:

                        st.error(message)

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# =========================================================
# TOP BAR
# =========================================================

def top_bar():

    # Persistent navigation lives in Streamlit's fixed left sidebar.
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand"><span class="sidebar-logo">▣</span>'
            '<span>Learnify <em>AI</em></span></div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="sidebar-caption">YOUR PERSONAL STUDY SPACE</div>',
            unsafe_allow_html=True
        )
        st.markdown('<div class="sidebar-section-label">WORKSPACE</div>', unsafe_allow_html=True)

        navigation = [
            ("home", "⌂", "Overview"),
            ("add_chapter", "＋", "New chapter"),
            ("history", "◷", "Learning history"),
        ]
        for page_key, symbol, label in navigation:
            if st.button(
                f"{symbol}  {label}",
                key=f"sidebar_nav_{page_key}",
                use_container_width=True,
                type="primary" if st.session_state.page == page_key else "secondary"
            ):
                st.session_state.page = page_key
                st.rerun()

        st.markdown('<div class="sidebar-section-label sidebar-library-label">YOUR LIBRARY</div>', unsafe_allow_html=True)
        chapters = st.session_state.get("chapters", [])
        if not chapters:
            st.markdown('<div class="sidebar-empty">Your chapters will appear here.</div>', unsafe_allow_html=True)
        else:
            for index, chapter in enumerate(chapters):
                is_current = (
                    st.session_state.page in ("chapter", "add_topic", "topic")
                    and st.session_state.get("current_chapter") == index
                )
                if st.button(
                    f"▤  {chapter['name']}",
                    key=f"sidebar_chapter_{chapter['id']}",
                    use_container_width=True,
                    type="primary" if is_current else "secondary"
                ):
                    st.session_state.current_chapter = index
                    st.session_state.page = "chapter"
                    st.rerun()

        st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="sidebar-user"><span class="sidebar-avatar">♙</span>'
            f'<span><b>{html.escape(str(st.session_state.username or "Student"))}</b>'
            '<small>Student account</small></span></div>',
            unsafe_allow_html=True
        )
        if st.button("↪  Log out", key="sidebar_logout", use_container_width=True):
            logout()

    st.markdown(
        '<div class="app-topline"><div class="top-brand">Learnify <span class="brand-ai">AI</span></div>'
        '<div class="topline-note">A calmer way to learn, one topic at a time.</div></div>',
        unsafe_allow_html=True
    )


# HOME
# =========================================================

def home_page():

    top_bar()

    username = html.escape(str(st.session_state.username or "there"))
    chapters = st.session_state.chapters

    total_chapters = len(chapters)
    total_topics = sum(len(ch.get("topics", [])) for ch in chapters)
    prepared_topics = sum(
        1 for ch in chapters for topic in ch.get("topics", [])
        if topic.get("material")
    )
    completion = round((prepared_topics / total_topics) * 100) if total_topics else 0

    conn = get_db()
    quiz_count = conn.execute(
        "SELECT COUNT(*) AS total FROM history WHERE user_id = ? AND action = 'Quiz completed'",
        (st.session_state.user_id,)
    ).fetchone()["total"]
    recent_rows = conn.execute(
        """
        SELECT h.action, h.score, h.total, h.created_at,
               t.name AS topic_name, c.name AS chapter_name
        FROM history h
        LEFT JOIN topics t ON h.topic_id = t.id
        LEFT JOIN chapters c ON t.chapter_id = c.id
        WHERE h.user_id = ?
        ORDER BY h.id DESC
        LIMIT 4
        """,
        (st.session_state.user_id,)
    ).fetchall()
    conn.close()

    st.markdown(
        f'<div class="dashboard-welcome"><div class="eyebrow">YOUR LEARNING SPACE</div>'
        f'<div class="learnify-title">Good to see you, {username} 👋</div>'
        '<div class="subtitle">A little progress every day adds up. What would you like to learn today?</div></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="hero dashboard-hero">
            <div class="hero-copy">
                <div class="badge">✦ YOUR PERSONAL AI STUDY COMPANION</div>
                <h2>Turn curiosity into confidence.</h2>
                <p>Create a chapter, explore a topic, understand it with AI-powered study notes,
                and check your knowledge with a quiz — all in one focused workspace.</p>
            </div>
            <div class="hero-mark">✧</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-heading">Your overview</div>', unsafe_allow_html=True)
    metric_cols = st.columns(4)
    metrics = [
        ("📚", "Chapters", total_chapters, "Your study collections"),
        ("📝", "Topics", total_topics, "Topics added"),
        ("✨", "Study packs", prepared_topics, "AI notes generated"),
        ("🎯", "Quizzes", quiz_count, "Completed attempts"),
    ]
    for col, (icon, label, value, hint) in zip(metric_cols, metrics):
        with col:
            st.markdown(
                f'<div class="stat-card"><div class="stat-icon">{icon}</div>'
                f'<div class="stat-value">{value}</div><div class="stat-label">{label}</div>'
                f'<div class="stat-hint">{hint}</div></div>',
                unsafe_allow_html=True
            )

    progress_col, action_col = st.columns([1.35, 1])
    with progress_col:
        st.markdown(
            f'<div class="panel-card"><div class="panel-title">📈 Your learning progress</div>'
            f'<div class="progress-number">{completion}% <span>of your topics have study packs</span></div>'
            f'<div class="progress-track"><div class="progress-fill" style="width:{completion}%"></div></div>'
            f'<div class="muted-copy">{prepared_topics} of {total_topics} topics prepared</div></div>',
            unsafe_allow_html=True
        )
    with action_col:
        st.markdown(
            '<div class="panel-card action-panel"><div class="panel-title">⚡ Quick action</div>'
            '<div class="muted-copy">Ready for your next learning session?</div>',
            unsafe_allow_html=True
        )
        if st.button("＋  Create a new chapter", use_container_width=True, type="primary", key="dashboard_add_chapter"):
            st.session_state.page = "add_chapter"
            st.rerun()
        if st.button("▤  View learning history", use_container_width=True, key="dashboard_history"):
            st.session_state.page = "history"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown('<div class="section-heading">📚 Your chapters</div>', unsafe_allow_html=True)
        if not chapters:
            st.markdown(
                '<div class="empty-state"><div class="empty-icon">📖</div>'
                '<b>Your learning space is ready.</b><p>Create your first chapter to start building your study library.</p></div>',
                unsafe_allow_html=True
            )
        else:
            for i, chapter in enumerate(chapters):
                topic_count = len(chapter.get("topics", []))
                ready_count = sum(1 for t in chapter.get("topics", []) if t.get("material"))
                st.markdown(
                    f'<div class="chapter-card"><div class="chapter-icon">📘</div>'
                    f'<div class="chapter-info"><b>{html.escape(str(chapter["name"]))}</b>'
                    f'<span>{html.escape(str(chapter["subject"]))} · {topic_count} topics · {ready_count} study packs ready</span></div></div>',
                    unsafe_allow_html=True
                )
                if st.button("Open chapter  →", key=f"open_chapter_{chapter['id']}", use_container_width=True):
                    st.session_state.current_chapter = i
                    st.session_state.page = "chapter"
                    st.rerun()

    with right:
        st.markdown('<div class="section-heading">🕘 Recent activity</div>', unsafe_allow_html=True)
        if not recent_rows:
            st.markdown(
                '<div class="empty-state"><div class="empty-icon">🌱</div>'
                '<b>Your activity will appear here.</b><p>Open a topic or complete a quiz to start your learning timeline.</p></div>',
                unsafe_allow_html=True
            )
        else:
            for row in recent_rows:
                action = html.escape(str(row["action"]))
                topic_name = html.escape(str(row["topic_name"] or "Study session"))
                chapter_name = html.escape(str(row["chapter_name"] or ""))
                date_text = html.escape(str(row["created_at"]).replace("T", " ")[:16])
                score_text = (
                    f' · Score {row["score"]}/{row["total"]}'
                    if row["score"] is not None and row["total"] else ""
                )
                st.markdown(
                    f'<div class="activity-item"><div class="activity-dot"></div>'
                    f'<div><b>{action}</b><div class="activity-topic">{topic_name}</div>'
                    f'<div class="activity-meta">{chapter_name}{score_text} · {date_text}</div></div></div>',
                    unsafe_allow_html=True
                )


# ADD CHAPTER
# =========================================================

def add_chapter_page():

    top_bar()

    st.title("➕ Create New Chapter")

    name = st.text_input(
        "Chapter Name",
        placeholder="Example: Artificial Intelligence"
    )

    subject = st.text_input(
        "Subject",
        placeholder="Example: Computer Science"
    )

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "← Back",
            use_container_width=True
        ):

            st.session_state.page = "home"
            st.rerun()

    with c2:

        if st.button(
            "Create Chapter 🚀",
            use_container_width=True
        ):

            if not name.strip():

                st.error(
                    "Please enter a chapter name."
                )

            elif not subject.strip():

                st.error(
                    "Please enter the subject."
                )

            else:

                conn = get_db()

                cur = conn.execute(
                    """
                    INSERT INTO chapters
                    (user_id, name, subject, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        st.session_state.user_id,
                        name.strip(),
                        subject.strip(),
                        datetime.now().isoformat(timespec="seconds")
                    )
                )

                chapter_id = cur.lastrowid

                conn.commit()
                conn.close()

                load_user_data()

                st.session_state.current_chapter = (
                    len(st.session_state.chapters) - 1
                )

                st.session_state.page = "chapter"

                st.rerun()


# =========================================================
# CHAPTER
# =========================================================

def chapter_page():

    top_bar()

    chapter = st.session_state.chapters[
        st.session_state.current_chapter
    ]

    st.title(
        f"📘 {chapter['name']}"
    )

    st.caption(
        f"Subject: {chapter['subject']}"
    )

    st.divider()

    st.markdown("### 📚 Topics")

    if not chapter["topics"]:

        st.info(
            "No topics yet. Add your first topic."
        )

    else:

        for i, topic in enumerate(
            chapter["topics"]
        ):

            ready = (
                "✅ Notes & Quiz ready"
                if topic.get("material")
                else "📝 Not prepared"
            )

            st.markdown(
                f"""
                <div class="card">
                    <b>📝 {html.escape(topic['name'])}</b><br>
                    <small>{ready}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                "Open Topic →",
                key=f"open_topic_{i}",
                use_container_width=True
            ):

                st.session_state.current_topic = i
                st.session_state.topic_section = "basic"
                st.session_state.page = "topic"

                st.rerun()

    st.divider()

    if st.button(
        "➕ Add New Topic",
        use_container_width=True
    ):

        st.session_state.page = "add_topic"
        st.rerun()

    if st.button(
        "← Back to Home",
        use_container_width=True
    ):

        st.session_state.page = "home"
        st.rerun()


# =========================================================
# ADD TOPIC
# =========================================================

def add_topic_page():

    top_bar()

    chapter = st.session_state.chapters[
        st.session_state.current_chapter
    ]

    st.title("➕ Add Topic")

    st.caption(
        f"Chapter: {chapter['name']}"
    )

    topic_name = st.text_input(
        "What do you want to learn?",
        placeholder="Example: What is Artificial Intelligence?"
    )

    if st.button(
        "Add Topic ✨",
        use_container_width=True
    ):

        if not topic_name.strip():

            st.error(
                "Please enter a topic."
            )

        else:

            conn = get_db()

            cur = conn.execute(
                """
                INSERT INTO topics
                (chapter_id, name, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    chapter["id"],
                    topic_name.strip(),
                    datetime.now().isoformat(timespec="seconds"),
                    datetime.now().isoformat(timespec="seconds")
                )
            )

            topic_id = cur.lastrowid

            conn.commit()
            conn.close()

            load_user_data()

            st.session_state.current_topic = len(
                st.session_state.chapters[
                    st.session_state.current_chapter
                ]["topics"]
            ) - 1

            st.session_state.topic_section = "basic"
            st.session_state.page = "topic"

            st.rerun()

    if st.button(
        "← Back",
        use_container_width=True
    ):

        st.session_state.page = "chapter"
        st.rerun()


# =========================================================
# TOPIC PAGE
# =========================================================

def topic_page():

    top_bar()

    chapter = st.session_state.chapters[
        st.session_state.current_chapter
    ]

    topic = chapter["topics"][
        st.session_state.current_topic
    ]

    st.title(
        f"📝 {topic['name']}"
    )

    st.caption(
        f"{chapter['subject']} • {chapter['name']}"
    )

    if not topic.get("material"):

        st.markdown(
            '<div class="ai-badge">'
            '🤖 Llama 3.2 • Local AI'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown("""
        ### ✨ Ready to learn?

        Learnify will create:

        **📖 Basic Idea**  
        Simple explanation, examples, difficult words,
        key points and memory tricks.

        **📊 Types & Visuals**  
        Important classifications and useful diagrams.

        **🧪 Quiz**  
        Five MCQs based specifically on this topic.
        """)

        if st.button(
            "✨ Prepare My Topic",
            use_container_width=True
        ):

            with st.spinner(
                "🧠 Learnify AI is preparing your topic..."
            ):

                try:

                    topic["material"] = generate_material(
                        topic["name"],
                        chapter["subject"]
                    )

                    topic["quiz_answers"] = {}
                    topic["quiz_submitted"] = False
                    topic["quiz_score"] = 0
                    topic["quiz_total"] = 0

                    save_material(topic)

                    add_history(
                        "Topic prepared",
                        topic["id"]
                    )

                    st.session_state.topic_section = "basic"

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Learnify could not generate the topic."
                    )

                    st.code(str(e))

        if st.button(
            "← Back to Chapter",
            use_container_width=True
        ):

            st.session_state.page = "chapter"
            st.rerun()

        return

    material = topic["material"]

    st.markdown(
        '<div class="ai-badge">'
        '✨ Topic Pack Ready'
        '</div>',
        unsafe_allow_html=True
    )

    b1, b2, b3 = st.columns(3)

    with b1:

        if st.button(
            "📖 1. Basic Idea",
            use_container_width=True
        ):

            st.session_state.topic_section = "basic"
            st.rerun()

    with b2:

        if st.button(
            "📊 2. Types & Visuals",
            use_container_width=True
        ):

            st.session_state.topic_section = "types"
            st.rerun()

    with b3:

        if st.button(
            "🧪 3. Quiz",
            use_container_width=True
        ):

            st.session_state.topic_section = "quiz"
            st.rerun()

    st.divider()

    # -----------------------------
    # BASIC
    # -----------------------------

    if st.session_state.topic_section == "basic":

        st.header("📖 Basic Idea")

        st.markdown(
            '<div class="card">'
            '<h3>📌 Simple Meaning</h3>'
            + html.escape(
                str(material.get("basic_idea", ""))
            )
            + "</div>",
            unsafe_allow_html=True
        )

        st.subheader(
            "🧠 Understand Step by Step"
        )

        for i, step in enumerate(
            material.get("step_by_step", []),
            1
        ):

            st.markdown(
                f"**{i}.** {step}"
            )

        st.subheader("💡 Easy Example")

        st.info(
            material.get(
                "example",
                "No example available."
            )
        )

        st.subheader("🔑 Important Points")

        for point in material.get(
            "key_points",
            []
        ):

            st.markdown(
                f"- {point}"
            )

        st.subheader(
            "📖 Difficult Words"
        )

        words = material.get(
            "difficult_words",
            []
        )

        if words:

            for item in words:

                st.markdown(
                    f"""
                    <div class="word">
                    <b>{html.escape(str(item.get("word", "")))}</b>
                    → {html.escape(str(item.get("meaning", "")))}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        else:

            st.info(
                "No special difficult words were identified."
            )

        st.subheader(
            "🧠 Memory Trick"
        )

        st.success(
            material.get(
                "memory_trick",
                "No special trick needed."
            )
        )

        st.subheader(
            "🎯 Exam Points"
        )

        for point in material.get(
            "exam_points",
            []
        ):

            st.markdown(
                f"- {point}"
            )

        st.subheader(
            "⚡ Quick Revision"
        )

        st.info(
            " ".join(
                material.get(
                    "key_points",
                    []
                )[:5]
            )
        )

    # -----------------------------
    # TYPES
    # -----------------------------

    elif st.session_state.topic_section == "types":

        st.header(
            "📊 Types & Visual Learning"
        )

        types = material.get(
            "types",
            []
        )

        if types:

            st.subheader(
                "🔹 Types / Classification"
            )

            for item in types:

                st.markdown(
                    f"""
                    <div class="card">
                        <h3>{html.escape(str(item.get('name', '')))}</h3>
                        <p>
                        <b>Meaning:</b>
                        {html.escape(str(item.get('meaning', '')))}
                        </p>
                        <p>
                        <b>Example:</b>
                        {html.escape(str(item.get('example', '')))}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        else:

            st.info(
                "This topic does not have important types/classifications."
            )

        st.divider()

        st.subheader(
            "🧩 Diagram / Flowchart"
        )

        show_diagram(
            material.get(
                "diagram",
                {}
            )
        )

    # -----------------------------
    # QUIZ
    # -----------------------------

    elif st.session_state.topic_section == "quiz":

        st.header("🧪 Topic Quiz")

        st.write(
            "Choose how many questions you want and how difficult "
            "you want the quiz to be."
        )

        # Quiz settings are kept separately so the student can
        # generate a new quiz without regenerating the notes.
        if "quiz_settings" not in topic:
            topic["quiz_settings"] = {
                "count": 5,
                "difficulty": "Easy"
            }

        if "generated_quiz" not in topic:
            topic["generated_quiz"] = None

        qcol1, qcol2 = st.columns(2)

        with qcol1:
            count_label = st.selectbox(
                "📝 Number of Questions",
                ["5 Questions", "10 Questions", "20 Questions"],
                index={
                    5: 0,
                    10: 1,
                    20: 2
                }.get(
                    topic["quiz_settings"].get("count", 5),
                    0
                ),
                key=f"quiz_count_{topic['id']}"
            )

        with qcol2:
            difficulty = st.selectbox(
                "🎯 Difficulty",
                ["Easy", "Moderate", "Difficult"],
                index=[
                    "Easy",
                    "Moderate",
                    "Difficult"
                ].index(
                    topic["quiz_settings"].get(
                        "difficulty",
                        "Easy"
                    )
                ),
                key=f"quiz_difficulty_{topic['id']}"
            )

        count = int(
            count_label.split()[0]
        )

        st.info(
            f"Your quiz: **{count} questions • {difficulty} level**"
        )

        if st.button(
            "🚀 Start Quiz",
            use_container_width=True
        ):

            with st.spinner(
                f"🧠 Creating {count} {difficulty.lower()} questions..."
            ):

                try:

                    quiz = generate_quiz(
                        topic["name"],
                        chapter["subject"],
                        count,
                        difficulty
                    )

                    topic["quiz_settings"] = {
                        "count": count,
                        "difficulty": difficulty
                    }

                    topic["generated_quiz"] = quiz
                    topic["quiz_answers"] = {}
                    topic["quiz_submitted"] = False
                    topic["quiz_score"] = 0
                    topic["quiz_total"] = count

                    save_quiz_state(topic)

                    # Keep the generated quiz in the same
                    # persisted material object for this topic.
                    topic["material"]["active_quiz"] = quiz
                    save_material(topic)

                    add_history(
                        f"{count}-question {difficulty} quiz started",
                        topic["id"]
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Could not create the quiz."
                    )
                    st.code(str(e))

        quiz = topic.get("generated_quiz")

        if not quiz:
            quiz = topic.get(
                "material",
                {}
            ).get(
                "active_quiz"
            )

        if not quiz:
            # If the student has not started a custom quiz yet,
            # do not automatically ask the old fixed 5 questions.
            st.markdown("""
            <div class="card">
                <h3>🎯 Choose your quiz</h3>
                <p>
                Pick <b>5, 10 or 20 questions</b> and select
                <b>Easy, Moderate or Difficult</b>.
                Then press <b>Start Quiz</b>.
                </p>
            </div>
            """, unsafe_allow_html=True)

        else:

            st.markdown(
                f"""
                <div class="card">
                    <b>🧪 {len(quiz)} Questions</b>
                    &nbsp;&nbsp;•&nbsp;&nbsp;
                    <b>🎯 {topic.get("quiz_settings", {}).get("difficulty", "Easy")}</b>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Answers are kept in session state until submission.
            for i, q in enumerate(quiz):

                st.markdown(
                    f"""
                    <div class="quiz-question">
                    <b>
                    Q{i+1}. {html.escape(str(q.get("question", "")))}
                    </b>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                options = q.get(
                    "options",
                    []
                )

                selected = st.radio(
                    "Choose one:",
                    options,
                    key=f"quiz_{topic['id']}_{i}",
                    index=None
                )

                topic["quiz_answers"][str(i)] = selected

            if st.button(
                "Check My Score 🎯",
                use_container_width=True
            ):

                unanswered = [
                    i + 1
                    for i, q in enumerate(quiz)
                    if not topic["quiz_answers"].get(str(i))
                ]

                if unanswered:

                    st.warning(
                        "Please answer all questions before checking your score. "
                        f"Unanswered: {', '.join(map(str, unanswered))}"
                    )

                else:

                    score = 0

                    for i, q in enumerate(quiz):

                        selected = topic[
                            "quiz_answers"
                        ].get(str(i))

                        options = q.get(
                            "options",
                            []
                        )

                        correct_index = q.get(
                            "answer",
                            0
                        )

                        if (
                            isinstance(
                                correct_index,
                                int
                            )
                            and 0 <= correct_index < len(options)
                            and selected == options[correct_index]
                        ):

                            score += 1

                    topic["quiz_submitted"] = True
                    topic["quiz_score"] = score
                    topic["quiz_total"] = len(quiz)

                    save_quiz_state(topic)

                    add_history(
                        "Quiz completed",
                        topic["id"],
                        score,
                        len(quiz)
                    )

                    st.rerun()

            if topic.get("quiz_submitted"):

                score = topic.get(
                    "quiz_score",
                    0
                )

                total = topic.get(
                    "quiz_total",
                    len(quiz)
                )

                st.divider()

                st.subheader(
                    f"🏆 Your Score: {score}/{total}"
                )

                percentage = round(
                    (score / total) * 100
                ) if total else 0

                st.progress(
                    percentage / 100
                )

                st.caption(
                    f"Accuracy: {percentage}%"
                )

                if score == total:

                    st.success(
                        "Excellent! Topic mastered! 🎉"
                    )

                elif score >= total * 0.6:

                    st.info(
                        "Good work! Revise the questions you missed."
                    )

                else:

                    st.warning(
                        "Revise the Basic Idea and try the quiz again."
                    )

                for i, q in enumerate(quiz):

                    selected = topic[
                        "quiz_answers"
                    ].get(str(i))

                    options = q.get(
                        "options",
                        []
                    )

                    correct_index = q.get(
                        "answer",
                        0
                    )

                    correct_answer = (
                        options[correct_index]
                        if isinstance(
                            correct_index,
                            int
                        )
                        and 0 <= correct_index < len(options)
                        else ""
                    )

                    if selected == correct_answer:

                        st.success(
                            f"Q{i+1}: Correct"
                        )

                    else:

                        st.error(
                            f"Q{i+1}: Correct answer → "
                            f"{correct_answer}"
                        )

                    st.caption(
                        q.get(
                            "explanation",
                            ""
                        )
                    )

            if st.button(
                "🔄 Create Another Quiz",
                use_container_width=True
            ):

                topic["generated_quiz"] = None
                topic["material"]["active_quiz"] = None
                topic["quiz_answers"] = {}
                topic["quiz_submitted"] = False
                topic["quiz_score"] = 0
                topic["quiz_total"] = 0

                save_material(topic)
                save_quiz_state(topic)

                st.rerun()

    st.divider()

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "🔄 Regenerate Topic Pack",
            use_container_width=True
        ):

            with st.spinner(
                "Creating a fresh topic pack..."
            ):

                try:

                    topic["material"] = generate_material(
                        topic["name"],
                        chapter["subject"]
                    )

                    topic["quiz_answers"] = {}
                    topic["quiz_submitted"] = False
                    topic["quiz_score"] = 0
                    topic["quiz_total"] = 0

                    save_material(topic)
                    save_quiz_state(topic)

                    add_history(
                        "Topic regenerated",
                        topic["id"]
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        str(e)
                    )

    with c2:

        if st.button(
            "← Back to Chapter",
            use_container_width=True
        ):

            st.session_state.page = "chapter"
            st.rerun()


# =========================================================
# HISTORY
# =========================================================

def history_page():

    top_bar()

    st.title(
        "📜 My Learning History"
    )

    st.write(
        "Your Learnify activity and quiz performance."
    )

    conn = get_db()

    rows = conn.execute(
        """
        SELECT
            h.*,
            t.name AS topic_name,
            c.name AS chapter_name
        FROM history h
        LEFT JOIN topics t
            ON h.topic_id = t.id
        LEFT JOIN chapters c
            ON t.chapter_id = c.id
        WHERE h.user_id = ?
        ORDER BY h.id DESC
        LIMIT 100
        """,
        (
            st.session_state.user_id,
        )
    ).fetchall()

    conn.close()

    if not rows:

        st.info(
            "No activity yet. Start learning a topic!"
        )

    else:

        for row in rows:

            time_text = row["created_at"].replace(
                "T",
                " "
            )

            if row["action"] == "Quiz completed":

                st.markdown(
                    f"""
                    <div class="history-item">
                    🧪 <b>Quiz completed</b><br>
                    Topic: <b>{html.escape(str(row["topic_name"]))}</b><br>
                    Chapter: {html.escape(str(row["chapter_name"]))}<br>
                    🏆 Score: <b>{row["score"]}/{row["total"]}</b><br>
                    <small>{time_text}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    f"""
                    <div class="history-item">
                    ✨ <b>{html.escape(str(row["action"]))}</b><br>
                    Topic: <b>{html.escape(str(row["topic_name"]))}</b><br>
                    Chapter: {html.escape(str(row["chapter_name"]))}<br>
                    <small>{time_text}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    st.divider()

    if st.button(
        "← Back to Home",
        use_container_width=True
    ):

        st.session_state.page = "home"
        st.rerun()


# =========================================================
# ROUTER
# =========================================================

if not st.session_state.logged_in:

    auth_page()

else:

    if st.session_state.page == "home":
        home_page()

    elif st.session_state.page == "add_chapter":
        add_chapter_page()

    elif st.session_state.page == "chapter":
        chapter_page()

    elif st.session_state.page == "add_topic":
        add_topic_page()

    elif st.session_state.page == "topic":
        topic_page()

    elif st.session_state.page == "history":
        history_page()
