"""Factory for creating RAG store instances with dependency injection."""

import logging
from typing import Optional

from config.settings import Settings
from .interfaces import EmbeddingProvider, VectorStore, RAGStore
from .embeddings import OpenAIEmbeddingProvider
from .stores import MongoVectorStore, FixChainRAGStore

logger = logging.getLogger(__name__)


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Create an embedding provider based on configuration.
    
    Args:
        settings: Application settings
        
    Returns:
        Configured embedding provider
        
    Raises:
        ValueError: If required configuration is missing
    """
    if not settings.openai_api_key:
        raise ValueError("OpenAI API key is required for embedding provider")
    
    return OpenAIEmbeddingProvider(
        api_key=settings.openai_api_key,
        model=settings.embedding_model,
        max_retries=settings.max_retries
    )


def create_vector_store(settings: Settings) -> VectorStore:
    """Create a vector store based on configuration.
    
    Args:
        settings: Application settings
        
    Returns:
        Configured vector store
    """
    return MongoVectorStore(
        mongodb_uri=settings.mongodb_uri,
        database_name=settings.database_name,
        collection_name=settings.collection_name,
        timeout=settings.timeout
    )


def create_rag_store(settings: Optional[Settings] = None) -> RAGStore:
    """Create a complete RAG store with all dependencies.
    
    Args:
        settings: Optional application settings. If None, will load from environment.
        
    Returns:
        Configured RAG store
        
    Raises:
        ValueError: If required configuration is missing
    """
    if settings is None:
        from config import get_settings
        settings = get_settings()
    
    logger.info("Creating RAG store components...")
    
    # Create embedding provider
    embedding_provider = create_embedding_provider(settings)
    logger.info(f"Created embedding provider: {type(embedding_provider).__name__}")
    
    # Create vector store
    vector_store = create_vector_store(settings)
    logger.info(f"Created vector store: {type(vector_store).__name__}")
    
    # Create RAG store
    rag_store = FixChainRAGStore(
        embedding_provider=embedding_provider,
        vector_store=vector_store
    )
    
    logger.info("RAG store created successfully")
    return rag_store


class RAGStoreBuilder:
    """Builder pattern for creating customized RAG stores."""
    
    def __init__(self):
        self._embedding_provider: Optional[EmbeddingProvider] = None
        self._vector_store: Optional[VectorStore] = None
    
    def with_embedding_provider(self, provider: EmbeddingProvider) -> 'RAGStoreBuilder':
        """Set the embedding provider.
        
        Args:
            provider: Embedding provider instance
            
        Returns:
            Builder instance for chaining
        """
        self._embedding_provider = provider
        return self
    
    def with_vector_store(self, store: VectorStore) -> 'RAGStoreBuilder':
        """Set the vector store.
        
        Args:
            store: Vector store instance
            
        Returns:
            Builder instance for chaining
        """
        self._vector_store = store
        return self
    
    def with_openai_embeddings(self, api_key: str, model: str = "text-embedding-ada-002") -> 'RAGStoreBuilder':
        """Configure OpenAI embeddings.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model name
            
        Returns:
            Builder instance for chaining
        """
        self._embedding_provider = OpenAIEmbeddingProvider(api_key=api_key, model=model)
        return self
    
    def with_mongo_store(self, mongodb_uri: str, database_name: str = "fixchain", 
                        collection_name: str = "rag_insights") -> 'RAGStoreBuilder':
        """Configure MongoDB vector store.
        
        Args:
            mongodb_uri: MongoDB connection URI
            database_name: Database name
            collection_name: Collection name
            
        Returns:
            Builder instance for chaining
        """
        self._vector_store = MongoVectorStore(
            mongodb_uri=mongodb_uri,
            database_name=database_name,
            collection_name=collection_name
        )
        return self
    
    def build(self) -> RAGStore:
        """Build the RAG store with configured components.
        
        Returns:
            Configured RAG store
            
        Raises:
            ValueError: If required components are not configured
        """
        if self._embedding_provider is None:
            raise ValueError("Embedding provider must be configured")
        
        if self._vector_store is None:
            raise ValueError("Vector store must be configured")
        
        return FixChainRAGStore(
            embedding_provider=self._embedding_provider,
            vector_store=self._vector_store
        )