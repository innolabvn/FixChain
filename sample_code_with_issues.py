"""Sample Python code with various issues for testing FixChain test suite.

This file intentionally contains syntax errors, type issues, and security
vulnerabilities to demonstrate the capabilities of the FixChain test suite.
"""

import os
import subprocess
import hashlib
from typing import List, Optional

# Security Issue: Hardcoded password
DATABASE_PASSWORD = "super_secret_password_123"
API_KEY = "sk-1234567890abcdef"

# TODO: Fix the syntax error below
def broken_function(
    """This function has a syntax error - missing closing parenthesis."""
    print("This will cause a syntax error")
    return "error"

# Type annotation issues
def process_data(data):
    """Process data without proper type hints."""
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

def calculate_average(numbers: List[int]) -> float:
    """Calculate average with potential type issues."""
    if not numbers:
        return None  # Type issue: should return float, not None
    
    total = sum(numbers)
    return total / len(numbers)

# Security Issue: Command injection vulnerability
def execute_user_command(user_input: str) -> str:
    """Execute user command - DANGEROUS!"""
    # Shell injection vulnerability
    result = os.system("ls " + user_input)
    return str(result)

# Security Issue: Use of eval
def evaluate_expression(expression: str):
    """Evaluate mathematical expression - DANGEROUS!"""
    # Dangerous use of eval
    return eval(expression)

# Security Issue: Weak cryptographic hash
def hash_password(password: str) -> str:
    """Hash password using weak algorithm."""
    # Weak hash function
    return hashlib.md5(password.encode()).hexdigest()

# Security Issue: SQL injection potential
def get_user_data(user_id: str) -> str:
    """Get user data from database - potential SQL injection."""
    query = "SELECT * FROM users WHERE id = '%s'" % user_id
    # This would be executed with a database connection
    return query

# FIXME: This function needs proper error handling
def divide_numbers(a: int, b: int) -> float:
    """Divide two numbers without error handling."""
    return a / b  # Division by zero not handled

# Type issue: inconsistent return types
def get_config_value(key: str) -> str:
    """Get configuration value."""
    config = {
        "debug": True,  # Should be string according to return type
        "host": "localhost",
        "port": 8080  # Should be string according to return type
    }
    return config.get(key, "default")

# Security Issue: Debug mode enabled
DEBUG = True

class DataProcessor:
    """Data processor with various issues."""
    
    def __init__(self, data):
        """Initialize without type hints."""
        self.data = data
        self.processed = False
    
    def process(self) -> List:
        """Process data with incomplete type hint."""
        if not self.data:
            return None  # Type inconsistency
        
        # TODO: Implement proper data validation
        processed_data = []
        for item in self.data:
            if isinstance(item, str):
                processed_data.append(item.upper())
            elif isinstance(item, (int, float)):
                processed_data.append(item * 2)
        
        self.processed = True
        return processed_data
    
    def save_to_file(self, filename: str) -> None:
        """Save processed data to file."""
        if not self.processed:
            raise ValueError("Data not processed yet")
        
        # Security issue: potential path traversal
        with open(filename, 'w') as f:
            for item in self.data:
                f.write(f"{item}\n")

# NotImplementedError for testing
def future_feature():
    """A feature to be implemented in the future."""
    raise NotImplementedError("This feature is not yet implemented")

# Main execution
if __name__ == "__main__":
    # Test the functions (some will fail)
    try:
        data = [1, 2, 3, "hello", 4.5]
        processor = DataProcessor(data)
        result = processor.process()
        print(f"Processed data: {result}")
        
        # This will cause issues
        avg = calculate_average([1, 2, 3])
        print(f"Average: {avg}")
        
        # Dangerous operations (commented out for safety)
        # execute_user_command("../../../etc/passwd")
        # evaluate_expression("__import__('os').system('rm -rf /')")
        
    except Exception as e:
        print(f"Error occurred: {e}")