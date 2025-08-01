#!/usr/bin/env python3
"""Example usage of FixChain Core Logic System.

This script demonstrates how to use the FixChain test runner
with static analysis tests including SyntaxCheck, TypeCheck,
and CriticalSecurityCheck.
"""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.runner import TestRunner
from core.tests.static.syntax_check import SyntaxCheck
from core.tests.static.type_check import TypeCheck
from core.tests.static.security_check import CriticalSecurityCheck
from core.base import TestCategory


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/fixchain_example.log')
        ]
    )
    return logging.getLogger(__name__)


def create_sample_test_files(project_path: Path):
    """Create sample test files for demonstration."""
    # Create a valid Python file
    valid_file = project_path / "sample_valid.py"
    valid_file.write_text('''
"""Sample valid Python file."""

def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
''')
    
    # Create a file with syntax error
    syntax_error_file = project_path / "sample_syntax_error.py"
    syntax_error_file.write_text('''
"""Sample file with syntax error."""

def broken_function():
    print("This function is missing a closing parenthesis"
    return "broken"
''')
    
    # Create a file with type issues
    type_error_file = project_path / "sample_type_issues.py"
    type_error_file.write_text('''
"""Sample file with potential type issues."""

def add_numbers(a, b):  # Missing type annotations
    return a + b

def process_data(data):
    # Potential type issues
    result = data.upper()  # Assumes string but no type hint
    return result.split(",")

# Usage that might cause type issues
result = add_numbers("hello", "world")  # String concatenation instead of addition
processed = process_data(123)  # Passing int instead of string
''')
    
    return [str(valid_file), str(syntax_error_file), str(type_error_file)]


def demonstrate_individual_tests(logger, project_path: str, test_files: list):
    """Demonstrate running individual test types."""
    logger.info("=== Demonstrating Individual Tests ===")
    
    # 1. Syntax Check Demo
    logger.info("\n1. Running Syntax Check...")
    syntax_check = SyntaxCheck(
        target_files=test_files,
        language="python",
        max_iterations=3
    )
    
    attempt = syntax_check.run(project_path=project_path)
    logger.info(f"Syntax Check Result: {attempt.message}")
    logger.info(f"Validation: {'PASS' if syntax_check.validate(attempt) else 'FAIL'}")
    
    if syntax_check.syntax_errors:
        logger.info("Syntax Errors Found:")
        for error in syntax_check.syntax_errors[:3]:  # Show first 3 errors
            logger.info(f"  - {error['file']}:{error['line']} - {error['message']}")
    
    # 2. Type Check Demo
    logger.info("\n2. Running Type Check...")
    type_check = TypeCheck(
        target_files=test_files,
        language="python",
        type_checker="mypy",
        strict_mode=False,
        max_iterations=2
    )
    
    attempt = type_check.run(project_path=project_path)
    logger.info(f"Type Check Result: {attempt.message}")
    logger.info(f"Validation: {'PASS' if type_check.validate(attempt) else 'FAIL'}")
    
    # 3. Security Check Demo
    logger.info("\n3. Running Security Check...")
    security_check = CriticalSecurityCheck(
        target_files=test_files,
        language="python",
        security_tools=["bandit", "safety"],
        severity_threshold="medium",
        max_iterations=2
    )
    
    attempt = security_check.run(project_path=project_path)
    logger.info(f"Security Check Result: {attempt.message}")
    logger.info(f"Validation: {'PASS' if security_check.validate(attempt) else 'FAIL'}")


