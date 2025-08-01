"""Syntax Check Test Implementation

This module implements syntax checking for code files using various tools
like Python's ast module, flake8, or other language-specific parsers.
"""

import ast
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from ...base import TestCase, TestAttempt, TestCategory


class SyntaxCheck(TestCase):
    """Test case for checking syntax errors in code files."""
    
    def __init__(self, 
                 target_files: Optional[List[str]] = None,
                 language: str = "python",
                 max_iterations: int = 5):
        """
        Initialize SyntaxCheck test.
        
        Args:
            target_files: List of file paths to check (if None, will scan project)
            language: Programming language to check (default: python)
            max_iterations: Maximum number of test iterations
        """
        super().__init__(
            name="SyntaxCheck",
            description="Checks for syntax errors in code files",
            category=TestCategory.STATIC,
            max_iterations=max_iterations
        )
        self.target_files = target_files or []
        self.language = language.lower()
        self.syntax_errors: List[Dict[str, Any]] = []
    
    def run(self, **kwargs) -> TestAttempt:
        """Execute syntax checking.
        
        Args:
            **kwargs: Additional parameters including:
                - project_path: Path to project directory
                - exclude_patterns: List of patterns to exclude
                - include_patterns: List of patterns to include
                
        Returns:
            TestAttempt: Test execution result
        """
        start_time = datetime.now()
        attempt = TestAttempt(
            iteration=self.result.current_iteration + 1,
            start_time=start_time
        )
        
        try:
            # Get project path from kwargs or use current directory
            project_path = kwargs.get('project_path', '.')
            exclude_patterns = kwargs.get('exclude_patterns', ['__pycache__', '.git', '.venv'])
            include_patterns = kwargs.get('include_patterns', [])
            
            # Discover files if not specified
            if not self.target_files:
                self.target_files = self._discover_files(project_path, exclude_patterns, include_patterns)
            
            # Check syntax for each file
            syntax_errors = []
            total_files = len(self.target_files)
            
            for file_path in self.target_files:
                file_errors = self._check_file_syntax(file_path)
                if file_errors:
                    syntax_errors.extend(file_errors)
            
            # TODO: Implement more sophisticated syntax checking
            # - Add support for multiple programming languages
            # - Integrate with language-specific linters (flake8, eslint, etc.)
            # - Add configurable severity levels
            # - Support for custom syntax rules
            
            self.syntax_errors = syntax_errors
            
            attempt.end_time = datetime.now()
            attempt.output = self._format_output(total_files, syntax_errors)
            attempt.metadata = {
                "total_files": total_files,
                "files_with_errors": len(set(err['file'] for err in syntax_errors)),
                "total_errors": len(syntax_errors),
                "language": self.language,
                "error_details": syntax_errors
            }
            
            if syntax_errors:
                attempt.message = f"Found {len(syntax_errors)} syntax errors in {len(set(err['file'] for err in syntax_errors))} files"
            else:
                attempt.message = f"No syntax errors found in {total_files} files"
                
        except Exception as e:
            attempt.end_time = datetime.now()
            attempt.output = f"Error during syntax check: {str(e)}"
            attempt.message = f"Syntax check failed: {str(e)}"
            attempt.metadata = {"error": str(e)}
        
        return attempt
    
    def validate(self, attempt: TestAttempt) -> bool:
        """Validate syntax check results.
        
        Args:
            attempt: Test attempt to validate
            
        Returns:
            bool: True if no syntax errors found, False otherwise
        """
        # TODO: Implement more sophisticated validation logic
        # - Allow configurable error thresholds
        # - Support for warning vs error distinction
        # - Integration with CI/CD pipeline requirements
        
        if "error" in attempt.metadata:
            return False
        
        total_errors = attempt.metadata.get("total_errors", 0)
        return total_errors == 0
    
    def _discover_files(self, project_path: str, exclude_patterns: List[str], 
                       include_patterns: List[str]) -> List[str]:
        """Discover files to check in the project.
        
        Args:
            project_path: Path to project directory
            exclude_patterns: Patterns to exclude
            include_patterns: Patterns to include
            
        Returns:
            List of file paths to check
        """
        # TODO: Implement comprehensive file discovery
        # - Support for multiple file extensions per language
        # - Respect .gitignore and other ignore files
        # - Add glob pattern matching
        # - Support for recursive directory scanning
        
        project_dir = Path(project_path)
        files = []
        
        if self.language == "python":
            # Simple Python file discovery
            for py_file in project_dir.rglob("*.py"):
                file_str = str(py_file)
                # Basic exclude pattern check
                if not any(pattern in file_str for pattern in exclude_patterns):
                    files.append(file_str)
        
        return files
    
    def _check_file_syntax(self, file_path: str) -> List[Dict[str, Any]]:
        """Check syntax for a single file.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            List of syntax errors found
        """
        errors = []
        
        try:
            if self.language == "python":
                errors.extend(self._check_python_syntax(file_path))
            else:
                # TODO: Add support for other languages
                # - JavaScript/TypeScript (using eslint, tsc)
                # - Java (using javac)
                # - C/C++ (using gcc/clang)
                # - Go (using go fmt, go vet)
                pass
                
        except Exception as e:
            errors.append({
                "file": file_path,
                "line": 0,
                "column": 0,
                "message": f"Error checking file: {str(e)}",
                "severity": "error"
            })
        
        return errors
    
    def _check_python_syntax(self, file_path: str) -> List[Dict[str, Any]]:
        """Check Python file syntax using AST.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            List of syntax errors
        """
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Parse with AST
            ast.parse(source_code, filename=file_path)
            
            # TODO: Add more comprehensive Python syntax checking
            # - Use flake8 for style and syntax issues
            # - Check for common Python antipatterns
            # - Validate import statements
            # - Check for undefined variables (basic static analysis)
            
        except SyntaxError as e:
            errors.append({
                "file": file_path,
                "line": e.lineno or 0,
                "column": e.offset or 0,
                "message": e.msg or "Syntax error",
                "severity": "error",
                "error_type": "SyntaxError"
            })
        except UnicodeDecodeError as e:
            errors.append({
                "file": file_path,
                "line": 0,
                "column": 0,
                "message": f"Unicode decode error: {str(e)}",
                "severity": "error",
                "error_type": "UnicodeDecodeError"
            })
        
        return errors
    
    def _format_output(self, total_files: int, syntax_errors: List[Dict[str, Any]]) -> str:
        """Format test output for display.
        
        Args:
            total_files: Total number of files checked
            syntax_errors: List of syntax errors found
            
        Returns:
            Formatted output string
        """
        output_lines = [
            f"Syntax Check Results ({self.language})",
            f"Files checked: {total_files}",
            f"Errors found: {len(syntax_errors)}",
            ""
        ]
        
        if syntax_errors:
            output_lines.append("Syntax Errors:")
            for error in syntax_errors:
                line_info = f":{error['line']}:{error['column']}" if error['line'] > 0 else ""
                output_lines.append(
                    f"  {error['file']}{line_info} - {error['message']}"
                )
        else:
            output_lines.append("✓ No syntax errors found")
        
        return "\n".join(output_lines)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of syntax errors.
        
        Returns:
            Dictionary with error summary statistics
        """
        if not self.syntax_errors:
            return {"total_errors": 0, "files_with_errors": 0}
        
        files_with_errors = set(err['file'] for err in self.syntax_errors)
        error_types = {}
        
        for error in self.syntax_errors:
            error_type = error.get('error_type', 'Unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.syntax_errors),
            "files_with_errors": len(files_with_errors),
            "error_types": error_types,
            "affected_files": list(files_with_errors)
        }