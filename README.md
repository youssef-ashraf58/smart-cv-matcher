# Smart CV Matcher — Technical Report & README

**Version:** 1.0.0 | **Team Role:** Backend + DevOps Engineer

---

## Executive Summary

Smart CV Matcher is an end-to-end Retrieval-Augmented Generation (RAG) system that ingests raw CV PDFs (English and Arabic) and answers natural-language questions about candidates — e.g., _"Is this candidate suitable for a Data Analyst role?"_ — using retrieved CV context injected into an LLM.

The system is fully containerized via Docker and exposes a clean REST API built with FastAPI following MVC architecture principles.

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Client (curl / Postman / UI)        │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP
┌───────────────────────▼─────────────────────────────┐
│              FastAPI Backend (Port 8000)             │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │  /health │  │ /cv/*    │  │ /query/ask        │  │
│  └──────────┘  └────┬─────┘  └────────┬──────────┘  │
│                     │                 │              │
│          ┌──────────▼─────────────────▼──────────┐  │
│          │           Services Layer               │  │
│          │  pdf_parser → vector_store → rag_pipe  │  │
│          │              llm_factory               │  │
│          └──────────────────┬────────────────────┘  │
└─────────────────────────────┼───────────────────────┘
                              │
        ┌─────────────────────┼──────────────────┐
        │                     │                  │
┌───────▼──────┐   ┌──────────▼────────┐  ┌─────▼────────┐
│  ChromaDB    │   │ Sentence-Transform │  │ LLM Provider │
│  (local vec  │   │ (multilingual emb) │  │ Gemini/OAI/  │
│   database)  │   │  runs in container │  │ Ollama       │
└──────────────┘   └───────────────────┘  └──────────────┘
```

---

## API Documentation

### Base URL: `http://localhost:8000`

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| GET | `/health` | System status check | — |
| POST | `/cv/upload` | Upload a CV PDF | `multipart/form-data` file |
| GET | `/cv/list` | List all uploaded CVs | — |
| DELETE | `/cv/{filename}` | Remove a CV | — |
| POST | `/query/ask` | Ask a question (RAG) | JSON (see below) |

#### POST `/query/ask` — Request Body
```json
{
  "question": "Is this candidate suitable for a data analyst role?",
  "cv_filename": "john_doe.pdf",   // optional — omit to search all CVs
  "top_k": 5,                      // optional — chunks to retrieve
  "llm_provider": "gemini"         // optional — override provider per request
}
```

#### POST `/query/ask` — Response
```json
{
  "question": "Is this candidate suitable for a data analyst role?",
  "answer": "Based on the CV, the candidate has 3 years of experience with Python and SQL...",
  "llm_provider": "gemini",
  "retrieved_chunks": [
    {
      "text": "Skills: Python, SQL, Tableau, Excel...",
      "source": "john_doe.pdf",
      "chunk_id": "uuid-here",
      "score": 0.87
    }
  ],
  "total_chunks_searched": 42
}
```

---

## Embedding Model Choice

**Model:** `paraphrase-multilingual-MiniLM-L12-v2`

- **Why:** Supports 50+ languages including Arabic natively — no separate model needed.
- **Size:** ~120MB — fast to load, runs on CPU, no GPU required.
- **Accuracy:** Trained on parallel multilingual corpora; cosine similarity is highly reliable for semantic CV matching.
- **Free:** Runs entirely inside the Docker container, zero API cost.

---

## Chunking Strategy

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Chunk size | 400 tokens | ~300 words — covers one CV section (e.g., a full job experience entry) without diluting retrieval |
| Overlap | 50 tokens | Prevents sentences split across chunk boundaries from losing meaning |
| Method | Word-based sliding window | Simple, fast, language-agnostic; works with both Arabic and English |

---

## Arabic NLP Handling

1. **Detection:** Unicode range check (U+0600–U+06FF) before langdetect for reliability.
2. **Normalization:** Removes tashkeel (diacritics), normalizes Alef variants (أإآ → ا), Ya (ى → ي), Ta Marbuta (ة → ه). This prevents the same word written two ways from getting different embeddings.
3. **RTL extraction:** `pdfplumber` extracts text at character level preserving RTL order.
4. **Embedding:** Same multilingual model handles Arabic without any special switch.

---

## LLM Factory Pattern

```
get_llm(provider)
    ├── "gemini" → GeminiLLM (Google Gemini 1.5 Flash — free tier)
    ├── "openai" → OpenAILLM (GPT-4o-mini)
    └── "ollama" → OllamaLLM (local Mistral/Llama3 — fully offline)
```

Switch provider per-request via the `llm_provider` field, or globally via `LLM_PROVIDER` in `.env`.

---

## Docker Deployment Instructions

### Prerequisites
- Docker Desktop installed and running
- A free Gemini API key from [aistudio.google.com](https://aistudio.google.com)

### Step-by-step

```bash
# 1. Clone / navigate to the project
cd smart-cv-matcher

# 2. Create your .env file
cp .env.example .env
# Then edit .env and paste your GEMINI_API_KEY

# 3. Build and start
docker-compose up --build

# 4. Open the API docs
# Visit http://localhost:8000/docs in your browser
```

---

## Project Structure

```
smart-cv-matcher/
├── app/
│   ├── main.py              # FastAPI app + middleware
│   ├── api/                 # Controllers (MVC: C)
│   │   ├── health.py
│   │   ├── cv_routes.py
│   │   └── query_routes.py
│   ├── models/              # Pydantic schemas (MVC: M)
│   │   └── schemas.py
│   ├── services/            # Business logic (MVC: V / Service layer)
│   │   ├── pdf_parser.py    # PDF ingestion + Arabic normalization
│   │   ├── vector_store.py  # ChromaDB wrapper
│   │   ├── llm_factory.py   # Factory pattern for LLM providers
│   │   └── rag_pipeline.py  # Full RAG orchestration
│   └── core/
│       └── config.py        # Centralized settings
├── data/cvs/                # Uploaded CVs stored here
├── chroma_db/               # ChromaDB persisted data
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── .gitignore
```
