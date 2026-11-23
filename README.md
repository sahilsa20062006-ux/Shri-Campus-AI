# Shri Campus AI

> **Intelligent College Assistant for Shri Ram Institute of Science & Technology (SRIST), Jabalpur, Madhya Pradesh, India**

Built as a B.Tech AIML capstone project. Shri Campus AI provides accurate, hallucination-free campus assistance powered by a structured JSON knowledge base and local Qwen LLM via Ollama.

---

## 🏛️ Project Overview

Shri Campus AI assists students in finding verified information regarding:
- Departments (B.Tech, MBA) and branches (CSE, AIML, IoT)
- Faculty members, HODs, and their office locations
- Classrooms across academic years and sections
- Laboratories, administrative offices, and campus facilities
- Natural bilingual queries in **English**, **Hindi**, and **Hinglish**

### 🔒 Single Source of Truth
All campus facts are retrieved strictly from `data/srist_knowledge_base.json` (extracted directly from the verified SRIST campus documentation). The assistant never hallucinates unverified faculty, rooms, or walking paths.

---

## 🏗️ Technology Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn, Pydantic v2, HTTPX
- **AI / LLM**: Local `qwen3.5:4b` hosted on Ollama (`http://localhost:11434`)
- **Retrieval Engine**: Hybrid Token & Semantic keyword matching + Hindi/Hinglish intent expansion + FAQ ranker
- **Frontend**: Clean Modern Responsive Single Page Application (HTML5, Modern CSS Variables, Vanilla JS)
- **Design**: Premium AI product UI, animated splash screen (~2s), hero section, feature cards, sample questions, interactive chat with optional starting location, responsive on Mobile/Tablet/Desktop

---

## 📁 Project Directory Structure

```text
shri campus ai/
│
├── .env                              # Environment configuration
├── requirements.txt                  # Python dependencies
├── run.py                            # One-click application runner
├── run_all_tests.py                  # Complete test suite runner
├── README.md                         # Documentation & usage guide
│
├── data/
│   └── srist_knowledge_base.json     # Single source of truth (61 FAQs, faculty, rooms, labs)
│
├── backend/
│   ├── __init__.py
│   ├── config.py                     # App configuration & settings
│   ├── models.py                     # Pydantic request/response schemas
│   ├── knowledge.py                  # Knowledge base loader, indexing & search
│   ├── ollama_service.py             # Ollama client & system prompt orchestration
│   ├── chat.py                       # Conversation manager & RAG pipeline
│   └── main.py                       # FastAPI application & static file server
│
├── frontend/
│   ├── index.html                    # Unified modern frontend (Splash, Landing, Chat)
│   └── logo.png                      # Official SRIST emblem
│
└── tests/
    ├── test_knowledge.py             # 62 unit tests for data integrity & search
    ├── test_chat.py                  # 22 tests for conversation & Ollama integration
    ├── test_api.py                   # 22 integration tests for FastAPI endpoints
    └── test_questions.py             # 15 tests verifying mandatory prompt questions
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Ollama running locally with `qwen3.5:4b`:
  ```bash
  ollama run qwen3.5:4b
  ```

### 2. Installation
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
The `.env` file is pre-configured:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:4b
KNOWLEDGE_BASE_PATH=data/srist_knowledge_base.json
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
MAX_CONVERSATION_HISTORY=10
REQUEST_TIMEOUT=120
```

### 4. Running the Application
Start the full stack (FastAPI backend + frontend static server) with a single command:
```bash
python run.py
```
Open your browser at:
👉 **`http://localhost:8000`**

---

## 🧪 Testing

Run the full comprehensive test suite with:
```bash
python run_all_tests.py
```

### Test Breakdown:
- **`tests/test_knowledge.py`** (62 tests): Validates JSON schema, verified faculty names, room numbers, floor associations, non-invention of missing facts, and FAQ entries.
- **`tests/test_chat.py`** (22 tests): Validates conversation state, session memory, query context enrichment (e.g. "Where is his office?"), and live Ollama inference.
- **`tests/test_api.py`** (22 tests): Validates FastAPI endpoints (`/api/health`, `/api/chat`, `/api/knowledge/status`, `/api/knowledge/search`, `/`, `/logo.png`).
- **`tests/test_questions.py`** (15 tests): Tests all questions explicitly specified in the project specification.

---

## 📝 Updating College Information

The chatbot reads the college directory dynamically from `data/srist_knowledge_base.json`. **No code modifications are required to update campus data.**

1. Open `data/srist_knowledge_base.json`.
2. Update or add items to the relevant section:
   - `"faculty"`: Add or modify faculty designation, room, and floor.
   - `"rooms"`: Add rooms under `"ground_floor"`, `"first_floor"`, `"second_floor"`, or `"third_floor"`.
   - `"classrooms"`: Update room numbers and floor for specific branch/year.
   - `"labs"`: Add lab names, room numbers, and floors.
   - `"faq"`: Add new question-and-answer pairs.
3. Save the file.
4. Restart the server (or with `reload=True`, changes take effect immediately).
