"""Critical Security Check Test Implementation

This module implements security vulnerability scanning for code files using
tools like bandit, safety, semgrep, or other security analysis tools.
"""

import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from ...base import TestCase, TestAttempt, TestCategory


class CriticalSecurityCheck(TestCase):
    """Test case for checking critical security vulnerabilities."""
    
    def __init__(self, 
                 target_files: Optional[List[str]] = None,
                 language: str = "python",
                 security_tools: Optional[List[str]] = None,
                 severity_threshold: str = "medium",
                 max_iterations: int = 5):
        """
        Initialize CriticalSecurityCheck test.
        
        Args:
            target_files: List of file paths to check (if None, will scan project)
            language: Programming language to check (default: python)
            security_tools: List of security tools to use (bandit, safety, etc.)
            severity_threshold: Minimum severity level to report (low, medium, high, critical)
            max_iterations: Maximum number of test iterations
        """
        super().__init__(
            name="CriticalSecurityCheck",
            description="Scans for critical security vulnerabilities",
            category=TestCategory.STATIC,
            max_iterations=max_iterations
        )
        self.target_files = target_files or []
        self.language = language.lower()
        self.security_tools = security_tools or self._get_default_tools()
        self.severity_threshold = severity_threshold.lower()
        self.security_issues: List[Dict[str, Any]] = []
        self.severity_levels = ["low", "medium", "high", "critical"]
    
    def _get_default_tools(self) -> List[str]:
        """Get default security tools for the language.
        
        Returns:
            List of default security tool names
        """
        if self.language == "python":
            return ["bandit", "safety"]
        elif self.language == "javascript":
            return ["eslint-security", "npm-audit"]
        elif self.language == "java":
            return ["spotbugs", "dependency-check"]
        else:
            return ["semgrep"]  # Generic tool
    
    def run(self, **kwargs) -> TestAttempt:
        """Execute security vulnerability scanning.
        
        Args:
            **kwargs: Additional parameters including:
                - project_path: Path to project directory
                - config_file: Path to security tool config file
                - exclude_patterns: List of patterns to exclude
                - include_patterns: List of patterns to include
                - custom_rules: Path to custom security rules
                
        Returns:
            TestAttempt: Test execution result
        """
        start_time = datetime.now()
        attempt = TestAttempt(
            iteration=self.result.current_iteration + 1,
            start_time=start_time
        )
        
        try:
            # Get parameters from kwargs
            project_path = kwargs.get('project_path', '.')
            config_file = kwargs.get('config_file')
            exclude_patterns = kwargs.get('exclude_patterns', ['__pycache__', '.git', '.venv', 'node_modules'])
            include_patterns = kwargs.get('include_patterns', [])
            custom_rules = kwargs.get('custom_rules')
            
            # Discover files if not specified
            if not self.target_files:
                self.target_files = self._discover_files(project_path, exclude_patterns, include_patterns)
            
            # Run security checks with all configured tools
            all_security_issues = []
            total_files = len(self.target_files)
            
            for tool in self.security_tools:
                try:
                    tool_issues = self._run_security_tool(tool, project_path, config_file, custom_rules)
                    all_security_issues.extend(tool_issues)
                except Exception as e:
                    # Log tool-specific errors but continue with other tools
                    all_security_issues.append({
                        "file": project_path,
                        "line": 0,
                        "column": 0,
                        "message": f"Security tool '{tool}' failed: {str(e)}",
                        "severity": "error",
                        "tool": tool,
                        "rule_id": "tool_error"
                    })
            
            # Filter by severity threshold
            filtered_issues = self._filter_by_severity(all_security_issues)
            
            # TODO: Implement more sophisticated security checking features
            # - Integration with vulnerability databases (CVE, NVD)
            # - Custom security rule definitions
            # - False positive filtering and whitelisting
            # - Integration with dependency vulnerability scanning
            # - SAST (Static Application Security Testing) integration
            # - Secret detection (API keys, passwords, tokens)
            # - License compliance checking
            
            self.security_issues = filtered_issues
            
            attempt.end_time = datetime.now()
            attempt.output = self._format_output(total_files, filtered_issues)
            attempt.metadata = {
                "total_files": total_files,
                "files_with_issues": len(set(issue['file'] for issue in filtered_issues)),
                "total_issues": len(filtered_issues),
                "critical_issues": len([i for i in filtered_issues if i.get('severity') == 'critical']),
                "high_issues": len([i for i in filtered_issues if i.get('severity') == 'high']),
                "medium_issues": len([i for i in filtered_issues if i.get('severity') == 'medium']),
                "low_issues": len([i for i in filtered_issues if i.get('severity') == 'low']),
                "language": self.language,
                "security_tools": self.security_tools,
                "severity_threshold": self.severity_threshold,
                "issue_details": filtered_issues
            }
            
            if filtered_issues:
                critical_count = attempt.metadata["critical_issues"]
                high_count = attempt.metadata["high_issues"]
                attempt.message = f"Found {len(filtered_issues)} security issues ({critical_count} critical, {high_count} high)"
            else:
                attempt.message = f"No security issues found above {self.severity_threshold} threshold"
                
        except Exception as e:
            attempt.end_time = datetime.now()
            attempt.output = f"Error during security check: {str(e)}"
            attempt.message = f"Security check failed: {str(e)}"
            attempt.metadata = {"error": str(e)}
        
        return attempt
    
    def validate(self, attempt: TestAttempt) -> bool:
        """Validate security check results.
        
        Args:
            attempt: Test attempt to validate
            
        Returns:
            bool: True if no critical security issues found, False otherwise
        """
        # TODO: Implement more sophisticated validation logic
        # - Configurable severity thresholds for pass/fail
        # - Allow certain number of low/medium issues
        # - Integration with security policy requirements
        # - Support for security exception handling
        
        if "error" in attempt.metadata:
            return False
        
        # Check for critical and high severity issues
        critical_issues = attempt.metadata.get("critical_issues", 0)
        high_issues = attempt.metadata.get("high_issues", 0)
        
        # Fail if any critical issues found
        if critical_issues > 0:
            return False
        
        # Fail if high issues found and threshold is high or critical
        if high_issues > 0 and self.severity_threshold in ["high", "critical"]:
            return False
        
        return True
    
    def _discover_files(self, project_path: str, exclude_patterns: List[str], 
                       include_patterns: List[str]) -> List[str]:
        """Discover files to security check in the project.
        
        Args:
            project_path: Path to project directory
            exclude_patterns: Patterns to exclude
            include_patterns: Patterns to include
            
        Returns:
            List of file paths to check
        """
        # TODO: Implement comprehensive file discovery
        # - Support for multiple file types per language
        # - Include configuration files (requirements.txt, package.json)
        # - Scan for secrets in various file types
        # - Handle binary files appropriately
        
        project_dir = Path(project_path)
        files = []
        
        # Language-specific file patterns
        if self.language == "python":
            patterns = ["*.py", "requirements*.txt", "setup.py", "pyproject.toml"]
        elif self.language == "javascript":
            patterns = ["*.js", "*.ts", "*.jsx", "*.tsx", "package.json", "package-lock.json"]
        elif self.language == "java":
            patterns = ["*.java", "*.xml", "pom.xml", "build.gradle"]
        else:
            patterns = ["*.*"]  # Scan all files for generic tools
        
        for pattern in patterns:
            for file_path in project_dir.rglob(pattern):
                file_str = str(file_path)
                # Basic exclude pattern check
                if not any(exclude_pattern in file_str for exclude_pattern in exclude_patterns):
                    files.append(file_str)
        
        return files
    
    def _run_security_tool(self, tool: str, project_path: str, 
                          config_file: Optional[str] = None,
                          custom_rules: Optional[str] = None) -> List[Dict[str, Any]]:
        """Run a specific security tool.
        
        Args:
            tool: Name of the security tool
            project_path: Path to project directory
            config_file: Optional config file path
            custom_rules: Optional custom rules path
            
        Returns:
            List of security issues found by the tool
        """
        if tool == "bandit":
            return self._run_bandit(project_path, config_file)
        elif tool == "safety":
            return self._run_safety(project_path)
        elif tool == "semgrep":
            return self._run_semgrep(project_path, custom_rules)
        else:
            # TODO: Add support for more security tools
            # - ESLint security plugin
            # - npm audit
            # - SpotBugs for Java
            # - Brakeman for Ruby
            # - gosec for Go
            # - Custom security scanners
            raise ValueError(f"Unsupported security tool: {tool}")
    
    def _run_bandit(self, project_path: str, config_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """Run Bandit security scanner for Python.
        
        Args:
            project_path: Path to project directory
            config_file: Optional bandit config file
            
        Returns:
            List of bandit security issues
        """
        # TODO: Implement actual bandit execution
        # - Build proper bandit command with all options
        # - Parse bandit JSON output
        # - Handle bandit configuration files
        # - Support for custom bandit rules
        
        cmd = ["bandit", "-r", project_path, "-f", "json"]
        
        if config_file:
            cmd.extend(["-c", config_file])
        
        # Add severity level filtering
        cmd.extend(["-ll"])  # Low level and above
        
        # Mock implementation - replace with actual subprocess call
        # result = subprocess.run(cmd, capture_output=True, text=True)
        # return self._parse_bandit_output(result.stdout)
        
        # Placeholder return
        return []
    
    def _run_safety(self, project_path: str) -> List[Dict[str, Any]]:
        """Run Safety scanner for Python dependencies.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            List of safety security issues
        """
        # TODO: Implement actual safety execution
        # - Check requirements files for vulnerable packages
        # - Parse safety JSON output
        # - Handle different requirements file formats
        # - Support for safety policy files
        
        cmd = ["safety", "check", "--json"]
        
        # Look for requirements files
        requirements_files = [
            "requirements.txt", "requirements-dev.txt", 
            "requirements-test.txt", "dev-requirements.txt"
        ]
        
        for req_file in requirements_files:
            req_path = Path(project_path) / req_file
            if req_path.exists():
                cmd.extend(["-r", str(req_path)])
                break
        
        # Mock implementation - replace with actual subprocess call
        # result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_path)
        # return self._parse_safety_output(result.stdout)
        
        # Placeholder return
        return []
    
    def _run_semgrep(self, project_path: str, custom_rules: Optional[str] = None) -> List[Dict[str, Any]]:
        """Run Semgrep security scanner.
        
        Args:
            project_path: Path to project directory
            custom_rules: Optional custom rules path
            
        Returns:
            List of semgrep security issues
        """
        # TODO: Implement actual semgrep execution
        # - Build proper semgrep command
        # - Parse semgrep JSON output
        # - Handle semgrep rule configurations
        # - Support for custom semgrep rules
        
        cmd = ["semgrep", "--config=auto", "--json", project_path]
        
        if custom_rules:
            cmd.extend(["--config", custom_rules])
        
        # Mock implementation - replace with actual subprocess call
        # result = subprocess.run(cmd, capture_output=True, text=True)
        # return self._parse_semgrep_output(result.stdout)
        
        # Placeholder return
        return []
    
    def _filter_by_severity(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter security issues by severity threshold.
        
        Args:
            issues: List of all security issues
            
        Returns:
            List of filtered issues
        """
        if not self.severity_threshold or self.severity_threshold not in self.severity_levels:
            return issues
        
        threshold_index = self.severity_levels.index(self.severity_threshold)
        filtered_issues = []
        
        for issue in issues:
            issue_severity = issue.get('severity', 'low').lower()
            if issue_severity in self.severity_levels:
                issue_index = self.severity_levels.index(issue_severity)
                if issue_index >= threshold_index:
                    filtered_issues.append(issue)
            else:
                # Include unknown severity issues
                filtered_issues.append(issue)
        
        return filtered_issues
    
    def _format_output(self, total_files: int, security_issues: List[Dict[str, Any]]) -> str:
        """Format test output for display.
        
        Args:
            total_files: Total number of files checked
            security_issues: List of security issues found
            
        Returns:
            Formatted output string
        """
        output_lines = [
            f"Security Check Results ({self.language})",
            f"Tools used: {', '.join(self.security_tools)}",
            f"Files checked: {total_files}",
            f"Issues found: {len(security_issues)}",
            f"Severity threshold: {self.severity_threshold}",
            ""
        ]
        
        if security_issues:
            # Group by severity
            by_severity = {}
            for issue in security_issues:
                severity = issue.get('severity', 'unknown')
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(issue)
            
            output_lines.append("Security Issues by Severity:")
            for severity in ["critical", "high", "medium", "low", "unknown"]:
                if severity in by_severity:
                    output_lines.append(f"\n{severity.upper()} ({len(by_severity[severity])} issues):")
                    for issue in by_severity[severity][:5]:  # Show first 5 per severity
                        line_info = f":{issue['line']}" if issue.get('line', 0) > 0 else ""
                        rule_info = f" [{issue['rule_id']}]" if issue.get('rule_id') else ""
                        tool_info = f" ({issue['tool']})" if issue.get('tool') else ""
                        output_lines.append(
                            f"  {issue['file']}{line_info} - {issue['message']}{rule_info}{tool_info}"
                        )
                    if len(by_severity[severity]) > 5:
                        output_lines.append(f"  ... and {len(by_severity[severity]) - 5} more")
        else:
            output_lines.append("✓ No security issues found")
        
        return "\n".join(output_lines)
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get summary of security issues.
        
        Returns:
            Dictionary with security summary statistics
        """
        if not self.security_issues:
            return {"total_issues": 0, "files_with_issues": 0}
        
        files_with_issues = set(issue['file'] for issue in self.security_issues)
        rule_counts = {}
        tool_counts = {}
        severity_counts = {}
        
        for issue in self.security_issues:
            # Count rules
            rule_id = issue.get('rule_id', 'unknown')
            rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1
            
            # Count tools
            tool = issue.get('tool', 'unknown')
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
            
            # Count severity levels
            severity = issue.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_issues": len(self.security_issues),
            "files_with_issues": len(files_with_issues),
            "rule_counts": rule_counts,
            "tool_counts": tool_counts,
            "severity_counts": severity_counts,
            "affected_files": list(files_with_issues),
            "security_tools": self.security_tools,
            "severity_threshold": self.severity_threshold
        }