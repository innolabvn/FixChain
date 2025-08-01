"""Test runner for FixChain test execution."""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import TestCase, TestResult, TestStatus, TestAttempt


class TestRunner:
    """Manages execution of multiple test cases with iteration tracking."""
    
    def __init__(self, 
                 logger: Optional[logging.Logger] = None,
                 max_workers: int = 1,
                 stop_on_first_success: bool = True):
        """
        Initialize TestRunner.
        
        Args:
            logger: Logger instance for test execution logging
            max_workers: Maximum number of concurrent test workers
            stop_on_first_success: Whether to stop iterations on first success
        """
        self.logger = logger or logging.getLogger(__name__)
        self.max_workers = max_workers
        self.stop_on_first_success = stop_on_first_success
        self._test_cases: List[TestCase] = []
        self._execution_history: List[Dict[str, Any]] = []
    
    def add_test(self, test_case: TestCase) -> None:
        """Add a test case to the runner.
        
        Args:
            test_case: TestCase instance to add
        """
        self._test_cases.append(test_case)
        self.logger.info(f"Added test case: {test_case.name} ({test_case.category.value})")
    
    def add_tests(self, test_cases: List[TestCase]) -> None:
        """Add multiple test cases to the runner.
        
        Args:
            test_cases: List of TestCase instances to add
        """
        for test_case in test_cases:
            self.add_test(test_case)
    
    def run_test(self, test_case: TestCase, **kwargs) -> TestResult:
        """Run a single test case with multiple iterations if needed.
        
        Args:
            test_case: TestCase to execute
            **kwargs: Additional parameters for test execution
            
        Returns:
            TestResult: Complete test results
        """
        self.logger.info(f"Starting test execution: {test_case.name}")
        start_time = datetime.now()
        
        # Reset test case for fresh run
        test_case.reset()
        
        try:
            while test_case.result.has_remaining_iterations:
                iteration = test_case.result.current_iteration + 1
                self.logger.info(f"Executing iteration {iteration}/{test_case.max_iterations} for {test_case.name}")
                
                attempt = test_case.execute_iteration(**kwargs)
                
                self.logger.info(
                    f"Iteration {iteration} completed: {attempt.status.value} "
                    f"(result: {attempt.result}, duration: {attempt.duration:.2f}s)"
                )
                
                # Stop on first success if configured
                if self.stop_on_first_success and attempt.result is True:
                    self.logger.info(f"Test {test_case.name} passed on iteration {iteration}, stopping")
                    break
                
                # Stop if test failed and no more iterations
                if attempt.result is False and not test_case.result.has_remaining_iterations:
                    self.logger.warning(f"Test {test_case.name} failed after {iteration} iterations")
                    break
        
        except Exception as e:
            self.logger.error(f"Error during test execution for {test_case.name}: {str(e)}")
            test_case.result.final_status = TestStatus.ERROR
            test_case.result.final_result = False
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Log execution summary
        self._log_test_summary(test_case, duration)
        
        # Record execution history
        self._record_execution(test_case, start_time, end_time, duration)
        
        return test_case.result
    
    def run_all_tests(self, **kwargs) -> Dict[str, TestResult]:
        """Run all registered test cases.
        
        Args:
            **kwargs: Additional parameters for test execution
            
        Returns:
            Dict[str, TestResult]: Mapping of test names to results
        """
        if not self._test_cases:
            self.logger.warning("No test cases registered")
            return {}
        
        self.logger.info(f"Starting execution of {len(self._test_cases)} test cases")
        results = {}
        
        if self.max_workers == 1:
            # Sequential execution
            for test_case in self._test_cases:
                results[test_case.name] = self.run_test(test_case, **kwargs)
        else:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_test = {
                    executor.submit(self.run_test, test_case, **kwargs): test_case
                    for test_case in self._test_cases
                }
                
                for future in as_completed(future_to_test):
                    test_case = future_to_test[future]
                    try:
                        result = future.result()
                        results[test_case.name] = result
                    except Exception as e:
                        self.logger.error(f"Error in parallel execution for {test_case.name}: {str(e)}")
                        results[test_case.name] = test_case.result
        
        self._log_execution_summary(results)
        return results
    
    def run_tests_by_category(self, category: str, **kwargs) -> Dict[str, TestResult]:
        """Run tests filtered by category.
        
        Args:
            category: Test category to filter by
            **kwargs: Additional parameters for test execution
            
        Returns:
            Dict[str, TestResult]: Mapping of test names to results
        """
        filtered_tests = [tc for tc in self._test_cases if tc.category.value == category]
        
        if not filtered_tests:
            self.logger.warning(f"No test cases found for category: {category}")
            return {}
        
        self.logger.info(f"Running {len(filtered_tests)} tests for category: {category}")
        
        # Temporarily replace test cases
        original_tests = self._test_cases
        self._test_cases = filtered_tests
        
        try:
            results = self.run_all_tests(**kwargs)
        finally:
            self._test_cases = original_tests
        
        return results
    
    def get_test_by_name(self, name: str) -> Optional[TestCase]:
        """Get test case by name.
        
        Args:
            name: Test case name
            
        Returns:
            TestCase or None if not found
        """
        for test_case in self._test_cases:
            if test_case.name == name:
                return test_case
        return None
    
    def remove_test(self, name: str) -> bool:
        """Remove test case by name.
        
        Args:
            name: Test case name to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        for i, test_case in enumerate(self._test_cases):
            if test_case.name == name:
                removed = self._test_cases.pop(i)
                self.logger.info(f"Removed test case: {removed.name}")
                return True
        return False
    
    def clear_tests(self) -> None:
        """Clear all registered test cases."""
        count = len(self._test_cases)
        self._test_cases.clear()
        self.logger.info(f"Cleared {count} test cases")
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history.
        
        Returns:
            List of execution records
        """
        return self._execution_history.copy()
    
    def clear_history(self) -> None:
        """Clear execution history."""
        self._execution_history.clear()
        self.logger.info("Cleared execution history")
    
    def _log_test_summary(self, test_case: TestCase, duration: float) -> None:
        """Log summary for a single test execution."""
        result = test_case.result
        self.logger.info(
            f"Test {test_case.name} completed: {result.final_status.value} "
            f"({result.current_iteration} iterations, {duration:.2f}s total, "
            f"success rate: {result.success_rate:.1%})"
        )
    
    def _log_execution_summary(self, results: Dict[str, TestResult]) -> None:
        """Log summary for all test executions."""
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.final_result is True)
        failed_tests = sum(1 for r in results.values() if r.final_result is False)
        error_tests = sum(1 for r in results.values() if r.final_status == TestStatus.ERROR)
        
        self.logger.info(
            f"Test execution completed: {total_tests} total, "
            f"{passed_tests} passed, {failed_tests} failed, {error_tests} errors"
        )
    
    def _record_execution(self, test_case: TestCase, start_time: datetime, 
                         end_time: datetime, duration: float) -> None:
        """Record test execution in history."""
        record = {
            "test_name": test_case.name,
            "category": test_case.category.value,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "iterations": test_case.result.current_iteration,
            "final_status": test_case.result.final_status.value,
            "final_result": test_case.result.final_result,
            "success_rate": test_case.result.success_rate
        }
        self._execution_history.append(record)
    
    @property
    def test_count(self) -> int:
        """Get number of registered test cases."""
        return len(self._test_cases)
    
    @property
    def test_names(self) -> List[str]:
        """Get list of registered test names."""
        return [tc.name for tc in self._test_cases]
    
    def __str__(self) -> str:
        return f"TestRunner(tests={self.test_count}, max_workers={self.max_workers})"
    
    def __repr__(self) -> str:
        return self.__str__()