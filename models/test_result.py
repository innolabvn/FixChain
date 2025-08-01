"""Pydantic models for FixChain test results.

This module contains Pydantic schemas for test execution results,
complementing the core test system with structured data models.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, validator


class TestStatus(str, Enum):
    """Test execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class TestCategory(str, Enum):
    """Test category enumeration."""
    STATIC = "static"
    DYNAMIC = "dynamic"
    SIMULATION = "simulation"


class TestSeverity(str, Enum):
    """Test issue severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TestIssue(BaseModel):
    """Model for individual test issues (errors, warnings, etc.)."""
    file: str = Field(description="File path where issue was found")
    line: int = Field(default=0, description="Line number (0 if not applicable)")
    column: int = Field(default=0, description="Column number (0 if not applicable)")
    message: str = Field(description="Issue description")
    severity: TestSeverity = Field(default=TestSeverity.MEDIUM, description="Issue severity")
    rule_id: Optional[str] = Field(default=None, description="Rule or check ID that triggered this issue")
    tool: Optional[str] = Field(default=None, description="Tool that detected this issue")
    error_code: Optional[str] = Field(default=None, description="Error code from the tool")
    suggestion: Optional[str] = Field(default=None, description="Suggested fix for the issue")
    
    @validator('line', 'column')
    def validate_position(cls, v):
        """Ensure line and column numbers are non-negative."""
        return max(0, v)


class TestAttemptResult(BaseModel):
    """Model for a single test attempt result."""
    iteration: int = Field(description="Iteration number (1-based)")
    start_time: datetime = Field(description="Test start timestamp")
    end_time: Optional[datetime] = Field(default=None, description="Test end timestamp")
    status: TestStatus = Field(default=TestStatus.PENDING, description="Test status")
    result: Optional[bool] = Field(default=None, description="Test result (True=pass, False=fail)")
    output: str = Field(default="", description="Test output/logs")
    message: str = Field(default="", description="Status message")
    issues: List[TestIssue] = Field(default_factory=list, description="Issues found during test")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate test duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def critical_issues(self) -> List[TestIssue]:
        """Get critical severity issues."""
        return [issue for issue in self.issues if issue.severity == TestSeverity.CRITICAL]
    
    @property
    def high_issues(self) -> List[TestIssue]:
        """Get high severity issues."""
        return [issue for issue in self.issues if issue.severity == TestSeverity.HIGH]
    
    @validator('iteration')
    def validate_iteration(cls, v):
        """Ensure iteration is positive."""
        if v < 1:
            raise ValueError('Iteration must be positive')
        return v


class TestExecutionResult(BaseModel):
    """Model for complete test execution results across all attempts."""
    test_name: str = Field(description="Test name")
    test_category: TestCategory = Field(description="Test category")
    source_file: str = Field(description="Source file path that was tested")
    description: str = Field(default="", description="Test description")
    max_iterations: int = Field(default=5, description="Maximum allowed iterations")
    attempts: List[TestAttemptResult] = Field(default_factory=list, description="List of test attempts")
    final_status: TestStatus = Field(default=TestStatus.PENDING, description="Final test status")
    final_result: Optional[bool] = Field(default=None, description="Final test result")
    created_at: datetime = Field(default_factory=datetime.now, description="Test creation timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Test completion timestamp")
    
    @property
    def current_iteration(self) -> int:
        """Get current iteration number."""
        return len(self.attempts)
    
    @property
    def has_remaining_iterations(self) -> bool:
        """Check if more iterations are allowed."""
        return self.current_iteration < self.max_iterations
    
    @property
    def last_attempt(self) -> Optional[TestAttemptResult]:
        """Get the last test attempt."""
        return self.attempts[-1] if self.attempts else None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate across all attempts."""
        if not self.attempts:
            return 0.0
        passed_attempts = sum(1 for attempt in self.attempts if attempt.result is True)
        return passed_attempts / len(self.attempts)
    
    @property
    def total_duration(self) -> float:
        """Calculate total duration across all attempts."""
        total = 0.0
        for attempt in self.attempts:
            if attempt.duration:
                total += attempt.duration
        return total
    
    @property
    def all_issues(self) -> List[TestIssue]:
        """Get all issues from all attempts."""
        all_issues = []
        for attempt in self.attempts:
            all_issues.extend(attempt.issues)
        return all_issues
    
    @property
    def critical_issues_count(self) -> int:
        """Count critical issues across all attempts."""
        return len([issue for issue in self.all_issues if issue.severity == TestSeverity.CRITICAL])
    
    @property
    def high_issues_count(self) -> int:
        """Count high severity issues across all attempts."""
        return len([issue for issue in self.all_issues if issue.severity == TestSeverity.HIGH])
    
    @validator('max_iterations')
    def validate_max_iterations(cls, v):
        """Ensure max_iterations is positive."""
        if v < 1:
            raise ValueError('max_iterations must be positive')
        return v


