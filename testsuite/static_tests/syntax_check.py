"""Syntax check test implementation.

This module implements syntax checking for Python source files using the ast module.
"""

import ast
import os
from typing import List, Dict, Any
from ..interfaces.test_case import ITestCase, TestResult
from models.test_result import TestIssue, TestSeverity


class SyntaxCheckTest(ITestCase):
    """Test case for checking Python syntax errors.
    
    This test uses Python's built-in ast module to parse source files
    and detect syntax errors.
    """
    
    def __init__(self, max_iterations: int = 5):
        """Initialize syntax check test.
        
        Args:
            max_iterations: Maximum number of test iterations
        """
        super().__init__(
            name="SyntaxCheck",
            test_type="static",
            max_iterations=max_iterations
        )
    
    async def run(
        self,
        source_file: str,
        attempt_id: str,
        **kwargs
    ) -> TestResult:
        """Execute syntax check on the source file.
        
        Args:
            source_file: Path to the Python file to check
            attempt_id: Unique identifier for this test attempt
            **kwargs: Additional parameters (unused)
            
        Returns:
            TestResult: Test execution result
        """
        issues = []
        output_lines = []
        
        try:
            # Check if file exists
            if not os.path.exists(source_file):
                issues.append(TestIssue(
                    file=source_file,
                    line=0,
                    column=0,
                    message=f"File not found: {source_file}",
                    severity=TestSeverity.CRITICAL,
                    rule_id="FILE_NOT_FOUND",
                    tool=self.get_tool_name(),
                    error_code="E001",
                    suggestion="Ensure the file path is correct and the file exists"
                ))
                
                return TestResult(
                    test_name=self.name,
                    test_type=self.test_type,
                    issues=issues,
                    summary=f"File not found: {source_file}",
                    status="fail",
                    tool=self.get_tool_name(),
                    output="File not found"
                )
            
            # Read and parse the file
            with open(source_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            output_lines.append(f"Checking syntax for: {source_file}")
            
            # Try to parse the AST
            try:
                ast.parse(source_code, filename=source_file)
                output_lines.append("✓ Syntax check passed")
                
                # Check for TODO comments that simulate issues
                todo_issues = self._check_for_todo_issues(source_code, source_file)
                issues.extend(todo_issues)
                
                if todo_issues:
                    output_lines.append(f"Found {len(todo_issues)} TODO items that need attention")
                    status = "fail"
                    summary = f"Syntax is valid but found {len(todo_issues)} TODO items requiring fixes"
                else:
                    status = "pass"
                    summary = "No syntax errors found"
                    
            except SyntaxError as e:
                # Create issue for syntax error
                issues.append(TestIssue(
                    file=source_file,
                    line=e.lineno or 0,
                    column=e.offset or 0,
                    message=e.msg or "Syntax error",
                    severity=TestSeverity.CRITICAL,
                    rule_id="SYNTAX_ERROR",
                    tool=self.get_tool_name(),
                    error_code="E002",
                    suggestion="Fix the syntax error according to Python language rules"
                ))
                
                output_lines.append(f"✗ Syntax error at line {e.lineno}: {e.msg}")
                status = "fail"
                summary = f"Syntax error found at line {e.lineno}: {e.msg}"
                
        except Exception as e:
            # Handle unexpected errors
            issues.append(TestIssue(
                file=source_file,
                line=0,
                column=0,
                message=f"Unexpected error during syntax check: {str(e)}",
                severity=TestSeverity.HIGH,
                rule_id="UNEXPECTED_ERROR",
                tool=self.get_tool_name(),
                error_code="E003",
                suggestion="Check file encoding and permissions"
            ))
            
            output_lines.append(f"✗ Unexpected error: {str(e)}")
            status = "fail"
            summary = f"Unexpected error: {str(e)}"
        
        return TestResult(
            test_name=self.name,
            test_type=self.test_type,
            issues=issues,
            summary=summary,
            status=status,
            tool=self.get_tool_name(),
            output="\n".join(output_lines),
            metadata={
                "attempt_id": attempt_id,
                "iteration": self.current_iteration + 1,
                "source_file": source_file,
                "file_size": os.path.getsize(source_file) if os.path.exists(source_file) else 0
            }
        )
    
    def _check_for_todo_issues(self, source_code: str, source_file: str) -> List[TestIssue]:
        """Check for TODO comments that simulate issues.
        
        Args:
            source_code: The source code content
            source_file: Path to the source file
            
        Returns:
            List[TestIssue]: List of TODO-related issues
        """
        issues = []
        lines = source_code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower().strip()
            
            # Check for various TODO patterns
            if '# todo:' in line_lower:
                todo_text = line.split('# todo:', 1)[1].strip() if '# todo:' in line_lower else "fix this"
                issues.append(TestIssue(
                    file=source_file,
                    line=line_num,
                    column=line.find('#'),
                    message=f"TODO item found: {todo_text}",
                    severity=TestSeverity.MEDIUM,
                    rule_id="TODO_FOUND",
                    tool=self.get_tool_name(),
                    error_code="W001",
                    suggestion="Implement the TODO item or remove the comment"
                ))
            
            elif '# fixme' in line_lower:
                fixme_text = line.split('# fixme', 1)[1].strip() if '# fixme' in line_lower else "fix this"
                issues.append(TestIssue(
                    file=source_file,
                    line=line_num,
                    column=line.find('#'),
                    message=f"FIXME item found: {fixme_text}",
                    severity=TestSeverity.HIGH,
                    rule_id="FIXME_FOUND",
                    tool=self.get_tool_name(),
                    error_code="W002",
                    suggestion="Address the FIXME item immediately"
                ))
            
            elif 'raise NotImplementedError' in line:
                issues.append(TestIssue(
                    file=source_file,
                    line=line_num,
                    column=line.find('raise'),
                    message="Method not implemented",
                    severity=TestSeverity.HIGH,
                    rule_id="NOT_IMPLEMENTED",
                    tool=self.get_tool_name(),
                    error_code="W003",
                    suggestion="Implement the method or remove the NotImplementedError"
                ))
        
        return issues
    
    def get_tool_name(self) -> str:
        """Get the tool name for this test.
        
        Returns:
            str: Tool name
        """
        return "ast"