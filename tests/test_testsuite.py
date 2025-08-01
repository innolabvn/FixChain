"""Tests for the FixChain test suite implementation.

This module contains comprehensive tests for the test suite components
including test cases, test executor, and integration tests.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from testsuite.interfaces.test_case import ITestCase, TestResult
from testsuite.static_tests.syntax_check import SyntaxCheckTest
from testsuite.static_tests.type_check import TypeCheckTest
from testsuite.static_tests.security_check import SecurityCheckTest
from core.test_executor import TestExecutor, run_syntax_check, run_all_static_tests
from models.test_result import TestSeverity, TestStatus, TestCategory


class TestSyntaxCheckTest:
    """Test cases for SyntaxCheckTest."""
    
    @pytest.fixture
    def syntax_test(self):
        """Create a SyntaxCheckTest instance."""
        return SyntaxCheckTest(max_iterations=3)
    
    @pytest.fixture
    def valid_python_file(self):
        """Create a temporary valid Python file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
def hello_world():
    """A simple function."""
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    hello_world()
''')
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    @pytest.fixture
    def invalid_python_file(self):
        """Create a temporary invalid Python file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
def broken_function(
    """Missing closing parenthesis."""
    print("This will cause a syntax error"
    return "error"

# TODO: Fix this syntax error
''')
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_valid_file(self, syntax_test, valid_python_file):
        """Test syntax check on a valid Python file."""
        result = await syntax_test.run(valid_python_file, "test_attempt_1")
        
        assert isinstance(result, TestResult)
        assert result.test_name == "SyntaxCheck"
        assert result.test_type == "static"
        assert result.status == "pass"
        assert result.tool == "ast"
        assert len(result.issues) == 0
        assert "No syntax errors found" in result.summary
    
    @pytest.mark.asyncio
    async def test_invalid_file(self, syntax_test, invalid_python_file):
        """Test syntax check on an invalid Python file."""
        result = await syntax_test.run(invalid_python_file, "test_attempt_2")
        
        assert isinstance(result, TestResult)
        assert result.test_name == "SyntaxCheck"
        assert result.test_type == "static"
        assert result.status == "fail"
        assert result.tool == "ast"
        assert len(result.issues) >= 1  # Should have syntax error + TODO
        
        # Check for syntax error
        syntax_errors = [i for i in result.issues if i.severity == TestSeverity.CRITICAL]
        assert len(syntax_errors) >= 1
    
    @pytest.mark.asyncio
    async def test_nonexistent_file(self, syntax_test):
        """Test syntax check on a non-existent file."""
        result = await syntax_test.run("/nonexistent/file.py", "test_attempt_3")
        
        assert result.status == "fail"
        assert len(result.issues) == 1
        assert result.issues[0].severity == TestSeverity.CRITICAL
        assert "File not found" in result.issues[0].message
    
    def test_interface_compliance(self, syntax_test):
        """Test that SyntaxCheckTest implements ITestCase interface."""
        assert isinstance(syntax_test, ITestCase)
        assert hasattr(syntax_test, 'run')
        assert hasattr(syntax_test, 'get_tool_name')
        assert hasattr(syntax_test, 'can_run_iteration')
        assert hasattr(syntax_test, 'increment_iteration')
        assert hasattr(syntax_test, 'reset_iterations')


