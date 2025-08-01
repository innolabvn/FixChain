"""Configuration settings for FixChain RAG system."""

import os
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB settings
    mongodb_uri: str = Field(
        default="mongodb://admin:password123@localhost:27017/fixchain?authSource=admin",
        env="MONGODB_URI",
        description="MongoDB connection URI"
    )
    database_name: str = Field(
        default="fixchain",
        env="DATABASE_NAME",
        description="MongoDB database name"
    )
    collection_name: str = Field(
        default="rag_insights",
        env="COLLECTION_NAME",
        description="MongoDB collection name for RAG insights"
    )
    
    # OpenAI settings
    openai_api_key: Optional[str] = Field(
        default=None,
        env="OPENAI_API_KEY",
        description="OpenAI API key for embeddings"
    )
    embedding_model: str = Field(
        default="text-embedding-ada-002",
        env="EMBEDDING_MODEL",
        description="OpenAI embedding model name"
    )
    
    # Vector search settings
    vector_index_name: str = Field(
        default="vector_index",
        env="VECTOR_INDEX_NAME",
        description="Vector search index name"
    )
    embedding_dimensions: int = Field(
        default=1536,
        env="EMBEDDING_DIMENSIONS",
        description="Embedding vector dimensions"
    )
    
    # Application settings
    max_retries: int = Field(
        default=3,
        env="MAX_RETRIES",
        description="Maximum retry attempts for operations"
    )
    timeout: int = Field(
        default=30,
        env="TIMEOUT",
        description="Connection timeout in seconds"
    )
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    
    # Development settings
    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="Enable debug mode"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()