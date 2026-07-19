# 🏆 AI Powered Sports Quiz Generation Agent

An AI agent that generates factually grounded, unique, multiple-choice sports quizzes
on demand — combining a **ChromaDB vector knowledge base**, **live DuckDuckGo web search**,
and an **LLM (OpenAI GPT-4o or Google Gemini)** inside a proper **Retrieval-Augmented
Generation (RAG)** pipeline, served through a polished **Streamlit** dashboard.

---

## 1. Project Overview

| | |
|---|---|
| **Goal** | Generate engaging, accurate, social-media-ready sports quizzes that are never hallucinated |
| **Sports supported** | Cricket, Football, Basketball, Tennis, Badminton, Hockey, Kabaddi, Formula 1, Olympics |
| **Difficulty levels** | Easy, Medium, Hard |
| **Questions per quiz** | 4–5 (configurable) |
| **Grounding sources** | ChromaDB (curated historical facts) + DuckDuckGo (live web results) |
| **LLM providers** | OpenAI (`gpt-4o` / `gpt-4.1`) or Google Gemini (`gemini-1.5-pro`) |

The agent is explicitly instructed — via a strict system prompt — to **only use retrieved
context** when writing questions. If context is insufficient, it generates fewer questions
rather than inventing facts. Every generated quiz is validated against a Pydantic schema
before being shown to the user, so malformed or hallucinated output never reaches the UI.

---

## 2. Architecture

```
                 ┌─────────────────┐
                 │   Streamlit UI   │   app.py + src/ui/
                 └────────┬─────────┘
                          │
                 ┌────────▼─────────┐
                 │   RAG Pipeline    │   src/rag/pipeline.py
                 └───┬──────────┬────┘
                     │          │
        ┌────────────▼───┐  ┌───▼─────────────────┐
        │  ChromaDB       │  │  DuckDuckGo Search   │
        │  (historical)   │  │  (live/current)      │
        │ src/database/   │  │ src/search/          │
        └────────────┬────┘  └───┬──────────────────┘
                      │           │
                 ┌────▼───────────▼────┐
                 │   Merged RAG Context  │   src/models/schema.py (RAGContext)
                 └───────────┬───────────┘
                             │
                 ┌───────────▼────────────┐
                 │  Prompt Engineering      │   src/llm/prompts.py
                 │  (system + user prompt)  │
                 └───────────┬────────────┘
                             │
                 ┌───────────▼────────────┐
                 │   LLM Client              │   src/llm/client.py
                 │  (OpenAI / Gemini)        │
                 └───────────┬────────────┘
                             │
                 ┌───────────▼────────────┐
                 │  Pydantic Validation     │   src/models/schema.py (Quiz)
                 └───────────┬────────────┘
                             │
                 ┌───────────▼────────────┐
                 │   Rendered Quiz UI        │   src/ui/components.py
                 └────────────────────────┘
```

### RAG Workflow (as implemented)

1. **User Input** — user selects a sport + difficulty in the sidebar and clicks *Generate Quiz*.
2. **Historical Retrieval** — `ChromaDBManager.query_by_sport()` performs a semantic
   (embedding-based) search over the `sports_facts` collection, filtered by sport metadata.
3. **Live Web Search** — `WebSearchClient.search_sport()` queries DuckDuckGo for recent
   news, winners, and records, and cleans/truncates the snippets.
4. **Merge Context** — both sources are combined into a single `RAGContext` object
   (`src/models/schema.py`), which is rendered into a labeled, readable text block.
5. **Grounded Prompt** — `build_user_prompt()` embeds the merged context into a prompt
   that explicitly forbids the model from using outside knowledge, plus a difficulty-specific
   instruction and a randomization hint (to keep regenerations fresh).
6. **Generation** — `LLMClient.generate_quiz()` calls the configured provider, requesting
   strict JSON output, and retries with exponential backoff on transient failures.
