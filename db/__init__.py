"""Database components for FixChain system.

This module provides database interfaces and implementations for:
- Document storage (MongoDB)
- Vector storage (RAG)
- Bug tracking and reasoning storage
"""

from .interfaces.document_store import DocumentStore
from .interfaces.bug_store import BugStore
from .mongo.fixchain_db import FixChainDB
from .mongo.exceptions import (
    DatabaseError,
    ConnectionError,
    ValidationError,
    DocumentNotFoundError,
    DuplicateKeyError,
    QueryError
)

__all__ = [
    "DocumentStore",
    "BugStore", 
    "FixChainDB",
    "DatabaseError",
    "ConnectionError",
    "ValidationError",
    "DocumentNotFoundError",
    "DuplicateKeyError",
    "QueryError"
]