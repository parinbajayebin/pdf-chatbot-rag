import os
import shutil
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.rag_engine import get_rag_engine

# FastAPI Initialization
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class ChatRequest(BaseModel):
    question: str = Field(..., example="What are the key findings in this document?", description="Question to ask based on uploaded PDF documents")

class SourceCitation(BaseModel):
    id: int
    filename: str
    page: int
    snippet: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    indexed_chunks_count: int

class StatusResponse(BaseModel):
    status: str
    indexed_chunks: int
    total_documents: int
    uploaded_files: List[str]
    embedding_model: str
    llm_model: str

class ResetResponse(BaseModel):
    status: str
    message: str


# Mount Static Files (Frontend UI)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serves the main HTML interface."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse(
        content="<h1>PDF Chatbot RAG System API</h1><p>Visit <a href='/docs'>/docs</a> for API documentation or <a href='/static/index.html'>/static/index.html</a> for web UI.</p>"
    )


@app.post("/api/upload", status_code=200)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Endpoint to upload and index a PDF document.
    Extracted text is split into chunks and stored in ChromaDB vector database.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF (.pdf) files are supported.")

    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)

    try:
        # Save file locally
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Index document into ChromaDB
        rag_engine = get_rag_engine()
        result = rag_engine.process_and_index_pdf(file_path, file.filename)

        return {
            "message": f"File '{file.filename}' uploaded and indexed successfully.",
            "details": result
        }
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF document: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_pdf(request: ChatRequest):
    """
    Endpoint to perform retrieval-augmented question answering.
    Retrieves top matching document passages and queries the OpenRouter LLM.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        rag_engine = get_rag_engine()
        response = rag_engine.generate_rag_response(request.question)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing RAG query: {str(e)}")


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Returns the current vector store status, model details, and uploaded files."""
    try:
        rag_engine = get_rag_engine()
        return rag_engine.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system status: {str(e)}")


@app.post("/api/reset", response_model=ResetResponse)
async def reset_system():
    """Resets the vector database and deletes all uploaded PDF files."""
    try:
        rag_engine = get_rag_engine()
        return rag_engine.reset_database()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset system: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
