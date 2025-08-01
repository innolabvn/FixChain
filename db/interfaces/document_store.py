"""Abstract interface for document storage.

This module defines the DocumentStore interface that provides
basic CRUD operations for document-based storage systems.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime


class DocumentStore(ABC):
    """Abstract interface for document storage operations.
    
    This interface defines the contract for storing and retrieving
    documents in a document-based database system.
    """
    
    @abstractmethod
    async def save_document(self, collection: str, document: Dict[str, Any]) -> str:
        """Save a document to the specified collection.
        
        Args:
            collection: Name of the collection to save to
            document: Document data to save
            
        Returns:
            Document ID of the saved document
            
        Raises:
            DatabaseError: If save operation fails
        """
        pass
    
    @abstractmethod
    async def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID.
        
        Args:
            collection: Name of the collection
            doc_id: Document ID to retrieve
            
        Returns:
            Document data if found, None otherwise
            
        Raises:
            DatabaseError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def update_document(self, collection: str, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Update a document by ID.
        
        Args:
            collection: Name of the collection
            doc_id: Document ID to update
            updates: Fields to update
            
        Returns:
            True if document was updated, False if not found
            
        Raises:
            DatabaseError: If update operation fails
        """
        pass
    
    @abstractmethod
    async def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete a document by ID.
        
        Args:
            collection: Name of the collection
            doc_id: Document ID to delete
            
        Returns:
            True if document was deleted, False if not found
            
        Raises:
            DatabaseError: If delete operation fails
        """
        pass
    
    @abstractmethod
    async def find_documents(
        self, 
        collection: str, 
        query: Dict[str, Any], 
        limit: Optional[int] = None,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """Find documents matching a query.
        
        Args:
            collection: Name of the collection
            query: MongoDB-style query filter
            limit: Maximum number of documents to return
            sort: Sort specification as list of (field, direction) tuples
            
        Returns:
            List of matching documents
            
        Raises:
            DatabaseError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def count_documents(self, collection: str, query: Dict[str, Any]) -> int:
        """Count documents matching a query.
        
        Args:
            collection: Name of the collection
            query: MongoDB-style query filter
            
        Returns:
            Number of matching documents
            
        Raises:
            DatabaseError: If count operation fails
        """
        pass
    
    @abstractmethod
    async def create_index(self, collection: str, index_spec: Dict[str, Any]) -> str:
        """Create an index on the collection.
        
        Args:
            collection: Name of the collection
            index_spec: Index specification
            
        Returns:
            Index name
            
        Raises:
            DatabaseError: If index creation fails
        """
        pass
    
    @abstractmethod
    async def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get statistics for a collection.
        
        Args:
            collection: Name of the collection
            
        Returns:
            Collection statistics
            
        Raises:
            DatabaseError: If stats retrieval fails
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the database connection.
        
        Raises:
            DatabaseError: If close operation fails
        """
        pass