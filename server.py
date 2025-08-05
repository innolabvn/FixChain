#!/usr/bin/env python3
"""FastAPI server for FixChain service."""

import logging
import sys
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from config import get_settings
from rag import create_rag_store, create_mongodb_only_rag_store
from rag.interfaces import RAGStore
from models.schemas import ReasoningEntry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/fixchain.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

# Global RAG store instance
rag_store: Optional[RAGStore] = None

# Pydantic models for API
class ReasoningEntryRequest(BaseModel):
    content: str
    metadata: Dict

class SearchRequest(BaseModel):
    query: str
    k: int = 5
    filter_criteria: Optional[Dict] = None

class SearchResult(BaseModel):
    content: str
    metadata: Dict
    score: float

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    rag_store_connected: bool

# FastAPI app
app = FastAPI(
    title="FixChain AI Service",
    description="AI-powered bug detection and RAG system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize RAG store on startup."""
    global rag_store
    try:
        logger.info("Initializing FixChain RAG store...")
        settings = get_settings()
        rag_store = create_mongodb_only_rag_store(
            mongodb_uri=settings.mongodb_uri,
            database_name=settings.database_name,
            collection_name=settings.collection_name,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2"
        )
        logger.info("FixChain RAG store initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG store: {e}")
        # Don't fail startup, just log the error
        rag_store = None

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global rag_store
    if rag_store:
        try:
            rag_store.close()
            logger.info("RAG store closed successfully")
        except Exception as e:
            logger.error(f"Error closing RAG store: {e}")

def get_rag_store() -> RAGStore:
    """Dependency to get RAG store instance."""
    if rag_store is None:
        raise HTTPException(status_code=503, detail="RAG store not available")
    return rag_store

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        rag_store_connected=rag_store is not None
    )

@app.post("/api/reasoning/add")
async def add_reasoning_entry(
    request: ReasoningEntryRequest,
    store: RAGStore = Depends(get_rag_store)
):
    """Add a reasoning entry to the RAG store."""
    try:
        # Add timestamp if not present
        if "timestamp" not in request.metadata:
            request.metadata["timestamp"] = datetime.now().isoformat()
        
        doc_id = store.add_reasoning_entry(request.content, request.metadata)
        return {"status": "success", "doc_id": doc_id}
    except Exception as e:
        logger.error(f"Failed to add reasoning entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reasoning/search", response_model=List[SearchResult])
async def search_reasoning(
    request: SearchRequest,
    store: RAGStore = Depends(get_rag_store)
):
    """Search for similar reasoning entries."""
    try:
        results = store.retrieve_similar_entries(
            request.query,
            k=request.k,
            filter_criteria=request.filter_criteria
        )
        
        return [
            SearchResult(
                content=result.content,
                metadata=result.metadata,
                score=result.score
            )
            for result in results
        ]
    except Exception as e:
        logger.error(f"Failed to search reasoning entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reasoning/stats")
async def get_stats(
    store: RAGStore = Depends(get_rag_store)
):
    """Get collection statistics."""
    try:
        stats = store.get_collection_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/reasoning/{doc_id}")
async def delete_reasoning_entry(
    doc_id: str,
    store: RAGStore = Depends(get_rag_store)
):
    """Delete a reasoning entry."""
    try:
        success = store.delete_entry(doc_id)
        if success:
            return {"status": "success", "message": "Entry deleted"}
        else:
            raise HTTPException(status_code=404, detail="Entry not found")
    except Exception as e:
        logger.error(f"Failed to delete reasoning entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )