"""Security check test implementation.

This module implements security checking for Python source files using bandit
and custom security pattern detection.
"""

import os
import subprocess
import json
import re
from typing import List, Dict, Any
from ..interfaces.test_case import ITestCase, TestResult
from models.test_result import TestIssue, TestSeverity


class SecurityCheckTest(ITestCase):
    """Test case for checking Python security vulnerabilities.
    
    This test uses bandit to perform security analysis on Python source files
    and includes custom security pattern detection.
    """
    
    def __init__(self, max_iterations: int = 5):
        """Initialize security check test.
        
        Args:
            max_iterations: Maximum number of test iterations
        """
        super().__init__(
            name="SecurityCheck",
            test_type="static",
            max_iterations=max_iterations
        )
        
        # Security patterns to detect
        self.security_patterns = {
            'hardcoded_password': {
                'pattern': r'(password|passwd|pwd)\s*=\s*["\'][^"\' ]{3,}["\']',
                'severity': TestSeverity.CRITICAL,
                'message': 'Hardcoded password detected',
                'suggestion': 'Use environment variables or secure configuration for passwords'
            },
            'sql_injection': {
                'pattern': r'(execute|query)\s*\([^)]*%[^)]*\)',
                'severity': TestSeverity.HIGH,
                'message': 'Potential SQL injection vulnerability',
                'suggestion': 'Use parameterized queries instead of string formatting'
            },
            'eval_usage': {
                'pattern': r'\beval\s*\(',
                'severity': TestSeverity.HIGH,
                'message': 'Use of eval() function detected',
                'suggestion': 'Avoid eval() as it can execute arbitrary code'
            },
            'exec_usage': {
                'pattern': r'\bexec\s*\(',
                'severity': TestSeverity.HIGH,
                'message': 'Use of exec() function detected',
                'suggestion': 'Avoid exec() as it can execute arbitrary code'
            },
            'shell_injection': {
                'pattern': r'(os\.system|subprocess\.call|subprocess\.run)\s*\([^)]*\+[^)]*\)',
                'severity': TestSeverity.HIGH,
                'message': 'Potential shell injection vulnerability',
                'suggestion': 'Use subprocess with shell=False and proper argument handling'
            },
            'weak_crypto': {
                'pattern': r'(md5|sha1)\s*\(',
                'severity': TestSeverity.MEDIUM,
                'message': 'Weak cryptographic hash function',
                'suggestion': 'Use stronger hash functions like SHA-256 or SHA-3'
            },
            'debug_mode': {
                'pattern': r'debug\s*=\s*True',
                'severity': TestSeverity.MEDIUM,
                'message': 'Debug mode enabled',
                'suggestion': 'Disable debug mode in production'
            }
        }
    
    async def run(
        self,
        source_file: str,
        attempt_id: str,
        **kwargs
    ) -> TestResult:
        """Execute security check on the source file.
        
        Args:
            source_file: Path to the Python file to check
            attempt_id: Unique identifier for this test attempt
            **kwargs: Additional parameters
                - confidence_level: str, minimum confidence level for bandit (low, medium, high)
                - severity_level: str, minimum severity level for bandit (low, medium, high)
            
        Returns:
            TestResult: Test execution result
        """
        issues = []
        output_lines = []
        
        # Get configuration options
        confidence_level = kwargs.get('confidence_level', 'medium')
        severity_level = kwargs.get('severity_level', 'low')
        
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
                    error_code="S001",
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
            
            output_lines.append(f"Security checking: {source_file}")
            
            # Run custom security pattern detection
            custom_issues = await self._run_custom_security_check(source_file)
            issues.extend(custom_issues)
            output_lines.append(f"Custom security patterns: {len(custom_issues)} issues found")
            
            # Check if bandit is available and run it
            if self._is_bandit_available():
                bandit_result = await self._run_bandit(source_file, confidence_level, severity_level)
                
                if bandit_result['success']:
                    issues.extend(bandit_result['issues'])
                    output_lines.extend(bandit_result['output'])
                    output_lines.append(f"Bandit analysis: {len(bandit_result['issues'])} issues found")
                else:
                    output_lines.append(f"Bandit execution failed: {bandit_result['error']}")
            else:
                output_lines.append("Bandit not available, using custom security checks only")
            
            # Determine overall status
            critical_issues = [i for i in issues if i.severity == TestSeverity.CRITICAL]
            high_issues = [i for i in issues if i.severity == TestSeverity.HIGH]
            
            if critical_issues:
                status = "fail"
                summary = f"Found {len(critical_issues)} critical security issues"
            elif high_issues:
                status = "fail"
                summary = f"Found {len(high_issues)} high severity security issues"
            elif issues:
                status = "fail"
                summary = f"Found {len(issues)} security issues"
            else:
                status = "pass"
                summary = "No security issues found"
                
        except Exception as e:
            # Handle unexpected errors
            issues.append(TestIssue(
                file=source_file,
                line=0,
                column=0,
                message=f"Unexpected error during security check: {str(e)}",
                severity=TestSeverity.HIGH,
                rule_id="UNEXPECTED_ERROR",
                tool=self.get_tool_name(),
                error_code="S002",
                suggestion="Check file permissions and tool installations"
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
                "confidence_level": confidence_level,
                "severity_level": severity_level,
                "custom_patterns_checked": len(self.security_patterns)
            }
        )
    
    def _is_bandit_available(self) -> bool:
        """Check if bandit is available in the system.
        
        Returns:
            bool: True if bandit is available
        """
        try:
            result = subprocess.run(
                ['bandit', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def _run_custom_security_check(self, source_file: str) -> List[TestIssue]:
        """Run custom security pattern detection.
        
        Args:
            source_file: Path to the file to check
            
        Returns:
            List[TestIssue]: Issues found by custom patterns
        """
        issues = []
        
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern_name, pattern_info in self.security_patterns.items():
                    if re.search(pattern_info['pattern'], line, re.IGNORECASE):
                        match = re.search(pattern_info['pattern'], line, re.IGNORECASE)
                        column = match.start() if match else 0
                        
                        issues.append(TestIssue(
                            file=source_file,
                            line=line_num,
                            column=column,
                            message=pattern_info['message'],
                            severity=pattern_info['severity'],
                            rule_id=pattern_name.upper(),
                            tool=self.get_tool_name(),
                            error_code=f"S{100 + len(issues)}",
                            suggestion=pattern_info['suggestion']
                        ))
            
        except Exception as e:
            issues.append(TestIssue(
                file=source_file,
                line=0,
                column=0,
                message=f"Error in custom security check: {str(e)}",
                severity=TestSeverity.MEDIUM,
                rule_id="CUSTOM_CHECK_ERROR",
                tool=self.get_tool_name(),
                error_code="S099",
                suggestion="Check file encoding and permissions"
            ))
        
        return issues
    
    async def _run_bandit(
        self,
        source_file: str,
        confidence_level: str,
        severity_level: str
    ) -> Dict[str, Any]:
        """Run bandit security analysis.
        
        Args:
            source_file: Path to the file to check
            confidence_level: Minimum confidence level
            severity_level: Minimum severity level
            
        Returns:
            Dict containing success status, issues, output, and error
        """
        try:
            # Build bandit command
            cmd = [
                'bandit',
                '-f', 'json',
                '-i', confidence_level,
                '-ii', severity_level,
                source_file
            ]
            
            # Run bandit
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            issues = []
            output_lines = []
            
            if result.stdout:
                try:
                    bandit_data = json.loads(result.stdout)
                    issues.extend(self._parse_bandit_output(bandit_data, source_file))
                    output_lines.append(f"Bandit found {len(issues)} issues")
                except json.JSONDecodeError:
                    output_lines.append("Failed to parse bandit JSON output")
            
            if result.stderr:
                output_lines.append(f"Bandit stderr: {result.stderr}")
            
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
                'error': 'Bandit execution timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'issues': [],
                'output': [],
                'error': str(e)
            }
    
    def _parse_bandit_output(self, bandit_data: Dict[str, Any], source_file: str) -> List[TestIssue]:
        """Parse bandit JSON output to extract issues.
        
        Args:
            bandit_data: Bandit JSON output
            source_file: Source file being checked
            
        Returns:
            List[TestIssue]: Parsed issues
        """
        issues = []
        
        if 'results' in bandit_data:
            for result in bandit_data['results']:
                # Map bandit severity to our severity
                bandit_severity = result.get('issue_severity', 'MEDIUM').upper()
                if bandit_severity == 'LOW':
                    severity = TestSeverity.LOW
                elif bandit_severity == 'MEDIUM':
                    severity = TestSeverity.MEDIUM
                elif bandit_severity == 'HIGH':
                    severity = TestSeverity.HIGH
                else:
                    severity = TestSeverity.MEDIUM
                
                issues.append(TestIssue(
                    file=result.get('filename', source_file),
                    line=result.get('line_number', 0),
                    column=result.get('col_offset', 0),
                    message=result.get('issue_text', 'Security issue detected'),
                    severity=severity,
                    rule_id=result.get('test_id', 'BANDIT_ISSUE'),
                    tool=self.get_tool_name(),
                    error_code=result.get('test_id', 'B000'),
                    suggestion=self._get_security_suggestion(result.get('issue_text', ''))
                ))
        
        return issues
    
    def _get_security_suggestion(self, message: str) -> str:
        """Generate security suggestion based on issue message.
        
        Args:
            message: Security issue message
            
        Returns:
            str: Suggested fix
        """
        message_lower = message.lower()
        
        if 'hardcoded' in message_lower and 'password' in message_lower:
            return "Use environment variables or secure configuration management"
        elif 'sql' in message_lower and 'injection' in message_lower:
            return "Use parameterized queries or ORM methods"
        elif 'shell' in message_lower and 'injection' in message_lower:
            return "Use subprocess with shell=False and validate inputs"
        elif 'eval' in message_lower or 'exec' in message_lower:
            return "Replace eval/exec with safer alternatives"
        elif 'crypto' in message_lower or 'hash' in message_lower:
            return "Use cryptographically secure hash functions"
        elif 'random' in message_lower:
            return "Use cryptographically secure random number generators"
        elif 'ssl' in message_lower or 'tls' in message_lower:
            return "Enable SSL/TLS verification and use secure protocols"
        else:
            return "Review and address the security vulnerability"
    
    def get_tool_name(self) -> str:
        """Get the tool name for this test.
        
        Returns:
            str: Tool name
        """
        return "bandit"