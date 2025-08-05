"""Example vulnerable code with exactly 5 security bugs for Semgrep testing."""

import subprocess
import os
import sqlite3
import hashlib


def bug1_command_injection():
    """Bug 1: Command injection vulnerability."""
    user_input = input("Enter command: ")
    # VULNERABILITY: Shell injection via os.system with user input
    os.system(user_input)


def bug2_sql_injection():
    """Bug 2: SQL injection vulnerability."""
    username = input("Enter username: ")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # VULNERABILITY: SQL injection via string concatenation
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    
    return cursor.fetchall()


def bug3_weak_crypto():
    """Bug 3: Weak cryptographic hash function."""
    password = "secret123"
    
    # VULNERABILITY: MD5 is cryptographically broken
    weak_hash = hashlib.md5(password.encode()).hexdigest()
    
    return weak_hash


def bug4_hardcoded_secret():
    """Bug 4: Hardcoded API key."""
    # VULNERABILITY: Hardcoded API key in source code
    api_key = "sk-1234567890abcdef"
    
    return api_key


def bug5_eval_injection():
    """Bug 5: Code injection via eval."""
    user_expression = input("Enter Python expression: ")
    
    # VULNERABILITY: eval() with user input allows code injection
    result = eval(user_expression)
    
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