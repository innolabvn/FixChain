"""Unit tests for SyntaxCheck test implementation.

This module contains unit tests for the SyntaxCheck class,
testing both successful and failure scenarios.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
from pathlib import Path

from core.tests.static.syntax_check import SyntaxCheck
from core.base import TestCategory, TestStatus


class TestSyntaxCheck:
    """Test cases for SyntaxCheck class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.syntax_check = SyntaxCheck(
            target_files=["test_file.py"],
            language="python",
            max_iterations=3
        )
    
    def test_initialization(self):
        """Test SyntaxCheck initialization."""
        assert self.syntax_check.name == "SyntaxCheck"
        assert self.syntax_check.description == "Checks for syntax errors in code files"
        assert self.syntax_check.category == TestCategory.STATIC
        assert self.syntax_check.max_iterations == 3
        assert self.syntax_check.language == "python"
        assert self.syntax_check.target_files == ["test_file.py"]
        assert self.syntax_check.syntax_errors == []
    
    def test_initialization_defaults(self):
        """Test SyntaxCheck initialization with defaults."""
        default_check = SyntaxCheck()
        assert default_check.target_files == []
        assert default_check.language == "python"
        assert default_check.max_iterations == 5
    
    @patch('builtins.open', new_callable=mock_open, read_data='print("Hello World")')
    @patch('ast.parse')
    def test_run_success_no_errors(self, mock_parse, mock_file):
        """Test successful run with no syntax errors."""
        # Mock ast.parse to not raise any exceptions
        mock_parse.return_value = None
        
        # Run the test
        attempt = self.syntax_check.run(project_path="/test/path")
        
        # Verify results
        assert attempt.iteration == 1
        assert attempt.start_time is not None
        assert attempt.end_time is not None
        assert "No syntax errors found" in attempt.message
        assert attempt.metadata["total_files"] == 1
        assert attempt.metadata["total_errors"] == 0
        assert attempt.metadata["language"] == "python"
        
        # Verify file was opened and parsed
        mock_file.assert_called_once_with("test_file.py", 'r', encoding='utf-8')
        mock_parse.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open, read_data='print("Hello World"')
    def test_run_with_syntax_error(self, mock_file):
        """Test run with syntax errors detected."""
        # Run the test (missing closing parenthesis will cause SyntaxError)
        attempt = self.syntax_check.run(project_path="/test/path")
        
        # Verify results
        assert attempt.iteration == 1
        assert "Found 1 syntax errors" in attempt.message
        assert attempt.metadata["total_errors"] == 1
        assert len(self.syntax_check.syntax_errors) == 1
        
        # Check error details
        error = self.syntax_check.syntax_errors[0]
        assert error["file"] == "test_file.py"
        assert error["severity"] == "error"
        assert error["error_type"] == "SyntaxError"
    
    @patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte'))
    def test_run_with_unicode_error(self, mock_file):
        """Test run with Unicode decode error."""
        # Run the test
        attempt = self.syntax_check.run(project_path="/test/path")
        
        # Verify results
        assert attempt.iteration == 1
        assert "Found 1 syntax errors" in attempt.message
        assert len(self.syntax_check.syntax_errors) == 1
        
        # Check error details
        error = self.syntax_check.syntax_errors[0]
        assert error["file"] == "test_file.py"
        assert error["error_type"] == "UnicodeDecodeError"
        assert "Unicode decode error" in error["message"]
    
    @patch('pathlib.Path.rglob')
    def test_discover_files_python(self, mock_rglob):
        """Test file discovery for Python files."""
        # Mock file discovery
        mock_files = [
            Path("/test/file1.py"),
            Path("/test/file2.py"),
            Path("/test/__pycache__/cached.py"),  # Should be excluded
            Path("/test/subdir/file3.py")
        ]
        mock_rglob.return_value = mock_files
        
        # Test file discovery
        syntax_check = SyntaxCheck()  # No target files specified
        files = syntax_check._discover_files(
            "/test", 
            exclude_patterns=["__pycache__"],
            include_patterns=[]
        )
        
        # Verify results
        expected_files = [
            "/test/file1.py",
            "/test/file2.py", 
            "/test/subdir/file3.py"
        ]
        assert len(files) == 3
        for expected_file in expected_files:
            assert any(expected_file in f for f in files)
    
    def test_validate_success(self):
        """Test validation with no errors."""
        from core.base import TestAttempt
        
        attempt = TestAttempt(
            iteration=1,
            start_time=datetime.now(),
            metadata={"total_errors": 0}
        )
        
        result = self.syntax_check.validate(attempt)
        assert result is True
    
    def test_validate_failure_with_errors(self):
        """Test validation with syntax errors."""
        from core.base import TestAttempt
        
        attempt = TestAttempt(
            iteration=1,
            start_time=datetime.now(),
            metadata={"total_errors": 2}
        )
        
        result = self.syntax_check.validate(attempt)
        assert result is False
    
    def test_validate_failure_with_error(self):
        """Test validation with execution error."""
        from core.base import TestAttempt
        
        attempt = TestAttempt(
            iteration=1,
            start_time=datetime.now(),
            metadata={"error": "Some execution error"}
        )
        
        result = self.syntax_check.validate(attempt)
        assert result is False
    
    def test_format_output_no_errors(self):
        """Test output formatting with no errors."""
        output = self.syntax_check._format_output(5, [])
        
        assert "Syntax Check Results (python)" in output
        assert "Files checked: 5" in output
        assert "Errors found: 0" in output
        assert "✓ No syntax errors found" in output
    
    def test_format_output_with_errors(self):
        """Test output formatting with errors."""
        errors = [
            {
                "file": "test1.py",
                "line": 10,
                "column": 5,
                "message": "invalid syntax"
            },
            {
                "file": "test2.py",
                "line": 0,
                "column": 0,
                "message": "unexpected EOF"
            }
        ]
        
        output = self.syntax_check._format_output(2, errors)
        
        assert "Syntax Check Results (python)" in output
        assert "Files checked: 2" in output
        assert "Errors found: 2" in output
        assert "Syntax Errors:" in output
        assert "test1.py:10:5 - invalid syntax" in output
        assert "test2.py - unexpected EOF" in output
    
    def test_get_error_summary_no_errors(self):
        """Test error summary with no errors."""
        summary = self.syntax_check.get_error_summary()
        
        assert summary["total_errors"] == 0
        assert summary["files_with_errors"] == 0
    
    def test_get_error_summary_with_errors(self):
        """Test error summary with errors."""
        self.syntax_check.syntax_errors = [
            {
                "file": "test1.py",
                "error_type": "SyntaxError",
                "message": "invalid syntax"
            },
            {
                "file": "test1.py",
                "error_type": "SyntaxError",
                "message": "unexpected token"
            },
            {
                "file": "test2.py",
                "error_type": "UnicodeDecodeError",
                "message": "decode error"
            }
        ]
        
        summary = self.syntax_check.get_error_summary()
        
        assert summary["total_errors"] == 3
        assert summary["files_with_errors"] == 2
        assert summary["error_types"]["SyntaxError"] == 2
        assert summary["error_types"]["UnicodeDecodeError"] == 1
        assert "test1.py" in summary["affected_files"]
        assert "test2.py" in summary["affected_files"]
    
    @patch('builtins.open', side_effect=FileNotFoundError("File not found"))
    def test_run_with_file_not_found(self, mock_file):
        """Test run when target file doesn't exist."""
        # Run the test
        attempt = self.syntax_check.run(project_path="/test/path")
        
        # Verify results
        assert attempt.iteration == 1
        assert "Found 1 syntax errors" in attempt.message
        assert len(self.syntax_check.syntax_errors) == 1
        
        # Check error details
        error = self.syntax_check.syntax_errors[0]
        assert error["file"] == "test_file.py"
        assert "Error checking file" in error["message"]
    
    def test_run_with_exception(self):
        """Test run method when an unexpected exception occurs."""
        # Create a syntax check with invalid configuration to trigger exception
        with patch.object(self.syntax_check, '_discover_files', side_effect=Exception("Unexpected error")):
            attempt = self.syntax_check.run(project_path="/test/path")
            
            # Verify error handling
            assert attempt.iteration == 1
            assert "Error during syntax check" in attempt.output
            assert "Syntax check failed" in attempt.message
            assert "error" in attempt.metadata
            assert "Unexpected error" in attempt.metadata["error"]


class TestSyntaxCheckIntegration:
    """Integration tests for SyntaxCheck."""
    
    def test_full_workflow_with_real_files(self, tmp_path):
        """Test complete workflow with real temporary files."""
        # Create test files
        valid_file = tmp_path / "valid.py"
        valid_file.write_text('print("Hello World")')
        
        invalid_file = tmp_path / "invalid.py"
        invalid_file.write_text('print("Hello World"')
        
        # Create syntax check instance
        syntax_check = SyntaxCheck(
            target_files=[str(valid_file), str(invalid_file)],
            max_iterations=2
        )
        
        # Run the test
        attempt = syntax_check.run(project_path=str(tmp_path))
        
        # Verify results
        assert attempt.iteration == 1
        assert attempt.metadata["total_files"] == 2
        assert attempt.metadata["total_errors"] == 1  # Only invalid.py should have error
        
        # Validate the attempt
        is_valid = syntax_check.validate(attempt)
        assert is_valid is False  # Should fail due to syntax error
        
        # Check error summary
        summary = syntax_check.get_error_summary()
        assert summary["total_errors"] == 1
        assert summary["files_with_errors"] == 1
        assert str(invalid_file) in summary["affected_files"]