7. **Validation** — the raw JSON is parsed and validated against the `Quiz` / `QuizQuestion`
   Pydantic models (distinct options, no duplicate questions, 3–6 question bounds, valid
   answer key). Invalid output raises `QuizGenerationError` instead of reaching the UI.
8. **Display** — the quiz renders as interactive cards; the exact retrieved context is
   shown in an expandable "transparency panel" so users can verify grounding themselves.

---

## 3. Folder Structure

```
sports_quiz_agent/
├── app.py                      # Streamlit entrypoint (thin orchestration layer)
├── requirements.txt
├── .env.example
├── README.md
├── config/
│   └── settings.py             # Centralized, typed configuration (all env vars load here)
├── data/
│   └── sports_facts.json       # Curated knowledge base ingested into ChromaDB
├── src/
│   ├── database/
│   │   ├── chroma_client.py    # ChromaDB connection, embedding, upsert, query
│   │   └── populate_db.py      # Loads sports_facts.json into ChromaDB
│   ├── search/
│   │   └── web_search.py       # DuckDuckGo live search + cleaning
│   ├── rag/
│   │   └── pipeline.py         # Orchestrates retrieval + context merging
│   ├── llm/
│   │   ├── prompts.py          # System prompt + difficulty logic + prompt builder
│   │   └── client.py           # OpenAI / Gemini client, JSON parsing, retries
│   ├── models/
│   │   └── schema.py           # Pydantic models: Quiz, QuizQuestion, RAGContext, etc.
│   ├── utils/
│   │   ├── logger.py           # App-wide logging setup
│   │   ├── export.py           # JSON / Markdown / PDF / social caption export
│   │   └── quiz_ops.py         # Shuffle questions / shuffle options
│   └── ui/
│       ├── components.py       # Reusable Streamlit rendering components
│       └── styles.py           # Custom CSS (dark-theme-friendly)
├── static/
│   └── assets/                 # Place logos / images here
├── logs/                       # Rotating log files (created at runtime)
└── chroma_store/                # Persistent ChromaDB storage (created at runtime)
```

**Design principle:** UI, RAG, prompting, database, search, config, models, and utilities
are all separated into independent modules — no business logic lives inside `app.py`.

---

## 4. Features

### Core (required)
- ✅ Sport selector (9 sports) and difficulty selector (Easy / Medium / Hard)
- ✅ Generate Quiz / Regenerate Quiz (guaranteed different questions via topic-avoidance + randomization seed)
- ✅ 4–5 MCQ questions per quiz, each with 4 options, correct answer, and explanation
- ✅ Full RAG pipeline: ChromaDB + DuckDuckGo → merged context → grounded LLM prompt
- ✅ Anti-hallucination system prompt; degrades to fewer questions instead of fabricating facts
- ✅ Expandable, transparent "Retrieved RAG Context" panel

### Bonus
- ✅ Quiz history (session-based, shown in sidebar)
- ✅ Download as JSON, Markdown, and PDF
- ✅ Social-media-ready copy/caption generator
- ✅ Shuffle Questions / Shuffle Options
- ✅ Session quiz timer (elapsed time while taking the quiz)
- ✅ Answer reveal with correct/incorrect highlighting
- ✅ Live scoring (X / total, %)

---

## 5. Installation

### Prerequisites
- Python 3.10+
- An OpenAI API key **or** a Google Gemini API key

### Steps

```bash
# 1. Clone / unzip the project, then move into it
cd sports_quiz_agent

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# then edit .env and add your OPENAI_API_KEY (or GEMINI_API_KEY + LLM_PROVIDER=gemini)

# 5. Run the app
streamlit run app.py
```

On first launch, the app automatically populates ChromaDB from `data/sports_facts.json`
(this only happens once — subsequent runs reuse the persisted `chroma_store/` directory).

---

