import os
import shutil
from typing import List, Dict, Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import settings

class RAGEngine:
    """
    RAGEngine handles the complete Retrieval-Augmented Generation lifecycle:
    1. Document loading & text extraction (PyPDFLoader)
    2. Document chunking (RecursiveCharacterTextSplitter)
    3. Embedding generation (HuggingFace Endpoint API)
    4. Vector persistence (ChromaDB)
    5. Contextual QA generation (OpenRouter API + LangChain chain)
    """

    def __init__(self):
        print(f"Initializing Hosted Embedding Model: {settings.EMBEDDING_MODEL_NAME}...")
        
        # Check if Hugging Face API key is set
        api_key = settings.HUGGINGFACE_API_KEY
        if not api_key:
            print("WARNING: HuggingFace API key (HUGGINGFACE_API_KEY / HF_TOKEN) is not configured.")
            
        self.embeddings = HuggingFaceEndpointEmbeddings(
            model=settings.EMBEDDING_MODEL_NAME,
            task="feature-extraction",
            huggingfacehub_api_token=api_key if api_key else "dummy-key"
        )
        
        self.vector_db = Chroma(
            persist_directory=settings.CHROMA_DB_DIR,
            embedding_function=self.embeddings,
            collection_name="pdf_rag_collection"
        )
        
        self._init_llm_chain()

    def _init_llm_chain(self):
        """Initializes the OpenRouter LLM and LangChain retrieval QA prompt chain."""
        api_key = settings.OPENROUTER_API_KEY
        if not api_key or api_key == "your_openrouter_api_key_here":
            print("WARNING: OpenRouter API key not configured in .env file.")

        self.llm = ChatOpenAI(
            model_name=settings.LLM_MODEL,
            openai_api_key=api_key if api_key else "dummy-key",
            openai_api_base=settings.OPENROUTER_BASE_URL,
            temperature=0.2,
            default_headers={
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "PDF Chatbot RAG System"
            }
        )

        system_prompt = (
            "You are a helpful, precise, and polite AI Assistant designed to answer user questions "
            "based strictly on the provided context retrieved from PDF documents.\n\n"
            "Guidelines:\n"
            "1. Base your answer ONLY on the provided context snippets.\n"
            "2. If the context does not contain enough information to answer the question, state clearly: "
            "'I cannot find sufficient information in the uploaded document(s) to answer your question.'\n"
            "3. Keep your response structured, well-formatted, and concise.\n"
            "4. Always mention relevant page numbers or document references if available in context metadata.\n\n"
            "Context:\n{context}\n\n"
            "User Question: {question}"
        )

        self.prompt_template = ChatPromptTemplate.from_template(system_prompt)
        self.qa_chain = self.prompt_template | self.llm | StrOutputParser()

    def process_and_index_pdf(self, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Loads a PDF file, splits it into semantic text chunks, and indexes it into ChromaDB.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at path: {file_path}")

        # 1. Extract text using PyPDFLoader
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        if not documents:
            raise ValueError("The uploaded PDF document appears to be empty or unreadable.")

        # Attach metadata to documents
        for i, doc in enumerate(documents):
            doc.metadata["source_filename"] = filename
            if "page" in doc.metadata:
                doc.metadata["page_number"] = doc.metadata["page"] + 1

        # 2. Text Chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)

        # 3. Store in ChromaDB
        try:
            self.vector_db.add_documents(chunks)
        except Exception as e:
            if "Authorization" in str(e) or "401" in str(e) or "credentials" in str(e).lower() or "token" in str(e).lower():
                raise ValueError("Hugging Face API key is invalid or missing. Please configure HUGGINGFACE_API_KEY correctly.")
            raise ValueError(f"Failed to generate embeddings via Hugging Face API: {str(e)}")

        return {
            "filename": filename,
            "total_pages": len(documents),
            "chunks_created": len(chunks),
            "status": "indexed_successfully"
        }

    def generate_rag_response(self, question: str, top_k: int = settings.TOP_K_RESULTS) -> Dict[str, Any]:
        """
        Executes Retrieval-Augmented Generation for a given question.
        Returns the generated answer along with retrieved source document citations.
        """
        # Check if vector DB has documents
        collection_count = self.vector_db._collection.count()
        if collection_count == 0:
            return {
                "answer": "No PDF documents have been uploaded yet. Please upload a PDF document first.",
                "sources": [],
                "indexed_chunks_count": 0
            }

        # 1. Similarity Retrieval
        try:
            retrieved_docs = self.vector_db.similarity_search(query=question, k=top_k)
        except Exception as e:
            if "Authorization" in str(e) or "401" in str(e) or "credentials" in str(e).lower() or "token" in str(e).lower():
                return {
                    "answer": "⚠️ **Hugging Face API Key Error**: The `HUGGINGFACE_API_KEY` is missing or invalid. Please check your credentials.",
                    "sources": [],
                    "indexed_chunks_count": collection_count
                }
            return {
                "answer": f"Error performing similarity search: {str(e)}",
                "sources": [],
                "indexed_chunks_count": collection_count
            }

        if not retrieved_docs:
            return {
                "answer": "No relevant context found in the uploaded documents to answer your question.",
                "sources": [],
                "indexed_chunks_count": collection_count
            }

        # 2. Format Context and Collect Sources
        context_str = ""
        sources = []
        for i, doc in enumerate(retrieved_docs, start=1):
            source_file = doc.metadata.get("source_filename", "Uploaded Document")
            page_num = doc.metadata.get("page_number", doc.metadata.get("page", "N/A"))
            snippet = doc.page_content.strip()
            
            context_str += f"[Source {i} | {source_file} - Page {page_num}]:\n{snippet}\n\n"
            
            sources.append({
                "id": i,
                "filename": source_file,
                "page": page_num,
                "snippet": snippet[:200] + "..." if len(snippet) > 200 else snippet
            })

        # 3. Check for API key before calling LLM
        if not settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY == "your_openrouter_api_key_here":
            return {
                "answer": (
                    "⚠️ **API Key Missing**: OpenRouter API key is not configured in your `.env` file.\n\n"
                    "**Retrieved Context Passages from your PDF:**\n\n" + 
                    "\n".join([f"**Source {s['id']} ({s['filename']} - Page {s['page']})**:\n{s['snippet']}\n" for s in sources]) +
                    "\n\n*To enable AI-generated answers, please set `OPENROUTER_API_KEY` in your `.env` file.*"
                ),
                "sources": sources,
                "indexed_chunks_count": collection_count
            }

        # 4. Generate LLM Answer
        try:
            answer = self.qa_chain.invoke({
                "context": context_str,
                "question": question
            })
        except Exception as e:
            answer = f"Error communicating with LLM API ({settings.LLM_MODEL}): {str(e)}"

        return {
            "answer": answer,
            "sources": sources,
            "indexed_chunks_count": collection_count
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns the current vector store status and indexed document metrics."""
        count = self.vector_db._collection.count()
        
        # Collect list of uploaded files
        uploaded_files = []
        if os.path.exists(settings.UPLOAD_DIR):
            uploaded_files = [f for f in os.listdir(settings.UPLOAD_DIR) if f.endswith(".pdf")]

        return {
            "status": "online",
            "indexed_chunks": count,
            "total_documents": len(uploaded_files),
            "uploaded_files": uploaded_files,
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "llm_model": settings.LLM_MODEL
        }

    def reset_database(self) -> Dict[str, Any]:
        """Clears all vectors from ChromaDB and deletes uploaded files."""
        try:
            self.vector_db.delete_collection()
            self.vector_db = Chroma(
                persist_directory=settings.CHROMA_DB_DIR,
                embedding_function=self.embeddings,
                collection_name="pdf_rag_collection"
            )
            
            # Clean uploads directory
            if os.path.exists(settings.UPLOAD_DIR):
                shutil.rmtree(settings.UPLOAD_DIR)
                os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
                
            return {"status": "success", "message": "Database and uploaded files successfully cleared."}
        except Exception as e:
            return {"status": "error", "message": f"Failed to reset database: {str(e)}"}

# Global RAG Engine Instance (Lazy Singleton)
_rag_engine_instance = None

def get_rag_engine() -> RAGEngine:
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = RAGEngine()
    return _rag_engine_instance
