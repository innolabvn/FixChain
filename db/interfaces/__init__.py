"""Database interfaces for FixChain system.

This module defines abstract interfaces for different types of data storage:
- DocumentStore: General document storage interface
- BugStore: Bug-specific storage interface
"""

from .document_store import DocumentStore
from .bug_store import BugStore

__all__ = [
    "DocumentStore",
    "BugStore"
]