## 6. Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Required | Description |
|---|---|---|
| `LLM_PROVIDER` | Yes | `openai` or `gemini` |
| `OPENAI_API_KEY` | If provider is `openai` | Your OpenAI API key |
| `OPENAI_MODEL` | No | Defaults to `gpt-4o` |
| `GEMINI_API_KEY` | If provider is `gemini` | Your Google AI Studio API key |
| `GEMINI_MODEL` | No | Defaults to `gemini-1.5-pro` |
| `CHROMA_PERSIST_DIR` | No | Where ChromaDB stores its local files |
| `EMBEDDING_MODEL` | No | Sentence-Transformers model for embeddings |
| `WEB_SEARCH_MAX_RESULTS` | No | Max DuckDuckGo results per sport |

---

## 7. Running Instructions

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (typically `http://localhost:8501`).

**Usage:**
1. Pick a **Sport** and **Difficulty** in the sidebar.
2. Click **Generate Quiz**.
3. Answer the questions, then click **Submit Answers & Reveal** to see your score,
   correct answers, and explanations — or click **Regenerate** anytime for a new quiz.
4. Use the **Shuffle** buttons to reorder questions/options, and the **Export & Share**
   panel to download the quiz or copy a social media caption.
5. Expand **View Retrieved RAG Context** to see exactly what grounded the quiz.

---

## 8. Screenshots

> _Add screenshots here after running the app locally, e.g.:_
> - `static/assets/screenshot-dashboard.png`
> - `static/assets/screenshot-quiz.png`
> - `static/assets/screenshot-context-panel.png`

---

## 9. Code Quality

- **PEP8** formatting, full **type hints**, and **docstrings** throughout
- **Pydantic** models validate every LLM response before display
- **SOLID**-oriented module boundaries (each class has a single responsibility)
- Centralized **logging** (`src/utils/logger.py`) with rotating file handler
- **Retry with exponential backoff** (`tenacity`) around LLM calls
- Graceful degradation: if live web search fails, the pipeline continues with
  ChromaDB-only context instead of crashing

---

## 10. Future Improvements

- Add a persistent (cross-session) quiz history using a lightweight database (SQLite)
- Add user authentication and per-user leaderboards
- Expand the ChromaDB knowledge base with a scheduled ingestion job pulling from
  sports statistics APIs
- Add multi-language quiz generation
- Add image-based questions (e.g. "identify this stadium/player") using a vision model
- Add automated evaluation (LLM-as-judge) to score factual grounding of each quiz before display

---

## 11. Tech Stack

Python · Streamlit · LangChain · OpenAI API / Google Gemini API · ChromaDB ·
Sentence-Transformers · DuckDuckGo Search · Pydantic · python-dotenv · fpdf2 · tenacity

---

## 12. Troubleshooting

### `ImportError: DLL load failed while importing cygrpc: An Application Control policy has blocked this file`

This happens on Windows machines with **Application Control** policies (Windows Defender
Application Control, Smart App Control, or a corporate endpoint-security product). ChromaDB
unconditionally imports OpenTelemetry's gRPC-based OTLP exporter at package-import time —
even though this project never uses ChromaDB's telemetry feature — and that import pulls in
`grpcio`'s compiled `cygrpc` native extension. Your machine's security policy is blocking that
unsigned/untrusted native DLL from loading, which crashes the app before it starts.

**This is already fixed in the codebase** via `config/telemetry_shim.py`, which registers a
no-op stand-in for that specific gRPC exporter submodule *before* ChromaDB is imported, so the
native extension is never touched. If you still see this error:

1. Make sure you're running the latest version of `src/database/chroma_client.py` (it should
   import `config.telemetry_shim` before `import chromadb`).
2. Delete `chroma_store/` and any stale `__pycache__` folders, then re-run `streamlit run app.py`.
3. If the error persists, your policy may also be blocking a *different* native dependency
   (e.g. from `sentence-transformers`/PyTorch). Ask your IT administrator to allow Python
   virtual-environment DLLs, or run the project inside WSL2/a Linux VM where such policies
   typically don't apply.

### `OPENAI_API_KEY is missing` / generation fails immediately
Make sure you copied `.env.example` to `.env` (not just edited the example file) and that it
sits in the project root, next to `app.py`.
