"""Pydantic schemas for FixChain RAG system."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ReasoningEntry(BaseModel):
    """Schema for reasoning entry metadata."""
    bug_id: Optional[str] = Field(None, description="Unique identifier for the bug")
    test_name: Optional[str] = Field(None, description="Name of the test that found the bug")
    iteration: Optional[int] = Field(None, description="Iteration number in the fix process")
    category: Optional[str] = Field(None, description="Category of the test (e.g., static, dynamic)")
    tool: Optional[str] = Field(None, description="Tool used for testing (e.g., bandit, pylint)")
    status: Optional[str] = Field(None, description="Status of the test (pass, fail, error)")
    timestamp: Optional[str] = Field(None, description="When the reasoning was recorded")
    source_file: Optional[str] = Field(None, description="Source file where the issue was found")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")
    
    # Legacy fields for backward compatibility
    method_name: Optional[str] = Field(None, description="Method or function name where bug occurred")
    fix_type: Optional[str] = Field(None, description="Type of fix applied")
    severity: Optional[str] = Field(None, description="Bug severity level")
    file_path: Optional[str] = Field(None, description="Path to the file containing the bug")
    line_number: Optional[int] = Field(None, description="Line number where the bug occurred")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchResult(BaseModel):
    """Schema for search results."""
    content: str = Field(..., description="The reasoning content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Associated metadata")
    score: Optional[float] = Field(None, description="Similarity score")
    document_id: Optional[str] = Field(None, description="Document ID in the database")


class RAGConfig(BaseModel):
    """Configuration schema for RAG system."""
    mongodb_uri: str = Field(..., description="MongoDB connection URI")
    database_name: str = Field(default="fixchain", description="Database name")
    collection_name: str = Field(default="rag_insights", description="Collection name for RAG insights")
    index_name: str = Field(default="vector_index", description="Vector search index name")
    embedding_model: str = Field(default="text-embedding-ada-002", description="Embedding model name")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout: int = Field(default=30, description="Connection timeout in seconds")