<div align="center">

# 🧠 PDF Mind RAG — AI-Powered PDF Chatbot

**A Production-Ready Retrieval-Augmented Generation (RAG) System built with FastAPI, LangChain, ChromaDB, HuggingFace Embeddings, and OpenRouter API.**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://www.langchain.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6B6B?style=for-the-badge&logo=database&logoColor=white)](https://www.trychroma.com/)
[![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter_API-6366F1?style=for-the-badge&logo=openai&logoColor=white)](https://openrouter.ai/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

</div>

---

## ✨ Features

- 📄 **Dynamic PDF Document Ingestion**: Upload any PDF document; automatically extracts text and parses page-level metadata using `PyPDF`.
- ✂️ **Semantic Text Chunking**: Uses `RecursiveCharacterTextSplitter` (800 character chunk size with 150 character overlap) to preserve sentence context.
- ⚡ **Local CPU Vector Embeddings**: Employs HuggingFace `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional embeddings) running 100% free locally on CPU.
- 💾 **Embedded Vector Store**: Uses `ChromaDB` persisted locally in `./data/chroma_db` — zero external DB servers or Docker containers required!
- 🌐 **OpenRouter LLM Integration**: Connects seamlessly with OpenRouter API, supporting models like Google Gemini, Meta Llama 3.3 70B, and DeepSeek R1.
- 🔍 **Strict Grounded QA with Citations**: Returns answers strictly grounded in retrieved PDF context along with exact page number citations and snippet previews.
- 🎨 **Glassmorphism Web UI**: Includes a sleek, dark-themed responsive dashboard for drag-and-drop file uploads, real-time chat, and system metrics.
- 🐳 **Dockerized Deployment**: Fully containerized setup with optimized builds (pre-downloads the embedding model to avoid runtime downloads) for quick cloud deployments (e.g. Render, Koyeb).
- 🛠️ **Full OpenAPI Documentation**: Automatic interactive API swagger documentation served at `/docs`.

---

## 🏛️ System Architecture

```
                               ┌────────────────────────────────┐
                               │       User Uploads PDF         │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
                               ┌────────────────────────────────┐
                               │  FastAPI Endpoint /api/upload  │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │ PyPDFLoader Text Extraction      │
                              │ RecursiveCharacterTextSplitter   │
                              └───────────────┬──────────────────┘
                                              │
                                              ▼
                              ┌──────────────────────────────────┐
                              │ HuggingFace Embeddings           │
                              │ (all-MiniLM-L6-v2 on CPU)        │
                              └───────────────┬──────────────────┘
                                              │
                                              ▼
                              ┌──────────────────────────────────┐
                              │ ChromaDB Local Vector Store      │
                              │ (Persisted at ./data/chroma_db) │
                              └───────────────┬──────────────────┘
                                              │
                                              ▼
┌──────────────────┐          ┌──────────────────────────────────┐          ┌──────────────────┐
│  User Question   ├─────────►│ Similarity Search (Top 4 Chunks) ├─────────►│ OpenRouter LLM   │
└──────────────────┘          └──────────────────────────────────┘          └────────┬─────────┘
                                                                                     │
                                                                                     ▼
                                                                            ┌──────────────────┐
                                                                            │ Answer + Page    │
                                                                            │ Source Citations │
                                                                            └──────────────────┘
```

---

## 📁 Repository Structure

```
pdf-chatbot-rag/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Centralized settings & env configuration
│   ├── rag_engine.py        # Core RAG pipeline (Loader, Splitter, ChromaDB, OpenRouter)
│   ├── main.py              # FastAPI application routes & middleware
│   └── static/              # Interactive Glassmorphic Web Dashboard
│       ├── index.html       # HTML UI Markup
│       ├── style.css        # CSS Styling & Glassmorphism Theme
│       └── script.js        # Frontend REST API Integration
├── data/                    # Vector store & uploaded files storage (Gitignored)
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
├── ARCHITECTURE.md          # Detailed System Architecture & Recruiter Interview Guide
├── PROGRESS.md              # Milestone tracking & feature verification document
└── README.md                # Project master documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** installed on your system.
- An **OpenRouter API Key** (Get your free/paid key from [OpenRouter Keys](https://openrouter.ai/keys)).

### 2. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/parinbajayebin/pdf-chatbot-rag.git
cd pdf-chatbot-rag

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your OpenRouter API key:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
LLM_MODEL=google/gemini-2.0-flash-lite-preview-02-05:free
```

### 5. Run Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Open your browser and navigate to:
- 🌐 **Web Dashboard UI**: `http://localhost:8000`
- 📚 **Swagger API Docs**: `http://localhost:8000/docs`

### 🐳 Alternative: Run using Docker
You can build and run the application containerized to avoid local Python configuration issues:

1. **Build the Docker Image**:
   ```bash
   docker build -t pdf-chatbot-rag .
   ```

2. **Run the Docker Container**:
   Make sure your `.env` file contains your `OPENROUTER_API_KEY`, then run:
   ```bash
   docker run -d -p 8000:8000 --env-file .env pdf-chatbot-rag
   ```
   Access the web dashboard at `http://localhost:8000`.

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/` | `GET` | Serves interactive web dashboard |
| `/api/upload` | `POST` | Upload and index a PDF file into ChromaDB |
| `/api/chat` | `POST` | Ask a question and receive RAG answer with page citations |
| `/api/status` | `GET` | Get total indexed vector count, LLM model, and uploaded files |
| `/api/reset` | `POST` | Reset vector database and clear uploaded documents |

---

## 🎤 Interview & Recruiter Explanation Guide

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for a comprehensive guide on how to explain this project's architecture, technical trade-offs (e.g. ChromaDB vs PGVector), and design decisions in technical interviews.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