class TestSuiteResult(BaseModel):
    """Model for test suite execution results."""
    suite_name: str = Field(description="Test suite name")
    description: str = Field(default="", description="Test suite description")
    test_results: List[TestExecutionResult] = Field(default_factory=list, description="Individual test results")
    start_time: datetime = Field(default_factory=datetime.now, description="Suite start time")
    end_time: Optional[datetime] = Field(default=None, description="Suite end time")
    total_tests: int = Field(default=0, description="Total number of tests")
    passed_tests: int = Field(default=0, description="Number of passed tests")
    failed_tests: int = Field(default=0, description="Number of failed tests")
    error_tests: int = Field(default=0, description="Number of tests with errors")
    skipped_tests: int = Field(default=0, description="Number of skipped tests")
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate suite duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_tests == 0:
            return 0.0
        return self.passed_tests / self.total_tests
    
    @property
    def total_issues(self) -> int:
        """Count total issues across all tests."""
        return sum(len(test.all_issues) for test in self.test_results)
    
    @property
    def critical_issues(self) -> int:
        """Count critical issues across all tests."""
        return sum(test.critical_issues_count for test in self.test_results)
    
    def update_counts(self):
        """Update test count statistics based on test results."""
        self.total_tests = len(self.test_results)
        self.passed_tests = sum(1 for test in self.test_results if test.final_result is True)
        self.failed_tests = sum(1 for test in self.test_results if test.final_result is False)
        self.error_tests = sum(1 for test in self.test_results if test.final_status == TestStatus.ERROR)
        self.skipped_tests = sum(1 for test in self.test_results if test.final_status == TestStatus.SKIPPED)
    
    def get_tests_by_category(self, category: TestCategory) -> List[TestExecutionResult]:
        """Get tests filtered by category."""
        return [test for test in self.test_results if test.test_category == category]
    
    def get_failed_tests(self) -> List[TestExecutionResult]:
        """Get all failed tests."""
        return [test for test in self.test_results if test.final_result is False]
    
    def get_tests_with_critical_issues(self) -> List[TestExecutionResult]:
        """Get tests that have critical issues."""
        return [test for test in self.test_results if test.critical_issues_count > 0]


class TestConfiguration(BaseModel):
    """Model for test configuration settings."""
    max_iterations: int = Field(default=5, description="Default maximum iterations per test")
    stop_on_first_success: bool = Field(default=True, description="Stop iterations on first success")
    parallel_execution: bool = Field(default=False, description="Enable parallel test execution")
    max_workers: int = Field(default=1, description="Maximum number of parallel workers")
    timeout_seconds: Optional[int] = Field(default=None, description="Test timeout in seconds")
    severity_threshold: TestSeverity = Field(default=TestSeverity.MEDIUM, description="Minimum severity to report")
    fail_on_critical: bool = Field(default=True, description="Fail test if critical issues found")
    fail_on_high: bool = Field(default=False, description="Fail test if high severity issues found")
    exclude_patterns: List[str] = Field(default_factory=lambda: ['__pycache__', '.git', '.venv'], description="File patterns to exclude")
    include_patterns: List[str] = Field(default_factory=list, description="File patterns to include")
    
    @validator('max_iterations', 'max_workers')
    def validate_positive(cls, v):
        """Ensure positive values."""
        if v < 1:
            raise ValueError('Value must be positive')
        return v
    
    @validator('timeout_seconds')
    def validate_timeout(cls, v):
        """Ensure timeout is positive if specified."""
        if v is not None and v <= 0:
            raise ValueError('Timeout must be positive')
        return v