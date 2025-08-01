"""Test executor for FixChain test suite.

This module provides the main test execution engine that orchestrates
test case execution, manages iterations, and handles result storage.
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Type
from pathlib import Path

from testsuite.interfaces.test_case import ITestCase, TestResult
from testsuite.static_tests.syntax_check import SyntaxCheckTest
from testsuite.static_tests.type_check import TypeCheckTest
from testsuite.static_tests.security_check import SecurityCheckTest
from db.mongo.fixchain_db import FixChainDB
from rag.stores import FixChainRAGStore
from models.test_result import TestExecutionResult, TestAttemptResult, TestStatus, TestCategory


class TestExecutor:
    """Main test execution engine for FixChain.
    
    This class orchestrates the execution of various test cases,
    manages iterations, and handles result storage to both
    document and vector stores.
    """
    
    def __init__(
        self,
        db: Optional[FixChainDB] = None,
        rag_store: Optional[FixChainRAGStore] = None
    ):
        """Initialize test executor.
        
        Args:
            db: FixChain database instance
            rag_store: FixChain RAG store instance
        """
        self.db = db or FixChainDB()
        self.rag_store = rag_store or FixChainRAGStore()
        
        # Registry of available test cases
        self.test_registry: Dict[str, Type[ITestCase]] = {
            'syntax_check': SyntaxCheckTest,
            'type_check': TypeCheckTest,
            'security_check': SecurityCheckTest,
        }
        
        # Test categories mapping
        self.test_categories = {
            'syntax_check': TestCategory.STATIC,
            'type_check': TestCategory.STATIC,
            'security_check': TestCategory.STATIC,
        }
    
    async def execute_test(
        self,
        test_name: str,
        source_file: str,
        max_iterations: int = 5,
        **kwargs
    ) -> TestExecutionResult:
        """Execute a single test case with iteration support.
        
        Args:
            test_name: Name of the test to execute
            source_file: Path to the source file to test
            max_iterations: Maximum number of iterations
            **kwargs: Additional test-specific parameters
            
        Returns:
            TestExecutionResult: Complete test execution result
            
        Raises:
            ValueError: If test_name is not registered
            FileNotFoundError: If source_file doesn't exist
        """
        if test_name not in self.test_registry:
            raise ValueError(f"Unknown test: {test_name}. Available tests: {list(self.test_registry.keys())}")
        
        if not Path(source_file).exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
        # Create test instance
        test_class = self.test_registry[test_name]
        test_instance = test_class(max_iterations=max_iterations)
        
        # Generate execution ID
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        attempts = []
        final_status = TestStatus.PENDING
        final_result = None
        
        try:
            # Execute test iterations
            for iteration in range(max_iterations):
                if not test_instance.can_run_iteration():
                    break
                
                attempt_id = f"{execution_id}_{iteration + 1}"
                attempt_start = datetime.utcnow()
                
                try:
                    # Run test iteration
                    result = await test_instance.run(
                        source_file=source_file,
                        attempt_id=attempt_id,
                        **kwargs
                    )
                    
                    # Create attempt result
                    attempt_result = TestAttemptResult(
                        iteration=iteration + 1,
                        start_time=attempt_start,
                        end_time=datetime.utcnow(),
                        status=TestStatus.PASSED if result.status == "pass" else TestStatus.FAILED,
                        result=result.status == "pass",
                        output=result.output,
                        message=result.summary,
                        issues=[],  # Will be populated from result if needed
                        metadata=result.metadata or {}
                    )
                    
                    attempts.append(attempt_result)
                    
                    # Store reasoning in vector store
                    await self._store_reasoning(
                        test_name=test_name,
                        attempt_id=attempt_id,
                        result=result,
                        source_file=source_file
                    )
                    
                    # Update test instance iteration
                    test_instance.increment_iteration()
                    
                    # Check if test passed
                    if result.status == "pass":
                        final_status = TestStatus.PASSED
                        final_result = result
                        break
                    else:
                        final_status = TestStatus.FAILED
                        final_result = result
                
                except Exception as e:
                    # Handle iteration error
                    attempt_result = TestAttemptResult(
                        iteration=iteration + 1,
                        start_time=attempt_start,
                        end_time=datetime.utcnow(),
                        status=TestStatus.ERROR,
                        result=False,
                        output=f"Error: {str(e)}",
                        message=f"Test iteration failed: {str(e)}",
                        issues=[],
                        metadata={"error": str(e)}
                    )
                    
                    attempts.append(attempt_result)
                    final_status = TestStatus.ERROR
                    test_instance.increment_iteration()
            
            # If no iterations passed, use the last result
            if final_status != TestStatus.PASSED and attempts:
                final_status = attempts[-1].status
        
        except Exception as e:
            # Handle execution error
            final_status = TestStatus.ERROR
            if not attempts:
                attempt_result = TestAttemptResult(
                    iteration=1,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    status=TestStatus.ERROR,
                    result=False,
                    output=f"Execution error: {str(e)}",
                    message=f"Test execution failed: {str(e)}",
                    issues=[],
                    metadata={"error": str(e)}
                )
                attempts.append(attempt_result)
        
        # Create execution result
        execution_result = TestExecutionResult(
            test_name=test_name,
            test_category=self.test_categories.get(test_name, TestCategory.STATIC),
            source_file=source_file,
            max_iterations=max_iterations,
            attempts=attempts,
            final_status=final_status,
            final_result=final_result.status == "pass" if final_result else False,
            created_at=start_time,
            completed_at=datetime.utcnow()
        )
        
        # Save to document store
        await self._save_test_result(execution_result)
        
        return execution_result
    
    async def execute_test_suite(
        self,
        test_names: List[str],
        source_file: str,
        max_iterations: int = 5,
        **kwargs
    ) -> Dict[str, TestExecutionResult]:
        """Execute multiple tests as a suite.
        
        Args:
            test_names: List of test names to execute
            source_file: Path to the source file to test
            max_iterations: Maximum number of iterations per test
            **kwargs: Additional test-specific parameters
            
        Returns:
            Dict[str, TestExecutionResult]: Results for each test
        """
        results = {}
        
        for test_name in test_names:
            try:
                result = await self.execute_test(
                    test_name=test_name,
                    source_file=source_file,
                    max_iterations=max_iterations,
                    **kwargs
                )
                results[test_name] = result
            except Exception as e:
                # Create error result for failed test
                execution_id = str(uuid.uuid4())
                error_result = TestExecutionResult(
                    test_name=test_name,
                    test_category=self.test_categories.get(test_name, TestCategory.STATIC),
                    source_file=source_file,
                    attempts=[],
                    final_status=TestStatus.ERROR,
                    final_result=False,
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )
                results[test_name] = error_result
        
        return results
    
    async def execute_static_tests(
        self,
        source_file: str,
        max_iterations: int = 5,
        **kwargs
    ) -> Dict[str, TestExecutionResult]:
        """Execute all static tests.
        
        Args:
            source_file: Path to the source file to test
            max_iterations: Maximum number of iterations per test
            **kwargs: Additional test-specific parameters
            
        Returns:
            Dict[str, TestExecutionResult]: Results for each static test
        """
        static_tests = [
            'syntax_check',
            'type_check',
            'security_check'
        ]
        
        return await self.execute_test_suite(
            test_names=static_tests,
            source_file=source_file,
            max_iterations=max_iterations,
            **kwargs
        )
    
    async def _save_test_result(self, execution_result: TestExecutionResult) -> None:
        """Save test result to document store.
        
        Args:
            execution_result: Test execution result to save
        """
        try:
            await self.db.save_test_result(execution_result.dict())
        except Exception as e:
            # Log error but don't fail the test execution
            print(f"Warning: Failed to save test result to database: {e}")
    
    async def _store_reasoning(
        self,
        test_name: str,
        attempt_id: str,
        result: TestResult,
        source_file: str
    ) -> None:
        """Store test reasoning in vector store.
        
        Args:
            test_name: Name of the test
            attempt_id: Attempt identifier
            result: Test result
            source_file: Source file path
        """
        try:
            # Create reasoning document
            reasoning_doc = {
                "test_name": test_name,
                "attempt_id": attempt_id,
                "source_file": source_file,
                "prompt": f"Execute {test_name} on {source_file}",
                "steps": [
                    f"1. Initialize {test_name} test case",
                    f"2. Analyze source file: {source_file}",
                    f"3. Execute test logic",
                    f"4. Generate test result with {len(result.issues)} issues"
                ],
                "output": result.output,
                "thinking": f"Test {test_name} analysis of {source_file}: {result.summary}",
                "metadata": {
                    "test_type": result.test_type,
                    "status": result.status,
                    "tool": result.tool,
                    "issues_count": len(result.issues),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            await self.rag_store.store_reasoning(reasoning_doc)
        except Exception as e:
            # Log error but don't fail the test execution
            print(f"Warning: Failed to store reasoning in vector store: {e}")
    
    def register_test(self, test_name: str, test_class: Type[ITestCase], category: TestCategory) -> None:
        """Register a new test case.
        
        Args:
            test_name: Name of the test
            test_class: Test case class
            category: Test category
        """
        self.test_registry[test_name] = test_class
        self.test_categories[test_name] = category
    
    def get_available_tests(self) -> List[str]:
        """Get list of available test names.
        
        Returns:
            List[str]: Available test names
        """
        return list(self.test_registry.keys())
    
    def get_test_info(self, test_name: str) -> Dict[str, Any]:
        """Get information about a specific test.
        
        Args:
            test_name: Name of the test
            
        Returns:
            Dict[str, Any]: Test information
            
        Raises:
            ValueError: If test_name is not registered
        """
        if test_name not in self.test_registry:
            raise ValueError(f"Unknown test: {test_name}")
        
        test_class = self.test_registry[test_name]
        test_instance = test_class()
        
        return {
            "name": test_instance.name,
            "test_type": test_instance.test_type,
            "category": self.test_categories[test_name].value,
            "max_iterations": test_instance.max_iterations,
            "tool": test_instance.get_tool_name()
        }


# Convenience functions for common operations
async def run_syntax_check(source_file: str, max_iterations: int = 5) -> TestExecutionResult:
    """Run syntax check on a source file.
    
    Args:
        source_file: Path to the source file
        max_iterations: Maximum iterations
        
    Returns:
        TestExecutionResult: Test result
    """
    executor = TestExecutor()
    return await executor.execute_test('syntax_check', source_file, max_iterations)


async def run_type_check(source_file: str, max_iterations: int = 5, **kwargs) -> TestExecutionResult:
    """Run type check on a source file.
    
    Args:
        source_file: Path to the source file
        max_iterations: Maximum iterations
        **kwargs: Additional type check parameters
        
    Returns:
        TestExecutionResult: Test result
    """
    executor = TestExecutor()
    return await executor.execute_test('type_check', source_file, max_iterations, **kwargs)


async def run_security_check(source_file: str, max_iterations: int = 5, **kwargs) -> TestExecutionResult:
    """Run security check on a source file.
    
    Args:
        source_file: Path to the source file
        max_iterations: Maximum iterations
        **kwargs: Additional security check parameters
        
    Returns:
        TestExecutionResult: Test result
    """
    executor = TestExecutor()
    return await executor.execute_test('security_check', source_file, max_iterations, **kwargs)


async def run_all_static_tests(source_file: str, max_iterations: int = 5, **kwargs) -> Dict[str, TestExecutionResult]:
    """Run all static tests on a source file.
    
    Args:
        source_file: Path to the source file
        max_iterations: Maximum iterations per test
        **kwargs: Additional test parameters
        
    Returns:
        Dict[str, TestExecutionResult]: Results for all static tests
    """
    executor = TestExecutor()
    return await executor.execute_static_tests(source_file, max_iterations, **kwargs)