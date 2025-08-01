"""Custom exceptions for MongoDB database operations.

This module defines specific exceptions that can be raised
during database operations to provide better error handling
and debugging information.
"""

from typing import Any, Dict, Optional


class DatabaseError(Exception):
    """Base exception for database operations.
    
    This is the base class for all database-related exceptions.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize database error.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """String representation of the error."""
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ConnectionError(DatabaseError):
    """Exception raised when database connection fails.
    
    This exception is raised when the application cannot
    establish or maintain a connection to the database.
    """
    
    def __init__(self, message: str = "Database connection failed", details: Optional[Dict[str, Any]] = None):
        """Initialize connection error.
        
        Args:
            message: Error message
            details: Additional connection details
        """
        super().__init__(message, details)


class ValidationError(DatabaseError):
    """Exception raised when data validation fails.
    
    This exception is raised when data doesn't meet the
    required schema or validation rules.
    """
    
    def __init__(self, message: str = "Data validation failed", details: Optional[Dict[str, Any]] = None):
        """Initialize validation error.
        
        Args:
            message: Error message
            details: Validation error details
        """
        super().__init__(message, details)


class DocumentNotFoundError(DatabaseError):
    """Exception raised when a requested document is not found.
    
    This exception is raised when trying to retrieve, update,
    or delete a document that doesn't exist.
    """
    
    def __init__(self, doc_id: str, collection: str):
        """Initialize document not found error.
        
        Args:
            doc_id: ID of the document that was not found
            collection: Collection where the document was searched
        """
        message = f"Document '{doc_id}' not found in collection '{collection}'"
        details = {"doc_id": doc_id, "collection": collection}
        super().__init__(message, details)


class DuplicateKeyError(DatabaseError):
    """Exception raised when trying to insert a document with duplicate key.
    
    This exception is raised when a unique constraint is violated.
    """
    
    def __init__(self, key: str, value: Any, collection: str):
        """Initialize duplicate key error.
        
        Args:
            key: The key that caused the duplication
            value: The value that was duplicated
            collection: Collection where duplication occurred
        """
        message = f"Duplicate key '{key}' with value '{value}' in collection '{collection}'"
        details = {"key": key, "value": value, "collection": collection}
        super().__init__(message, details)


class QueryError(DatabaseError):
    """Exception raised when a database query fails.
    
    This exception is raised when a query operation fails
    due to syntax errors, invalid parameters, or other issues.
    """
    
    def __init__(self, query: Dict[str, Any], collection: str, original_error: Optional[Exception] = None):
        """Initialize query error.
        
        Args:
            query: The query that failed
            collection: Collection where query was executed
            original_error: The original exception that caused this error
        """
        message = f"Query failed in collection '{collection}'"
        details = {
            "query": query,
            "collection": collection,
            "original_error": str(original_error) if original_error else None
        }
        super().__init__(message, details)
        self.original_error = original_error