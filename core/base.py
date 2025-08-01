"""Base classes and models for FixChain test system."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class TestCategory(str, Enum):
    """Test category types."""
    STATIC = "static"
    DYNAMIC = "dynamic"
    SIMULATION = "simulation"


class TestAttempt(BaseModel):
    """Model for a single test attempt."""
    iteration: int = Field(description="Iteration number (1-based)")
    start_time: datetime = Field(description="Test start timestamp")
    end_time: Optional[datetime] = Field(default=None, description="Test end timestamp")
    status: TestStatus = Field(default=TestStatus.PENDING, description="Test status")
    result: Optional[bool] = Field(default=None, description="Test result (True=pass, False=fail)")
    output: str = Field(default="", description="Test output/logs")
    message: str = Field(default="", description="Status message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate test duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class TestResult(BaseModel):
    """Model for complete test results across all attempts."""
    test_name: str = Field(description="Test name")
    test_category: TestCategory = Field(description="Test category")
    max_iterations: int = Field(default=5, description="Maximum allowed iterations")
    attempts: List[TestAttempt] = Field(default_factory=list, description="List of test attempts")
    final_status: TestStatus = Field(default=TestStatus.PENDING, description="Final test status")
    final_result: Optional[bool] = Field(default=None, description="Final test result")
    created_at: datetime = Field(default_factory=datetime.now, description="Test creation timestamp")
    
    @property
    def current_iteration(self) -> int:
        """Get current iteration number."""
        return len(self.attempts)
    
    @property
    def has_remaining_iterations(self) -> bool:
        """Check if more iterations are allowed."""
        return self.current_iteration < self.max_iterations
    
    @property
    def last_attempt(self) -> Optional[TestAttempt]:
        """Get the last test attempt."""
        return self.attempts[-1] if self.attempts else None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate across all attempts."""
        if not self.attempts:
            return 0.0
        passed_attempts = sum(1 for attempt in self.attempts if attempt.result is True)
        return passed_attempts / len(self.attempts)


class TestCase(ABC):
    """Abstract base class for all test cases."""
    
    def __init__(self, name: str, description: str, category: TestCategory, max_iterations: int = 5):
        self.name = name
        self.description = description
        self.category = category
        self.max_iterations = max_iterations
        self._result = TestResult(
            test_name=name,
            test_category=category,
            max_iterations=max_iterations
        )
    
    @property
    def result(self) -> TestResult:
        """Get test result."""
        return self._result
    
    @abstractmethod
    def run(self, **kwargs) -> TestAttempt:
        """Execute the test logic.
        
        Args:
            **kwargs: Additional parameters for test execution
            
        Returns:
            TestAttempt: The test attempt result
        """
        pass
    
    @abstractmethod
    def validate(self, attempt: TestAttempt) -> bool:
        """Validate test results.
        
        Args:
            attempt: The test attempt to validate
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        pass
    
    def execute_iteration(self, **kwargs) -> TestAttempt:
        """Execute a single test iteration.
        
        Args:
            **kwargs: Additional parameters for test execution
            
        Returns:
            TestAttempt: The completed test attempt
        """
        if not self._result.has_remaining_iterations:
            raise RuntimeError(f"Maximum iterations ({self.max_iterations}) reached for test {self.name}")
        
        iteration = self._result.current_iteration + 1
        attempt = TestAttempt(
            iteration=iteration,
            start_time=datetime.now()
        )
        
        try:
            attempt.status = TestStatus.RUNNING
            # Execute the test
            executed_attempt = self.run(**kwargs)
            
            # Update attempt with execution results
            attempt.end_time = executed_attempt.end_time or datetime.now()
            attempt.output = executed_attempt.output
            attempt.message = executed_attempt.message
            attempt.metadata = executed_attempt.metadata
            
            # Validate results
            attempt.result = self.validate(executed_attempt)
            attempt.status = TestStatus.PASSED if attempt.result else TestStatus.FAILED
            
        except Exception as e:
            attempt.end_time = datetime.now()
            attempt.status = TestStatus.ERROR
            attempt.result = False
            attempt.message = f"Test execution error: {str(e)}"
            attempt.output = str(e)
        
        # Add attempt to results
        self._result.attempts.append(attempt)
        
        # Update final status
        if attempt.result is True:
            self._result.final_status = TestStatus.PASSED
            self._result.final_result = True
        elif not self._result.has_remaining_iterations:
            self._result.final_status = TestStatus.FAILED
            self._result.final_result = False
        
        return attempt
    
    def reset(self):
        """Reset test results for a fresh run."""
        self._result = TestResult(
            test_name=self.name,
            test_category=self.category,
            max_iterations=self.max_iterations
        )
    
    def __str__(self) -> str:
        return f"TestCase(name={self.name}, category={self.category.value})"
    
    def __repr__(self) -> str:
        return self.__str__()