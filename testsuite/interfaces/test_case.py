"""Abstract interface for FixChain test cases.

This module defines the ITestCase interface that all test implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from models.test_result import TestIssue


class TestResult:
    """Test execution result structure."""
    
    def __init__(
        self,
        test_name: str,
        test_type: str,
        issues: List[TestIssue],
        summary: str,
        status: str,
        tool: str,
        output: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.test_name = test_name
        self.test_type = test_type
        self.issues = issues
        self.summary = summary
        self.status = status  # 'pass' or 'fail'
        self.tool = tool
        self.output = output
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'test_name': self.test_name,
            'test_type': self.test_type,
            'issues': [issue.dict() for issue in self.issues],
            'summary': self.summary,
            'status': self.status,
            'tool': self.tool,
            'output': self.output,
            'metadata': self.metadata
        }


class ITestCase(ABC):
    """Abstract interface for all test cases.
    
    This interface defines the contract that all test implementations must follow.
    Each test case should implement the run() method to execute the test logic.
    """
    
    def __init__(self, name: str, test_type: str, max_iterations: int = 5):
        """Initialize test case.
        
        Args:
            name: Test case name
            test_type: Type of test (static, dynamic, simulation)
            max_iterations: Maximum number of iterations allowed
        """
        self.name = name
        self.test_type = test_type
        self.max_iterations = max_iterations
        self.current_iteration = 0
    
    @abstractmethod
    async def run(
        self,
        source_file: str,
        attempt_id: str,
        **kwargs
    ) -> TestResult:
        """Execute the test case.
        
        Args:
            source_file: Path to the source file to test
            attempt_id: Unique identifier for this test attempt
            **kwargs: Additional test-specific parameters
            
        Returns:
            TestResult: The test execution result containing:
                - test_name: str
                - test_type: str
                - issues: List[TestIssue]
                - summary: str
                - status: 'pass' | 'fail'
                - tool: str
                - output: str
        """
        pass
    
    @abstractmethod
    def get_tool_name(self) -> str:
        """Get the name of the tool used by this test case.
        
        Returns:
            str: Tool name (e.g., 'pylint', 'mypy', 'bandit')
        """
        pass
    
    def can_run_iteration(self) -> bool:
        """Check if another iteration can be run.
        
        Returns:
            bool: True if more iterations are allowed
        """
        return self.current_iteration < self.max_iterations
    
    def increment_iteration(self) -> None:
        """Increment the current iteration counter."""
        self.current_iteration += 1
    
    def reset_iterations(self) -> None:
        """Reset iteration counter."""
        self.current_iteration = 0