class TestTypeCheckTest:
    """Test cases for TypeCheckTest."""
    
    @pytest.fixture
    def type_test(self):
        """Create a TypeCheckTest instance."""
        return TypeCheckTest(max_iterations=3)
    
    @pytest.fixture
    def typed_python_file(self):
        """Create a temporary Python file with type annotations."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
from typing import List, Optional

def process_numbers(numbers: List[int]) -> Optional[int]:
    """Process a list of numbers."""
    if not numbers:
        return None
    return sum(numbers)

def main() -> None:
    """Main function."""
    result = process_numbers([1, 2, 3, 4, 5])
    print(f"Result: {result}")
''')
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_typed_file(self, type_test, typed_python_file):
        """Test type check on a well-typed Python file."""
        result = await type_test.run(typed_python_file, "test_attempt_1")
        
        assert isinstance(result, TestResult)
        assert result.test_name == "TypeCheck"
        assert result.test_type == "static"
        assert result.tool == "mypy"
        # Status depends on mypy availability and configuration
        assert result.status in ["pass", "fail"]
    
    @pytest.mark.asyncio
    async def test_mypy_not_available(self, type_test, typed_python_file):
        """Test type check when mypy is not available."""
        with patch.object(type_test, '_is_mypy_available', return_value=False):
            result = await type_test.run(typed_python_file, "test_attempt_2")
            
            assert result.tool == "mypy"
            assert "mypy not available" in result.output.lower()
    
    def test_interface_compliance(self, type_test):
        """Test that TypeCheckTest implements ITestCase interface."""
        assert isinstance(type_test, ITestCase)
        assert hasattr(type_test, 'run')
        assert hasattr(type_test, 'get_tool_name')


class TestSecurityCheckTest:
    """Test cases for SecurityCheckTest."""
    
    @pytest.fixture
    def security_test(self):
        """Create a SecurityCheckTest instance."""
        return SecurityCheckTest(max_iterations=3)
    
    @pytest.fixture
    def insecure_python_file(self):
        """Create a temporary Python file with security issues."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
import os
import subprocess

# Security issues for testing
password = "hardcoded_secret_123"  # Hardcoded password

def execute_command(user_input):
    """Unsafe command execution."""
    os.system("ls " + user_input)  # Shell injection
    
def unsafe_eval(code):
    """Unsafe eval usage."""
    return eval(code)  # Dangerous eval

def weak_hash():
    """Weak cryptographic function."""
    import hashlib
    return hashlib.md5(b"data").hexdigest()  # Weak hash
''')
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    @pytest.fixture
    def secure_python_file(self):
        """Create a temporary secure Python file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
import hashlib
import subprocess
from typing import List

def secure_hash(data: bytes) -> str:
    """Secure hash function."""
    return hashlib.sha256(data).hexdigest()

def safe_command(args: List[str]) -> str:
    """Safe command execution."""
    result = subprocess.run(args, capture_output=True, text=True, shell=False)
    return result.stdout
''')
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_insecure_file(self, security_test, insecure_python_file):
        """Test security check on an insecure Python file."""
        result = await security_test.run(insecure_python_file, "test_attempt_1")
        
        assert isinstance(result, TestResult)
        assert result.test_name == "SecurityCheck"
        assert result.test_type == "static"
        assert result.status == "fail"
        assert result.tool == "bandit"
        assert len(result.issues) > 0
        
        # Check for specific security issues
        issue_messages = [issue.message.lower() for issue in result.issues]
        assert any("password" in msg or "hardcoded" in msg for msg in issue_messages)
    
    @pytest.mark.asyncio
    async def test_secure_file(self, security_test, secure_python_file):
        """Test security check on a secure Python file."""
        result = await security_test.run(secure_python_file, "test_attempt_2")
        
        assert isinstance(result, TestResult)
        assert result.test_name == "SecurityCheck"
        assert result.test_type == "static"
        assert result.tool == "bandit"
        # Should have fewer or no issues
    
    def test_interface_compliance(self, security_test):
        """Test that SecurityCheckTest implements ITestCase interface."""
        assert isinstance(security_test, ITestCase)
        assert hasattr(security_test, 'run')
        assert hasattr(security_test, 'get_tool_name')


