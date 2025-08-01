"""Abstract interfaces for FixChain RAG system following SOLID principles."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from models.schemas import SearchResult


class EmbeddingProvider(ABC):
    """Abstract interface for embedding providers."""
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for given text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding vector
        """
        pass
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for multiple texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Get the dimensionality of the embedding vectors."""
        pass


class VectorStore(ABC):
    """Abstract interface for vector storage backends."""
    
    @abstractmethod
    def add_document(self, content: str, embedding: List[float], metadata: Dict[str, Any]) -> str:
        """Add a document with its embedding to the store.
        
        Args:
            content: Document content
            embedding: Embedding vector
            metadata: Document metadata
            
        Returns:
            Document ID
        """
        pass
    
    @abstractmethod
    def search_similar(self, query_embedding: List[float], k: int = 3, 
                      filter_criteria: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar documents using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filter_criteria: Optional metadata filters
            
        Returns:
            List of search results with similarity scores
        """
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID.
        
        Args:
            document_id: ID of document to delete
            
        Returns:
            True if deletion was successful
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the connection to the vector store."""
        pass


class RAGStore(ABC):
    """Abstract interface for RAG storage and retrieval operations."""
    
    @abstractmethod
    def add_reasoning_entry(self, content: str, metadata: Dict[str, Any]) -> str:
        """Add a reasoning entry to the RAG store.
        
        Args:
            content: Reasoning content text
            metadata: Associated metadata
            
        Returns:
            Document ID of the added entry
        """
        pass
    
    @abstractmethod
    def retrieve_similar_entries(self, query: str, k: int = 3, 
                               filter_criteria: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Retrieve semantically similar reasoning entries.
        
        Args:
            query: Query string
            k: Number of results to return
            filter_criteria: Optional metadata filters
            
        Returns:
            List of similar reasoning entries
        """
        pass
    
    @abstractmethod
    def retrieve_similar_entries_with_scores(self, query: str, k: int = 3,
                                           filter_criteria: Optional[Dict[str, Any]] = None) -> List[Tuple[SearchResult, float]]:
        """Retrieve similar entries with explicit similarity scores.
        
        Args:
            query: Query string
            k: Number of results to return
            filter_criteria: Optional metadata filters
            
        Returns:
            List of tuples (search_result, similarity_score)
        """
        pass
    
    @abstractmethod
    def delete_entry(self, document_id: str) -> bool:
        """Delete a reasoning entry.
        
        Args:
            document_id: ID of entry to delete
            
        Returns:
            True if deletion was successful
        """
        pass
    
    @abstractmethod
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics.
        
        Returns:
            Dictionary with collection statistics
        """
        pass
    
    @abstractmethod
    def store_reasoning(self, content: str, metadata: Dict[str, Any]) -> str:
        """Store reasoning text with metadata in RAG vector store.
        
        Args:
            content: The reasoning content to store
            metadata: Metadata dict with required fields: bug_id, test_name, iteration, 
                     category, timestamp, tags, source
                     
        Returns:
            Document ID of the stored reasoning entry
        """
        pass
    
    @abstractmethod
    def search_reasoning(self, query: str, limit: int = 5, 
                        filter: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for reasoning entries based on query.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            filter: Optional metadata filters
            
        Returns:
            List of search results with reasoning entries
        """
        pass
    
    @abstractmethod
    def delete_reasoning_by_bug_id(self, bug_id: str) -> int:
        """Delete all reasoning entries for a specific bug ID.
        
        Args:
            bug_id: Bug ID to delete reasoning entries for
            
        Returns:
            Number of deleted entries
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close connections and cleanup resources."""
        pass