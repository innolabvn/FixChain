"""Abstract interface for bug-specific storage operations.

This module defines the BugStore interface that provides
specialized operations for bug tracking, test results,
and fix reasoning storage.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

from models.test_result import TestExecutionResult, TestIssue


class BugStore(ABC):
    """Abstract interface for bug-specific storage operations.
    
    This interface defines the contract for storing and retrieving
    bug-related data including test results, fixes, and changelogs.
    """
    
    @abstractmethod
    async def save_test_result(self, result: TestExecutionResult) -> str:
        """Save a test execution result.
        
        Args:
            result: Test execution result to save
            
        Returns:
            Test result ID
            
        Raises:
            DatabaseError: If save operation fails
        """
        pass
    
    @abstractmethod
    async def get_test_result(self, test_id: str) -> Optional[TestExecutionResult]:
        """Retrieve a test result by ID.
        
        Args:
            test_id: Test result ID to retrieve
            
        Returns:
            Test execution result if found, None otherwise
            
        Raises:
            DatabaseError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def get_test_results_by_bug(self, bug_id: str) -> List[TestExecutionResult]:
        """Get all test results related to a specific bug.
        
        Args:
            bug_id: Bug ID to search for
            
        Returns:
            List of test execution results
            
        Raises:
            DatabaseError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def log_changelog(
        self, 
        bug_id: str, 
        changes: Dict[str, Any], 
        timestamp: Optional[datetime] = None
    ) -> str:
        """Log changes made to fix a bug.
        
        Args:
            bug_id: Bug ID being fixed
            changes: Dictionary of changes made
            timestamp: When changes were made (defaults to now)
            
        Returns:
            Changelog entry ID
            
        Raises:
            DatabaseError: If logging operation fails
        """
        pass
    
    @abstractmethod
    async def get_changelog(self, bug_id: str) -> List[Dict[str, Any]]:
        """Get changelog entries for a bug.
        
        Args:
            bug_id: Bug ID to get changelog for
            
        Returns:
            List of changelog entries sorted by timestamp
            
        Raises:
            DatabaseError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def save_fix_result(
        self, 
        bug_id: str, 
        patch: str, 
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save the result of applying a fix.
        
        Args:
            bug_id: Bug ID being fixed
            patch: The patch/fix that was applied
            status: Status of the fix (applied, failed, pending, etc.)
            metadata: Additional metadata about the fix
            
        Returns:
            Fix result ID
            
        Raises:
            DatabaseError: If save operation fails
        """
        pass
    
    @abstractmethod
    async def get_fix_result(self, bug_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest fix result for a bug.
        
        Args:
            bug_id: Bug ID to get fix result for
            
        Returns:
            Fix result data if found, None otherwise
            
        Raises:
            DatabaseError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def get_bug_list(
        self, 
        test_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[TestIssue]:
        """Get list of bugs/issues.
        
        Args:
            test_id: Filter by specific test ID
            status: Filter by bug status
            limit: Maximum number of bugs to return
            
        Returns:
            List of test issues/bugs
            
        Raises:
            DatabaseError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def get_bug_by_id(self, bug_id: str) -> Optional[TestIssue]:
        """Get a specific bug by ID.
        
        Args:
            bug_id: Bug ID to retrieve
            
        Returns:
            Test issue if found, None otherwise
            
        Raises:
            DatabaseError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def update_bug_status(self, bug_id: str, status: str) -> bool:
        """Update the status of a bug.
        
        Args:
            bug_id: Bug ID to update
            status: New status for the bug
            
        Returns:
            True if bug was updated, False if not found
            
        Raises:
            DatabaseError: If update operation fails
        """
        pass
    
    @abstractmethod
    async def get_bug_statistics(self) -> Dict[str, Any]:
        """Get statistics about bugs in the system.
        
        Returns:
            Dictionary containing bug statistics
            
        Raises:
            DatabaseError: If query operation fails
        """
        pass