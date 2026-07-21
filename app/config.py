import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME: str = "PDF Chatbot RAG System"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Retrieval-Augmented Generation (RAG) system for querying PDFs using FastAPI, ChromaDB, and OpenRouter API."
    
    # OpenRouter API settings
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openrouter/free")
    
    # HuggingFace API key for cloud embeddings
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", os.getenv("HF_TOKEN", ""))
    
    # Vector store & document settings
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", str(BASE_DIR / "data" / "chroma_db"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads"))
    
    # HuggingFace Embedding Model
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Chunking parameters
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 800))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 150))
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", 4))
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))

settings = Settings()

# Ensure directories exist
os.makedirs(settings.CHROMA_DB_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