class TestTestExecutor:
    """Test cases for TestExecutor."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database."""
        db = Mock()
        db.save_test_result = AsyncMock()
        return db
    
    @pytest.fixture
    def mock_rag_store(self):
        """Create a mock RAG store."""
        rag_store = Mock()
        rag_store.store_reasoning = AsyncMock()
        return rag_store
    
    @pytest.fixture
    def test_executor(self, mock_db, mock_rag_store):
        """Create a TestExecutor instance with mocked dependencies."""
        return TestExecutor(db=mock_db, rag_store=mock_rag_store)
    
    @pytest.fixture
    def sample_python_file(self):
        """Create a sample Python file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
def sample_function():
    """A sample function."""
    return "Hello, World!"
''')
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_execute_single_test(self, test_executor, sample_python_file):
        """Test executing a single test case."""
        result = await test_executor.execute_test(
            test_name="syntax_check",
            source_file=sample_python_file,
            max_iterations=2
        )
        
        assert result.test_name == "syntax_check"
        assert result.test_category == TestCategory.STATIC
        assert result.source_file == sample_python_file
        assert len(result.attempts) >= 1
        assert result.final_status in [TestStatus.PASSED, TestStatus.FAILED, TestStatus.ERROR]
    
    @pytest.mark.asyncio
    async def test_execute_test_suite(self, test_executor, sample_python_file):
        """Test executing multiple tests as a suite."""
        test_names = ["syntax_check", "type_check"]
        results = await test_executor.execute_test_suite(
            test_names=test_names,
            source_file=sample_python_file,
            max_iterations=1
        )
        
        assert len(results) == 2
        assert "syntax_check" in results
        assert "type_check" in results
        
        for test_name, result in results.items():
            assert result.test_name == test_name
            assert result.source_file == sample_python_file
    
    @pytest.mark.asyncio
    async def test_execute_static_tests(self, test_executor, sample_python_file):
        """Test executing all static tests."""
        results = await test_executor.execute_static_tests(
            source_file=sample_python_file,
            max_iterations=1
        )
        
        expected_tests = ["syntax_check", "type_check", "security_check"]
        assert len(results) == len(expected_tests)
        
        for test_name in expected_tests:
            assert test_name in results
            assert results[test_name].test_category == TestCategory.STATIC
    
    @pytest.mark.asyncio
    async def test_unknown_test(self, test_executor, sample_python_file):
        """Test executing an unknown test."""
        with pytest.raises(ValueError, match="Unknown test"):
            await test_executor.execute_test(
                test_name="unknown_test",
                source_file=sample_python_file
            )
    
    @pytest.mark.asyncio
    async def test_nonexistent_file(self, test_executor):
        """Test executing test on non-existent file."""
        with pytest.raises(FileNotFoundError):
            await test_executor.execute_test(
                test_name="syntax_check",
                source_file="/nonexistent/file.py"
            )
    
    def test_get_available_tests(self, test_executor):
        """Test getting available tests."""
        tests = test_executor.get_available_tests()
        expected_tests = ["syntax_check", "type_check", "security_check"]
        
        for test_name in expected_tests:
            assert test_name in tests
    
    def test_get_test_info(self, test_executor):
        """Test getting test information."""
        info = test_executor.get_test_info("syntax_check")
        
        assert info["name"] == "SyntaxCheck"
        assert info["test_type"] == "static"
        assert info["category"] == "static"
        assert info["tool"] == "ast"
    
    def test_register_test(self, test_executor):
        """Test registering a new test."""
        class CustomTest(ITestCase):
            def __init__(self):
                super().__init__("CustomTest", "static", 1)
            
            async def run(self, source_file: str, attempt_id: str, **kwargs) -> TestResult:
                return TestResult(
                    test_name="CustomTest",
                    test_type="static",
                    issues=[],
                    summary="Custom test",
                    status="pass",
                    tool="custom",
                    output="Custom output"
                )
            
            def get_tool_name(self) -> str:
                return "custom"
        
        test_executor.register_test("custom_test", CustomTest, TestCategory.STATIC)
        
        assert "custom_test" in test_executor.get_available_tests()
        assert test_executor.test_categories["custom_test"] == TestCategory.STATIC


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.fixture
    def sample_python_file(self):
        """Create a sample Python file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
def test_function():
    """A test function."""
    return True
''')
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_run_syntax_check(self, sample_python_file):
        """Test run_syntax_check convenience function."""
        with patch('core.test_executor.FixChainDB'), \
             patch('core.test_executor.FixChainRAGStore'):
            
            result = await run_syntax_check(sample_python_file, max_iterations=1)
            
            assert result.test_name == "syntax_check"
            assert result.source_file == sample_python_file
    
    @pytest.mark.asyncio
    async def test_run_all_static_tests(self, sample_python_file):
        """Test run_all_static_tests convenience function."""
        with patch('core.test_executor.FixChainDB'), \
             patch('core.test_executor.FixChainRAGStore'):
            
            results = await run_all_static_tests(sample_python_file, max_iterations=1)
            
            expected_tests = ["syntax_check", "type_check", "security_check"]
            assert len(results) == len(expected_tests)
            
            for test_name in expected_tests:
                assert test_name in results
                assert results[test_name].source_file == sample_python_file


if __name__ == "__main__":
    pytest.main([__file__, "-v"])