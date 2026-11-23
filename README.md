# Learnify AI

**Learn a topic. Understand it. Test yourself.**

Learnify AI is a personal AI study companion that turns a student's topic into clear notes, visual explanations, memory aids and topic-based quizzes.

## Features

- Student registration and login
- Personal chapters, topics and learning history
- AI-generated, student-friendly notes
- Step-by-step explanations and examples
- Difficult-word definitions and key points
- Memory tricks and exam-focused revision points
- Topic classifications and simple flowcharts
- Custom MCQ quizzes (5, 10 or 20 questions)
- Easy, Moderate and Difficult quiz levels
- Score tracking with answer explanations

## Technology

- **App:** Python + Streamlit
- **Local AI:** Ollama + Llama 3.2
- **Database:** SQLite
- **HTTP client:** Requests

## Requirements

- Python 3.9 or newer
- [Ollama](https://ollama.com/) installed and running
- The `llama3.2` model downloaded in Ollama

## Run locally

1. Clone the repository:

   ```bash
   git clone https://github.com/khushic851-blip/Learnify_AI.git
   cd Learnify_AI
   ```

2. Install Python dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Download the local model:

   ```bash
   ollama pull llama3.2
   ```

4. Start Ollama (if it is not already running), then launch Learnify:

   ```bash
   streamlit run app.py
   ```

5. Open the local URL printed by Streamlit in your browser.

## Data and privacy

The current version stores account, chapter, topic and quiz data in a local SQLite database named `learnify.db`. The AI requests are sent to the local Ollama service at `http://localhost:11434`; this version does not require a hosted AI API key.

For a public deployment, configure persistent database storage, HTTPS, secure secrets and an appropriate authentication/session strategy before inviting real users.

## Project structure

```text
Learnify_AI/
├── app.py
├── requirements.txt
├── test_ai.py
└── README.md
```

## Project goal

Make learning more understandable and active by bringing explanations, revision support and self-assessment into one simple workspace.
