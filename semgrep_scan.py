#!/usr/bin/env python3
"""Semgrep Scanner for src_test Directory

This script provides a command-line interface to scan the src_test directory
for security vulnerabilities using Semgrep.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional, List

from testsuite.static_tests.semgrep_scanner import scan_src_test_directory, SemgrepScanner


def print_scan_results(results: dict, verbose: bool = False) -> None:
    """Print scan results in a formatted way."""
    if not results["success"]:
        print(f"âŒ Scan failed: {results.get('error', 'Unknown error')}")
        return
    
    summary = results["summary"]
    issues = results["issues"]
    
    print(f"\n - Semgrep Security Scan Results")
    print(f"- Target: {summary.get('target_path', 'Unknown')}")
    print(f"- Total Issues: {summary.get('total_issues', 0)}")
    print(f"- Files with Issues: {summary.get('files_with_issues', 0)}")
    print(f"- Scan Time: {summary.get('scan_time', 'Unknown')}")
    
    # Print severity breakdown
    by_severity = summary.get('by_severity', {})
    if by_severity:
        print(f"\n - Issues by Severity:")
        for severity in ['critical', 'high', 'medium', 'low']:
            count = by_severity.get(severity, 0)
            if count > 0:
                icon = "-" if severity in ['critical', 'high'] else "-" if severity == 'medium' else "-"
                print(f"  {icon} {severity.upper()}: {count}")
    
    # Print detailed issues if verbose or if there are issues
    if issues and (verbose or len(issues) <= 10):
        print(f"\n - Detailed Issues:")
        for i, issue in enumerate(issues[:20], 1):  # Show max 20 issues
            severity = issue.get('severity', 'unknown')
            icon = "-" if severity in ['critical', 'high'] else "-" if severity == 'medium' else "-"
            
            print(f"\n{i}. {icon} {severity.upper()} - {issue.get('file', 'Unknown file')}")
            print(f"   - Line {issue.get('line', 0)}: {issue.get('message', 'No message')}")
            print(f"   - Rule: {issue.get('rule_id', 'Unknown rule')}") 
            
            # Show metadata if available
            metadata = issue.get('metadata', {})
            if metadata.get('cwe'):
                print(f"   - CWE: {', '.join(metadata['cwe'])}")
            if metadata.get('category'):
                print(f"   - Category: {metadata['category']}")
    
    elif issues and not verbose:
        print(f"\n - Use --verbose to see detailed issue information") 
    
    if not issues:
        print(f"\n - No security issues found!")
    
    print(f"\n" + "="*50)


def main():
    """Main command line interface."""
    parser = argparse.ArgumentParser(
        description="Scan src_test directory for security vulnerabilities using Semgrep",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python semgrep_scan.py                           # Basic scan
  python semgrep_scan.py --verbose                 # Detailed output
  python semgrep_scan.py --severity high           # Only high/critical issues
  python semgrep_scan.py --config p/security-audit # Use security audit rules
  python semgrep_scan.py --output results.json     # Save results to file
        """
    )
    
    parser.add_argument(
        "--src-test-path",
        default="src_test",
        help="Path to src_test directory (default: src_test)"
    )
    
    parser.add_argument(
        "--config",
        default="auto",
        help="Semgrep configuration (auto, p/security-audit, etc.)"
    )
    
    parser.add_argument(
        "--severity",
        choices=["low", "medium", "high", "critical"],
        default="medium",
        help="Minimum severity to report (default: medium)"
    )
    
    parser.add_argument(
        "--custom-rules",
        help="Path to custom semgrep rules file"
    )
    
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=[],
        help="Patterns to exclude from scanning"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed issue information"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Save results to JSON file"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds for semgrep execution (default: 300)"
    )
    
    parser.add_argument(
        "--post-to-api",
        action="store_true",
        help="Post bugs to API endpoint after scan"
    )
    parser.add_argument(
        "--api-base-url",
        default="http://localhost:8000/api/v1",
        help="Base URL for bug import API (default: http://localhost:8000/api/v1)"
    )
    parser.add_argument('--disable-ssl', 
        action='store_true',
        help='Disable SSL certificate verification')
    
    args = parser.parse_args()
    
    # Handle SSL disable option
    if args.disable_ssl:
        os.environ['PYTHONHTTPSVERIFY'] = '0'
    
    # Check if src_test directory exists
    if not Path(args.src_test_path).exists():
        print(f"- Error: src_test directory not found: {args.src_test_path}")
        print(f"- Create the directory or specify a different path with --src-test-path")
        sys.exit(1)
    
    print(f"- Starting Semgrep security scan...")
    print(f"- Target: {args.src_test_path}")
    print(f"- Config: {args.config}")
    print(f"- Severity: {args.severity}+")
    
    if args.custom_rules:
        print(f"- Custom Rules: {args.custom_rules}")
    
    # Run scan
    try:
        results = scan_src_test_directory(
            src_test_path=args.src_test_path,
            config=args.config,
            severity_threshold=args.severity,
            exclude_patterns=args.exclude,
            custom_rules=args.custom_rules,
            post_to_api=args.post_to_api,
            api_base_url=args.api_base_url
        )
        
        # Print results
        print_scan_results(results, args.verbose)
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"- Results saved to: {args.output}")
        
        # Exit with error code if issues found
        if results["success"] and results["summary"]["total_issues"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print(f"\n - Scan interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"- Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()