def demonstrate_test_runner(logger, project_path: str, test_files: list):
    """Demonstrate using TestRunner for coordinated test execution."""
    logger.info("\n=== Demonstrating Test Runner ===")
    
    # Create test runner
    runner = TestRunner(
        logger=logger,
        max_workers=1,  # Sequential execution for demo
        stop_on_first_success=True
    )
    
    # Add all test types
    runner.add_test(SyntaxCheck(
        target_files=test_files,
        language="python",
        max_iterations=2
    ))
    
    runner.add_test(TypeCheck(
        target_files=test_files,
        language="python",
        type_checker="mypy",
        max_iterations=2
    ))
    
    runner.add_test(CriticalSecurityCheck(
        target_files=test_files,
        language="python",
        severity_threshold="high",
        max_iterations=2
    ))
    
    logger.info(f"Test Runner initialized with {runner.test_count} tests")
    logger.info(f"Test names: {', '.join(runner.test_names)}")
    
    # Run all tests
    logger.info("\nRunning all tests...")
    results = runner.run_all_tests(project_path=project_path)
    
    # Display results
    logger.info("\n=== Test Results Summary ===")
    for test_name, result in results.items():
        status = "PASS" if result.final_result else "FAIL"
        logger.info(
            f"{test_name}: {status} "
            f"({result.current_iteration} iterations, "
            f"{result.success_rate:.1%} success rate)"
        )
        
        if result.last_attempt:
            logger.info(f"  Last attempt: {result.last_attempt.message}")
    
    # Run tests by category
    logger.info("\n=== Running Static Tests Only ===")
    static_results = runner.run_tests_by_category("static", project_path=project_path)
    logger.info(f"Static tests completed: {len(static_results)} tests")
    
    # Show execution history
    history = runner.get_execution_history()
    logger.info(f"\nExecution history contains {len(history)} records")
    
    return results


def demonstrate_multi_iteration(logger, project_path: str, test_files: list):
    """Demonstrate multi-iteration test execution."""
    logger.info("\n=== Demonstrating Multi-Iteration Execution ===")
    
    # Create a test that might need multiple iterations
    syntax_check = SyntaxCheck(
        target_files=test_files,
        language="python",
        max_iterations=5
    )
    
    runner = TestRunner(
        logger=logger,
        stop_on_first_success=False  # Run all iterations
    )
    
    runner.add_test(syntax_check)
    
    # Run the test
    results = runner.run_all_tests(project_path=project_path)
    
    # Analyze iteration results
    result = results["SyntaxCheck"]
    logger.info(f"\nMulti-iteration results for SyntaxCheck:")
    logger.info(f"Total iterations: {result.current_iteration}")
    logger.info(f"Success rate: {result.success_rate:.1%}")
    logger.info(f"Total duration: {result.total_duration:.2f}s")
    
    for i, attempt in enumerate(result.attempts, 1):
        logger.info(
            f"  Iteration {i}: {attempt.status.value} "
            f"(duration: {attempt.duration:.2f}s)"
        )


def demonstrate_error_handling(logger):
    """Demonstrate error handling in test execution."""
    logger.info("\n=== Demonstrating Error Handling ===")
    
    # Test with non-existent files
    syntax_check = SyntaxCheck(
        target_files=["/non/existent/file.py"],
        max_iterations=2
    )
    
    runner = TestRunner(logger=logger)
    runner.add_test(syntax_check)
    
    # This should handle errors gracefully
    results = runner.run_all_tests(project_path="/non/existent/path")
    
    result = results["SyntaxCheck"]
    logger.info(f"Error handling test result: {result.final_status.value}")
    if result.last_attempt:
        logger.info(f"Error message: {result.last_attempt.message}")


def main():
    """Main demonstration function."""
    # Setup
    logger = setup_logging()
    logger.info("Starting FixChain Core Logic Demonstration")
    
    # Create project directory and sample files
    project_path = Path("./demo_project")
    project_path.mkdir(exist_ok=True)
    
    try:
        # Create sample test files
        test_files = create_sample_test_files(project_path)
        logger.info(f"Created sample files: {[Path(f).name for f in test_files]}")
        
        # Run demonstrations
        demonstrate_individual_tests(logger, str(project_path), test_files)
        demonstrate_test_runner(logger, str(project_path), test_files)
        demonstrate_multi_iteration(logger, str(project_path), test_files)
        demonstrate_error_handling(logger)
        
        logger.info("\n=== Demonstration Complete ===")
        logger.info("Check the logs/fixchain_example.log file for detailed output")
        
    except Exception as e:
        logger.error(f"Error during demonstration: {str(e)}", exc_info=True)
        return 1
    
    finally:
        # Cleanup demo files
        try:
            import shutil
            if project_path.exists():
                shutil.rmtree(project_path)
                logger.info("Cleaned up demo project files")
        except Exception as e:
            logger.warning(f"Could not clean up demo files: {str(e)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())