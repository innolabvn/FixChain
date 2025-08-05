"""Semgrep Security Scanner Integration

This module provides integration with Semgrep for security vulnerability scanning
across multiple programming languages and frameworks.
"""

import json
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import requests
import glob
import os

logger = logging.getLogger(__name__)


class SemgrepScanner:
    """Semgrep security scanner integration."""
    
    def __init__(self, 
                 config: str = "auto",
                 severity_threshold: str = "medium",
                 max_target_bytes: Optional[int] = None,
                 timeout: int = 300):
        """
        Initialize Semgrep scanner.
        
        Args:
            config: Semgrep configuration (auto, p/security-audit, etc.)
            severity_threshold: Minimum severity to report (low, medium, high, critical)
            max_target_bytes: Maximum file size to scan
            timeout: Timeout in seconds for semgrep execution
        """
        self.config = config
        self.severity_threshold = severity_threshold.lower()
        self.max_target_bytes = max_target_bytes
        self.timeout = timeout
        self.severity_levels = ["low", "medium", "high", "critical"]
        
    def scan_directory(self, 
                      target_path: str,
                      exclude_patterns: Optional[List[str]] = None,
                      include_patterns: Optional[List[str]] = None,
                      custom_rules: Optional[str] = None) -> Dict[str, Any]:
        """
        Scan a directory for security vulnerabilities.
        
        Args:
            target_path: Path to directory to scan
            exclude_patterns: Patterns to exclude from scanning
            include_patterns: Patterns to include in scanning
            custom_rules: Path to custom semgrep rules
            
        Returns:
            Dictionary containing scan results
        """
        if not Path(target_path).exists():
            return {
                "success": False,
                "error": f"Target path does not exist: {target_path}",
                "issues": [],
                "summary": {}
            }
        
        try:
            # Build semgrep command
            cmd = self._build_semgrep_command(
                target_path=target_path,
                exclude_patterns=exclude_patterns,
                include_patterns=include_patterns,
                custom_rules=custom_rules
            )
            
            logger.info(f"Running semgrep: {' '.join(cmd)}")
            print(f"DEBUG: Scanning target path: {target_path}")
            print(f"DEBUG: Semgrep command: {' '.join(cmd)}")
            print(f"DEBUG: Exclude patterns: {exclude_patterns}")
            
            # Execute semgrep with environment variable
            import os
            env = os.environ.copy()
            env['PYTHONHTTPSVERIFY'] = '0'
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=self.timeout,
                env=env
            )
            
            print(f"DEBUG: Semgrep return code: {result.returncode}")
            print(f"DEBUG: Semgrep stdout length: {len(result.stdout)}")
            print(f"DEBUG: Semgrep stderr: {result.stderr[:500]}")
            print(f"DEBUG: Semgrep stdout content: {result.stdout[:1000]}")
            
            if result.returncode == 0 or result.returncode == 1:
                # Parse successful output (0 = no findings, 1 = findings detected)
                return self._parse_semgrep_output(result.stdout, target_path)
            else:
                # Handle semgrep errors
                return self._handle_semgrep_error(result.stderr, result.returncode)
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Semgrep scan timed out after {self.timeout} seconds",
                "issues": [],
                "summary": {}
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Semgrep scan failed: {str(e)}",
                "issues": [],
                "summary": {}
            }
    
    def scan_file(self, 
                  file_path: str,
                  custom_rules: Optional[str] = None) -> Dict[str, Any]:
        """
        Scan a single file for security vulnerabilities.
        
        Args:
            file_path: Path to file to scan
            custom_rules: Path to custom semgrep rules
            
        Returns:
            Dictionary containing scan results
        """
        return self.scan_directory(
            target_path=file_path,
            custom_rules=custom_rules
        )
    
    def _build_semgrep_command(self, 
                                 target_path: str,
                                 exclude_patterns: Optional[List[str]] = None,
                                 include_patterns: Optional[List[str]] = None,
                                 custom_rules: Optional[str] = None) -> List[str]:
        """Build semgrep command with all options."""
        command = [
            "semgrep",
            "--disable-version-check",
            "--no-rewrite-rule-ids",
            "--no-git-ignore",
            "--json",
        ]
        
        # Add configuration
        if custom_rules:
            # Check if custom_rules is a directory or file
            if os.path.isdir(custom_rules):
                # Load all YAML files from the directory
                rule_files = glob.glob(os.path.join(custom_rules, "*.yml")) + glob.glob(os.path.join(custom_rules, "*.yaml"))
                if not rule_files:
                    raise RuntimeError(f"No YAML rules found in {custom_rules}")
                print(f"DEBUG: Loading rule files: {rule_files}")
                for rule_file in rule_files:
                    command.extend(["--config", rule_file])
            else:
                # Single rule file
                command.extend(["--config", custom_rules])
        elif self.config != "auto":
            command.extend(["--config", self.config])
        else:
            # Auto-load all YAML rules from semgrep_rules directory
            rules_dir = os.path.join(os.path.dirname(__file__), "semgrep_rules")
            rule_files = glob.glob(os.path.join(rules_dir, "*.yml")) + glob.glob(os.path.join(rules_dir, "*.yaml"))
            if not rule_files:
                raise RuntimeError(f"No YAML rules found in {rules_dir}")
            for rule_file in rule_files:
                command.extend(["--config", rule_file])
        
        # Add exclude patterns
        if exclude_patterns:
            for pattern in exclude_patterns:
                command.extend(["--exclude", pattern])
        
        # Add include patterns
        if include_patterns:
            for pattern in include_patterns:
                command.extend(["--include", pattern])
        
        # Add max target bytes if specified
        if self.max_target_bytes:
            command.extend(["--max-target-bytes", str(self.max_target_bytes)])
        
        # Add target path
        command.append(target_path)
        
        return command
    
    def _parse_semgrep_output(self, output: str, target_path: str) -> Dict[str, Any]:
        """Parse semgrep JSON output."""
        try:
            data = json.loads(output)
            
            # Extract results
            results = data.get("results", [])
            
            # Filter by severity
            filtered_results = self._filter_by_severity(results)
            
            # Convert to standardized format
            issues = []
            for result in filtered_results:
                issue = self._convert_semgrep_result(result)
                issues.append(issue)
            
            # Generate summary
            summary = self._generate_summary(issues, target_path)
            
            return {
                "success": True,
                "issues": issues,
                "summary": summary,
                "raw_output": data
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse semgrep JSON output: {str(e)}",
                "issues": [],
                "summary": {}
            }
    
    def _handle_semgrep_error(self, stderr: str, returncode: int) -> Dict[str, Any]:
        """Handle semgrep execution errors."""
        error_msg = f"Semgrep failed with return code {returncode}"
        if stderr:
            error_msg += f": {stderr.strip()}"
        
        return {
            "success": False,
            "error": error_msg,
            "issues": [],
            "summary": {}
        }
    
    def _filter_by_severity(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter results by severity threshold."""
        if not self.severity_threshold or self.severity_threshold not in self.severity_levels:
            return results
        
        threshold_index = self.severity_levels.index(self.severity_threshold)
        filtered_results = []
        
        # Map semgrep severity to our levels
        severity_mapping = {
            "info": "low",
            "warning": "medium", 
            "error": "high"
        }
        
        for result in results:
            raw_severity = result.get("extra", {}).get("severity", "low").lower()
            # Map semgrep severity to our standard levels
            severity = severity_mapping.get(raw_severity, raw_severity)
            
            if severity in self.severity_levels:
                severity_index = self.severity_levels.index(severity)
                if severity_index >= threshold_index:
                    filtered_results.append(result)
            else:
                # Include unknown severity results
                filtered_results.append(result)
        
        return filtered_results
    
    def _convert_semgrep_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert semgrep result to standardized format."""
        extra = result.get("extra", {})
        
        # Map semgrep severity to our standard levels
        severity_mapping = {
            "info": "low",
            "warning": "medium", 
            "error": "high"
        }
        raw_severity = extra.get("severity", "low").lower()
        severity = severity_mapping.get(raw_severity, raw_severity)
        
        return {
            "file": result.get("path", ""),
            "line": result.get("start", {}).get("line", 0),
            "column": result.get("start", {}).get("col", 0),
            "end_line": result.get("end", {}).get("line", 0),
            "end_column": result.get("end", {}).get("col", 0),
            "message": extra.get("message", ""),
            "severity": severity,
            "rule_id": result.get("check_id", ""),
            "tool": "semgrep",
            "confidence": extra.get("confidence", "medium"),
            "metadata": {
                "rule_url": extra.get("metadata", {}).get("source", ""),
                "category": extra.get("metadata", {}).get("category", ""),
                "cwe": extra.get("metadata", {}).get("cwe", []),
                "owasp": extra.get("metadata", {}).get("owasp", [])
            }
        }
    
    def _generate_summary(self, issues: List[Dict[str, Any]], target_path: str) -> Dict[str, Any]:
        """Generate summary statistics."""
        by_severity = {}
        by_file = {}
        
        for issue in issues:
            severity = issue.get("severity", "unknown")
            file_path = issue.get("file", "")
            
            if severity not in by_severity:
                by_severity[severity] = 0
            by_severity[severity] += 1
            
            if file_path not in by_file:
                by_file[file_path] = 0
            by_file[file_path] += 1
        
        return {
            "total_issues": len(issues),
            "files_with_issues": len(by_file),
            "by_severity": by_severity,
            "by_file": by_file,
            "target_path": target_path,
            "scan_time": datetime.now().isoformat()
        }


def convert_semgrep_issue_to_bug(issue: dict) -> dict:
    """
    Convert a semgrep issue to the bug schema for API import.
    """
    return {
        "source_file": issue.get("file", ""),
        "bug_type": "security",  # Có thể map động nếu cần
        "severity": issue.get("severity", "medium"),
        "line_number": issue.get("line", 0),
        "column_number": issue.get("column", None),
        "description": issue.get("message", ""),
        "code_snippet": "",  # Sẽ lấy ở bước sau
        "suggested_fix": None,
        "actual_fix": None,
        "detection_method": "static_analysis",
        "ai_confidence": None,
        "detection_iteration": None,
        "fix_iteration": None,
        "status": "detected",
        "human_feedback": None,
        "related_bugs": [],
        "fix_impact": None
    }

def post_bugs_to_api(bugs: list, base_url: str = "http://localhost:8000/api/fixchain/import/bulk"):
    """
    Gửi batch bug lên API endpoint /bugs/import
    """
    url = "http://192.168.1.9:5000/api/fixchain/import/bulk"
    payload = {
        "data": {
            "bugs": bugs,
        },
        "metadata": {
            "source": "semgrep_scan",
            "import_date": datetime.now().isoformat(),
            "imported_by": "fixchain",
            "notes": "Auto import from semgrep scan"
        }
    }
    # Log payload trước khi gửi
    print("==== JSON BUG PAYLOAD SẼ GỬI LÊN API ====")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("==== END JSON BUG PAYLOAD ====")
    try:
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            print(f"✅ Imported {len(bugs)} bugs to API successfully!")
        else:
            print(f"❌ Failed to import bugs! Status: {resp.status_code}, Response: {resp.text}")
    except Exception as e:
        print(f"❌ Exception when importing bugs: {e}")


def scan_src_test_directory(src_test_path: str = "src_test",
                           config: str = "auto",
                           severity_threshold: str = "medium",
                           exclude_patterns: Optional[List[str]] = None,
                           custom_rules: Optional[str] = None,
                           post_to_api: bool = False,
                           api_base_url: str = "http://localhost:8000/api/v1") -> Dict[str, Any]:
    """
    Scan the src_test directory for security vulnerabilities.
    Optionally, post results to API.
    """
    scanner = SemgrepScanner(
        config=config,
        severity_threshold=severity_threshold
    )
    if exclude_patterns is None:
        exclude_patterns = [
            # "**/node_modules/**",
            # "**/.git/**", 
            # "**/__pycache__/**",
            # "**/*.pyc",
            # "**/.venv/**",
            # "**/venv/**",
            # "**/dist/**",
            # "**/build/**"
        ]
    result = scanner.scan_directory(
        target_path=src_test_path,
        exclude_patterns=exclude_patterns,
        custom_rules=custom_rules
    )
    # Convert and post to API if needed
    if post_to_api and result.get("success") and result.get("issues"):
        bugs = [convert_semgrep_issue_to_bug(issue) for issue in result["issues"]]
        post_bugs_to_api(bugs, base_url=api_base_url)
    return result