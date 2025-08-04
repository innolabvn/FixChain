#!/usr/bin/env python3
"""A clean Python file for testing the FixChain Test Suite."""

import os
import sys
from typing import List, Dict, Optional


def greet(name: str) -> str:
    """Return a greeting message.
    
    Args:
        name: The name to greet
        
    Returns:
        A greeting string
    """
    return f"Hello, {name}!"


def calculate_sum(numbers: List[int]) -> int:
    """Calculate the sum of a list of numbers.
    
    Args:
        numbers: List of integers to sum
        
    Returns:
        The sum of all numbers
    """
    return sum(numbers)


def get_user_info(user_id: int) -> Optional[Dict[str, str]]:
    """Get user information by ID.
    
    Args:
        user_id: The user ID to look up
        
    Returns:
        User information dictionary or None if not found
    """
    # This is a mock implementation
    users = {
        1: {"name": "Alice", "email": "alice@example.com"},
        2: {"name": "Bob", "email": "bob@example.com"}
    }
    return users.get(user_id)


def main() -> None:
    """Main function to demonstrate the clean code."""
    print(greet("World"))
    
    numbers = [1, 2, 3, 4, 5]
    total = calculate_sum(numbers)
    print(f"Sum of {numbers} is {total}")
    
    user = get_user_info(1)
    if user:
        print(f"User: {user['name']} ({user['email']})")
    else:
        print("User not found")


if __name__ == "__main__":
    main()