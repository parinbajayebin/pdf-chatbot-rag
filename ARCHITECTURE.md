# 🏗️ PDF Chatbot RAG — System Architecture & Interview Guide

This document provides a comprehensive technical breakdown of the **Retrieval-Augmented Generation (RAG) Architecture** implemented in this application. It is designed to help software engineers explain this GenAI project to tech leads, hiring managers, and recruiters during technical interviews.

---

## 📐 1. System Architecture Diagram

```mermaid
flowchart TD
    subgraph Data_Ingestion_Pipeline["1. Document Ingestion Pipeline"]
        PDF["📄 PDF Document"] --> Loader["PyPDFLoader (LangChain)"]
        Loader --> RawText["Extracted Text & Page Metadata"]
        RawText --> Splitter["RecursiveCharacterTextSplitter\n(Chunk Size: 800, Overlap: 150)"]
        Splitter --> Chunks["Text Chunks + Metadata"]
    end

    subgraph Embedding_and_Vector_DB["2. Vector Embedding & Database Persistence"]
        Chunks --> Embedder["HuggingFace Embeddings\n(sentence-transformers/all-MiniLM-L6-v2)"]
        Embedder --> VectorEmbeddings["384-Dimensional Vectors"]
        VectorEmbeddings --> Chroma["ChromaDB Local Vector Store\n(Cosine Similarity Search)"]
    end

    subgraph RAG_Query_Chain["3. Retrieval & QA Generation Pipeline"]
        UserQuery["❓ User Question"] --> QueryEmbedder["Generate Query Embedding"]
        QueryEmbedder --> VectorSearch["Top-K Similarity Retrieval (k=4)"]
        Chroma --> VectorSearch
        VectorSearch --> ContextPassages["Relevant Context Passages + Page Numbers"]
        
        ContextPassages --> PromptTemplate["Custom ChatPromptTemplate\n(Context + Strict Grounding Instructions)"]
        UserQuery --> PromptTemplate
        
        PromptTemplate --> LLM["OpenRouter API\n(Google Gemini / DeepSeek / Llama 3)"]
        LLM --> FinalResponse["💬 Grounded Response + Source Citations"]
    end
```

---

## 🔬 2. Component-by-Component Breakdown

### Component 1: Data Ingestion & Semantic Chunking
* **Library**: `langchain_community.document_loaders.PyPDFLoader` & `RecursiveCharacterTextSplitter`.
* **Mechanism**: 
  - The PDF document is parsed page-by-page. Metadata like `source_filename` and `page_number` are attached to each document.
  - The raw text is divided into chunks of **800 characters** with a **150 character overlap**.
* **Why recursive character chunking?**
  - Unlike naive chunking (by fixed length), recursive chunking respects double newlines, single newlines, and space boundaries, ensuring complete sentences and paragraphs remain together without losing semantic context.

---

### Component 2: Vector Embeddings
* **Model**: `sentence-transformers/all-MiniLM-L6-v2` via `langchain-huggingface`.
* **Output Dimension**: 384 dimensions.
* **Why this model?**
  - 100% free, lightweight (~90MB), and runs CPU-friendly with zero external API call latency.
  - High accuracy for semantic similarity tasks in English.

---

### Component 3: Vector Store (ChromaDB)
* **Database**: `ChromaDB` (embedded mode).
* **Storage Location**: Persisted locally in `./data/chroma_db`.
* **Search Metric**: Cosine Distance / Similarity.
* **Why ChromaDB instead of PostgreSQL PGVector?**
  - ChromaDB requires **zero external infrastructure or Docker setups**. It runs natively inside the Python process and persists data to disk automatically.

---

### Component 4: Retrieval-Augmented Generation (RAG Chain)
* **API Provider**: OpenRouter API (`https://openrouter.ai/api/v1`).
* **Client**: LangChain `ChatOpenAI` initialized with OpenRouter base URL.
* **Grounding & Guardrails**:
  - The system prompt enforces that the LLM **must only answer using the retrieved context passages**. If context is insufficient, it responds with a clear disclaimer rather than hallucinating.

---

## 🎤 3. How to Explain This Project to Recruiters & Interviewers

When asked: *"Can you explain your PDF Chatbot RAG project?"*, use this structured **STAR-style explanation**:

### 1. High-Level Elevator Pitch (30 seconds)
> *"I built an end-to-end Retrieval-Augmented Generation (RAG) system using FastAPI, LangChain, ChromaDB, and OpenRouter API. The app allows users to upload any PDF document, automatically extracts and embeds its semantic content, and allows users to ask questions in plain English with answers backed by exact page citations."*

### 2. Technical Stack & Trade-offs (60 seconds)
> *"For the architecture, I made specific design choices:*
> * **Vector Store**: I selected ChromaDB for lightweight embedded local persistence without needing heavy external Docker instances like PostgreSQL/PGVector.
> * **Embeddings**: I used HuggingFace's `all-MiniLM-L6-v2` model running locally on CPU to generate 384-dimensional embeddings at zero cost and minimal latency.
> * **LLM Integration**: I integrated OpenRouter API using LangChain's standard OpenAI client interface, allowing easy model switching between Gemini, Llama 3, and DeepSeek.
> * **API & UI**: The backend is built with FastAPI featuring background PDF parsing and interactive Swagger documentation, complemented by a modern glassmorphic web dashboard."*

### 3. Key Challenges & Solutions (40 seconds)
> *"One challenge in RAG is preventing hallucinations and context loss. To solve this, I implemented recursive text chunking with 150-character overlap to preserve sentence structure across chunk boundaries. Additionally, I crafted a strict system prompt that instructs the LLM to only answer if context is present and to cite page numbers for full transparency."*
