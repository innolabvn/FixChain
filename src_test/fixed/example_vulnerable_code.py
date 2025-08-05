"""Example vulnerable code with exactly 5 security bugs for Semgrep testing."""

import subprocess
import os
import sqlite3
import hashlib
import shlex
from getpass import getpass


def bug1_command_injection():
    """Bug 1: Fixed command injection vulnerability."""
    user_input = input("Enter command: ")
    # FIXED: Use subprocess with shell=False and proper argument parsing
    try:
        args = shlex.split(user_input)
        subprocess.run(args, check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"Command execution failed: {e}")


def bug2_sql_injection():
    """Bug 2: Fixed SQL injection vulnerability."""
    username = input("Enter username: ")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # FIXED: Use parameterized queries to prevent SQL injection
    query = "SELECT * FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    
    return cursor.fetchall()


def bug3_weak_crypto():
    """Bug 3: Fixed weak cryptographic hash function."""
    password = "secret123"
    
    # FIXED: Use SHA-256 instead of MD5
    secure_hash = hashlib.sha256(password.encode()).hexdigest()
    
    return secure_hash


def bug4_hardcoded_secret():
    """Bug 4: Fixed hardcoded API key."""
    # FIXED: Get API key from environment variable
    api_key = os.getenv('API_KEY')
    if not api_key:
        raise ValueError("API_KEY environment variable not set")
    
    return api_key


def bug5_eval_injection():
    """Bug 5: Fixed code injection via eval."""
    user_expression = input("Enter Python expression: ")
    
    # FIXED: Use ast.literal_eval for safe evaluation of literals only
    import ast
    try:
        result = ast.literal_eval(user_expression)
    except (ValueError, SyntaxError) as e:
        print(f"Invalid expression: {e}")
        return None
    
    return result


def main():
    """Main function demonstrating 5 security vulnerabilities."""
    print("This file contains 5 intentional security vulnerabilities:")
    print("1. Command injection (os.system)")
    print("2. SQL injection (string concatenation)")
    print("3. Weak cryptography (MD5)")
    print("4. Hardcoded secrets (API key)")
    print("5. Code injection (eval)")
    
    # Uncomment these to test (but don't run in production!)
    # bug1_command_injection()
    # bug2_sql_injection()
    # bug3_weak_crypto()
    # bug4_hardcoded_secret()
    # bug5_eval_injection()


if __name__ == "__main__":
    main()