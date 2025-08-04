"""Type check test implementation.

This module implements type checking for Python source files using mypy.
"""

import os
import subprocess
import json
import tempfile
from typing import List, Dict, Any
from ..interfaces.test_case import ITestCase, TestResult
from models.test_result import TestIssue, TestSeverity


class TypeCheckTest(ITestCase):
    """Test case for checking Python type annotations and type safety.
    
    This test uses mypy to perform static type checking on Python source files.
    """
    
    def __init__(self, max_iterations: int = 5):
        """Initialize type check test.
        
        Args:
            max_iterations: Maximum number of test iterations
        """
        super().__init__(
            name="TypeCheck",
            test_type="static",
            max_iterations=max_iterations
        )
    
    async def run(
        self,
        source_file: str,
        attempt_id: str,
        **kwargs
    ) -> TestResult:
        """Execute type check on the source file.
        
        Args:
            source_file: Path to the Python file to check
            attempt_id: Unique identifier for this test attempt
            **kwargs: Additional parameters
                - strict_mode: bool, whether to use strict type checking
                - ignore_missing_imports: bool, whether to ignore missing import errors
            
        Returns:
            TestResult: Test execution result
        """
        issues = []
        output_lines = []
        
        # Get configuration options
        strict_mode = kwargs.get('strict_mode', False)
        ignore_missing_imports = kwargs.get('ignore_missing_imports', True)
        
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
                    error_code="T001",
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
            
            output_lines.append(f"Type checking: {source_file}")
            
            # Check if mypy is available
            if not self._is_mypy_available():
                # Fallback to basic type annotation checking
                output_lines.append("mypy not available, using basic type annotation check")
                return await self._basic_type_check(source_file, attempt_id, output_lines)
            
            # Run mypy
            mypy_result = await self._run_mypy(source_file, strict_mode, ignore_missing_imports)
            
            if mypy_result['success']:
                issues.extend(mypy_result['issues'])
                output_lines.extend(mypy_result['output'])
                
                if issues:
                    status = "fail"
                    summary = f"Found {len(issues)} type checking issues"
                else:
                    status = "pass"
                    summary = "No type checking issues found"
            else:
                # mypy execution failed
                issues.append(TestIssue(
                    file=source_file,
                    line=0,
                    column=0,
                    message=f"Type checker execution failed: {mypy_result['error']}",
                    severity=TestSeverity.HIGH,
                    rule_id="TOOL_ERROR",
                    tool=self.get_tool_name(),
                    error_code="T002",
                    suggestion="Check mypy installation and configuration"
                ))
                
                output_lines.append(f"[ERROR] mypy execution failed: {mypy_result['error']}")
                status = "fail"
                summary = f"Type checker execution failed: {mypy_result['error']}"
                
        except Exception as e:
            # Handle unexpected errors
            issues.append(TestIssue(
                file=source_file,
                line=0,
                column=0,
                message=f"Unexpected error during type check: {str(e)}",
                severity=TestSeverity.HIGH,
                rule_id="UNEXPECTED_ERROR",
                tool=self.get_tool_name(),
                error_code="T003",
                suggestion="Check file permissions and mypy installation"
            ))
            
            output_lines.append(f"[ERROR] Unexpected error: {str(e)}")
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
                "strict_mode": strict_mode,
                "ignore_missing_imports": ignore_missing_imports
            }
        )
    
    def _is_mypy_available(self) -> bool:
        """Check if mypy is available in the system.
        
        Returns:
            bool: True if mypy is available
        """
        try:
            result = subprocess.run(
                ['mypy', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def _run_mypy(
        self,
        source_file: str,
        strict_mode: bool,
        ignore_missing_imports: bool
    ) -> Dict[str, Any]:
        """Run mypy on the source file.
        
        Args:
            source_file: Path to the file to check
            strict_mode: Whether to use strict mode
            ignore_missing_imports: Whether to ignore missing imports
            
        Returns:
            Dict containing success status, issues, output, and error
        """
        try:
            # Build mypy command
            cmd = ['mypy', '--show-error-codes', '--no-error-summary']
            
            if strict_mode:
                cmd.append('--strict')
            
            if ignore_missing_imports:
                cmd.append('--ignore-missing-imports')
            
            cmd.append(source_file)
            
            # Run mypy
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            issues = []
            output_lines = []
            
            if result.stdout:
                output_lines.append("mypy output:")
                issues.extend(self._parse_mypy_output(result.stdout, source_file))
                output_lines.extend(result.stdout.split('\n'))
            
            if result.stderr:
                output_lines.append("mypy errors:")
                output_lines.extend(result.stderr.split('\n'))
            
            if result.returncode == 0:
                output_lines.append("[OK] Type check passed")
            else:
                output_lines.append(f"[ERROR] Type check failed with {len(issues)} issues")
            
            return {
                'success': True,
                'issues': issues,
                'output': output_lines,
                'error': None
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'issues': [],
                'output': [],
                'error': 'mypy execution timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'issues': [],
                'output': [],
                'error': str(e)
            }
    
    def _parse_mypy_output(self, output: str, source_file: str) -> List[TestIssue]:
        """Parse mypy output to extract issues.
        
        Args:
            output: mypy output text
            source_file: Source file being checked
            
        Returns:
            List[TestIssue]: Parsed issues
        """
        issues = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            # Parse mypy output format: file:line:column: level: message [error-code]
            parts = line.split(':', 3)
            if len(parts) >= 4:
                try:
                    file_path = parts[0]
                    line_num = int(parts[1]) if parts[1].isdigit() else 0
                    column_num = int(parts[2]) if parts[2].isdigit() else 0
                    message_part = parts[3].strip()
                    
                    # Extract error level and message
                    if message_part.startswith('error:'):
                        severity = TestSeverity.HIGH
                        message = message_part[6:].strip()
                    elif message_part.startswith('warning:'):
                        severity = TestSeverity.MEDIUM
                        message = message_part[8:].strip()
                    elif message_part.startswith('note:'):
                        severity = TestSeverity.LOW
                        message = message_part[5:].strip()
                    else:
                        severity = TestSeverity.MEDIUM
                        message = message_part
                    
                    # Extract error code if present
                    error_code = None
                    if '[' in message and ']' in message:
                        start = message.rfind('[')
                        end = message.rfind(']')
                        if start < end:
                            error_code = message[start+1:end]
                            message = message[:start].strip()
                    
                    issues.append(TestIssue(
                        file=file_path,
                        line=line_num,
                        column=column_num,
                        message=message,
                        severity=severity,
                        rule_id=error_code or "TYPE_ERROR",
                        tool=self.get_tool_name(),
                        error_code=error_code or "T100",
                        suggestion=self._get_type_suggestion(message)
                    ))
                    
                except (ValueError, IndexError):
                    # If parsing fails, create a generic issue
                    issues.append(TestIssue(
                        file=source_file,
                        line=0,
                        column=0,
                        message=f"Unparsed mypy output: {line}",
                        severity=TestSeverity.LOW,
                        rule_id="PARSE_ERROR",
                        tool=self.get_tool_name(),
                        error_code="T999",
                        suggestion="Review mypy output manually"
                    ))
        
        return issues
    
    def _get_type_suggestion(self, message: str) -> str:
        """Generate suggestion based on type error message.
        
        Args:
            message: Type error message
            
        Returns:
            str: Suggested fix
        """
        message_lower = message.lower()
        
        if 'missing type annotation' in message_lower:
            return "Add type annotations to the function or variable"
        elif 'incompatible types' in message_lower:
            return "Check type compatibility and fix type mismatches"
        elif 'has no attribute' in message_lower:
            return "Verify the attribute exists or check the object type"
        elif 'cannot be imported' in message_lower:
            return "Check import statement and module availability"
        elif 'unused' in message_lower:
            return "Remove unused imports or variables"
        else:
            return "Review and fix the type-related issue"
    
    async def _basic_type_check(
        self,
        source_file: str,
        attempt_id: str,
        output_lines: List[str]
    ) -> TestResult:
        """Perform basic type annotation checking when mypy is not available.
        
        Args:
            source_file: Path to the file to check
            attempt_id: Test attempt ID
            output_lines: Output lines to append to
            
        Returns:
            TestResult: Basic type check result
        """
        issues = []
        
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Basic checks for type annotations
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for function definitions without type annotations
                if line_stripped.startswith('def ') and '->' not in line:
                    if not line_stripped.endswith(':'):
                        continue
                    
                    func_name = line_stripped.split('(')[0].replace('def ', '')
                    if not func_name.startswith('_'):  # Skip private methods
                        issues.append(TestIssue(
                            file=source_file,
                            line=line_num,
                            column=0,
                            message=f"Function '{func_name}' missing return type annotation",
                            severity=TestSeverity.LOW,
                            rule_id="MISSING_RETURN_TYPE",
                            tool=self.get_tool_name(),
                            error_code="T200",
                            suggestion="Add return type annotation using -> syntax"
                        ))
            
            output_lines.append(f"Basic type check completed, found {len(issues)} issues")
            
            if issues:
                status = "fail"
                summary = f"Found {len(issues)} type annotation issues"
            else:
                status = "pass"
                summary = "Basic type check passed"
                
        except Exception as e:
            issues.append(TestIssue(
                file=source_file,
                line=0,
                column=0,
                message=f"Error during basic type check: {str(e)}",
                severity=TestSeverity.HIGH,
                rule_id="BASIC_CHECK_ERROR",
                tool=self.get_tool_name(),
                error_code="T201",
                suggestion="Check file encoding and permissions"
            ))
            
            status = "fail"
            summary = f"Basic type check failed: {str(e)}"
        
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
                "fallback_mode": True
            }
        )
    
    def get_tool_name(self) -> str:
        """Get the tool name for this test.
        
        Returns:
            str: Tool name
        """
        return "mypy"