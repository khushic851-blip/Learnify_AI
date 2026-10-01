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
.stApp {
    background: #f7f8fc;
}

#MainMenu, footer {
    visibility: hidden;
}

.learnify-title {
    font-size: 48px;
    font-weight: 800;
    letter-spacing: -1px;
}

.subtitle {
    color: #666;
    font-size: 19px;
    margin-bottom: 25px;
}

.hero {
    padding: 30px;
    border-radius: 24px;
    background: linear-gradient(135deg, #ffffff, #eef3ff);
    border: 1px solid #e2e6ef;
    margin-bottom: 24px;
}

.card {
    padding: 22px;
    border-radius: 18px;
    background: white;
    border: 1px solid #e5e7eb;
    margin-bottom: 14px;
}

.word {
    padding: 12px 15px;
    background: #f5f7ff;
    border-radius: 12px;
    margin: 7px 0;
}

.diagram-box {
    padding: 18px;
    border-radius: 16px;
    background: white;
    border: 2px solid #dfe5f5;
    text-align: center;
    font-weight: 700;
    margin: 5px;
}

.arrow {
    text-align: center;
    font-size: 25px;
    font-weight: 800;
    margin: 2px 0;
}

.badge {
    display: inline-block;
    padding: 7px 13px;
    border-radius: 20px;
    background: #eef2ff;
    color: #4f46e5;
    font-size: 13px;
    font-weight: 700;
}

.ai-badge {
    display: inline-block;
    padding: 7px 13px;
    border-radius: 20px;
    background: #ecfdf5;
    color: #047857;
    font-size: 13px;
    font-weight: 700;
}

.quiz-question {
    padding: 20px;
    border-radius: 18px;
    background: white;
    border: 1px solid #e5e7eb;
    margin: 15px 0;
}

.auth-box {
    max-width: 600px;
    margin: 50px auto;
}

.history-item {
    padding: 18px;
    border-radius: 16px;
    background: white;
    border: 1px solid #e5e7eb;
    margin-bottom: 12px;
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

    c1, c2, c3 = st.columns(
        [5, 2, 1]
    )

    with c1:
        st.markdown(
            f"### 📚 Learnify AI"
        )

    with c2:
        st.caption(
            f"👤 {st.session_state.username}"
        )

    with c3:
        if st.button(
            "Logout",
            key="logout_top"
        ):
            logout()


# =========================================================
# HOME
# =========================================================

def home_page():

    top_bar()

    st.markdown(
        '<div class="learnify-title">Welcome back 👋</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Learn • Practice • Track your progress'
        '</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    total_chapters = len(
        st.session_state.chapters
    )

    total_topics = sum(
        len(ch["topics"])
        for ch in st.session_state.chapters
    )

    prepared_topics = sum(
        1
        for ch in st.session_state.chapters
        for topic in ch["topics"]
        if topic.get("material")
    )

    with c1:
        st.metric(
            "📚 Chapters",
            total_chapters
        )

    with c2:
        st.metric(
            "📝 Topics",
            total_topics
        )

    with c3:
        st.metric(
            "✨ Prepared",
            prepared_topics
        )

    st.markdown("""
    <div class="hero">
        <div class="badge">LOCAL AI POWERED</div>
        <h2>Learn a topic. Understand it. Test yourself.</h2>
        <p>
        Learnify turns your topic into easy notes, visual learning,
        difficult-word meanings, memory tricks, exam points and a quiz.
        Your chapters and learning history are saved locally.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        if st.button(
            "➕ Add New Chapter",
            use_container_width=True
        ):
            st.session_state.page = "add_chapter"
            st.rerun()

    with c2:
        if st.button(
            "📜 My History",
            use_container_width=True
        ):
            st.session_state.page = "history"
            st.rerun()

    st.divider()
    st.markdown("### 📚 Your Chapters")

    if not st.session_state.chapters:

        st.info(
            "No chapters yet. Create your first chapter."
        )

    else:

        for i, chapter in enumerate(
            st.session_state.chapters
        ):

            count = len(
                chapter["topics"]
            )

            if st.button(
                f"📘 {chapter['name']}  •  "
                f"{chapter['subject']}  •  "
                f"{count} topics",
                key=f"chapter_{i}",
                use_container_width=True
            ):

                st.session_state.current_chapter = i
                st.session_state.page = "chapter"
                st.rerun()


# =========================================================
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
