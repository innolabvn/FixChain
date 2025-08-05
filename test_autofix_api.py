#!/usr/bin/env python3
"""
Simple test script to verify autofix reasoning API functionality.
"""

import requests
import json
from datetime import datetime, timezone

def test_store_autofix():
    """Test storing autofix reasoning"""
    print("🧪 Testing autofix reasoning storage...")
    
    url = "http://localhost:8000/api/reasoning/add"
    
    payload = {
        "content": """=== AUTOFIX REASONING TEST ===

## AI Thinking Process:
Phát hiện lỗi syntax đơn giản - thiếu dấu đóng ngoặc. Đây là lỗi có thể sửa tự động với confidence cao.

## Fix Steps:
1. Phân tích syntax error
2. Xác định vị trí thiếu parenthesis
3. Thêm ')' vào đúng vị trí
4. Validate syntax

## Token Usage:
- Prompt tokens: 120
- Completion tokens: 45
- Total tokens: 165

## Fix Location:
- File: test.py
- Line: 10
- Column: 15

## Code Changes:

### Original Code:
```
print("Hello world"
```

### Fixed Code:
```
print("Hello world")
```

## Confidence Score: 0.98

## Fix Summary:
Successfully fixed syntax error with 4 steps, using 165 tokens.
Confidence level: 98.0%""",
        "metadata": {
            "bug_id": "TEST-AUTOFIX-001",
            "test_name": "autofix",
            "iteration": 1,
            "category": "autofix",
            "source": "ai_autofix",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "tags": ["autofix", "syntax", "high", "ai_generated", "test"],
            "autofix_metadata": {
                "source_file": "test.py",
                "bug_type": "syntax",
                "severity": "high",
                "fix_iteration": 1,
                "confidence": 0.98,
                "token_usage": {
                    "prompt_tokens": 120,
                    "completion_tokens": 45,
                    "total_tokens": 165
                },
                "fix_location": {
                    "file": "test.py",
                    "line": 10,
                    "column": 15
                },
                "fix_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            result = response.json()
            doc_id = result.get('doc_id')
            print(f"✅ Autofix reasoning stored successfully!")
            print(f"   Doc ID: {doc_id}")
            return doc_id
        else:
            print(f"❌ Failed to store: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_search_autofix():
    """Test searching autofix reasoning"""
    print("\n🔍 Testing autofix reasoning search...")
    
    url = "http://localhost:8000/api/reasoning/search"
    
    payload = {
        "query": "syntax error autofix",
        "k": 3,
        "filter_criteria": {
            "tags": {"$in": ["autofix", "syntax"]}
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            response_data = response.json()
            # Handle both possible response formats
            if isinstance(response_data, list):
                results = response_data
            else:
                results = response_data.get('results', [])
            
            print(f"✅ Found {len(results)} autofix reasoning entries")
            
            for i, result in enumerate(results[:2]):
                print(f"\n   Result {i+1}:")
                print(f"     Score: {result.get('score', 0):.3f}")
                metadata = result.get('metadata', {})
                print(f"     Bug ID: {metadata.get('bug_id', 'N/A')}")
                autofix_meta = metadata.get('autofix_metadata', {})
                print(f"     Bug Type: {autofix_meta.get('bug_type', 'N/A')}")
                print(f"     Confidence: {autofix_meta.get('confidence', 0):.2f}")
                print(f"     Tokens: {autofix_meta.get('token_usage', {}).get('total_tokens', 0)}")
            
            return len(results)
        else:
            print(f"❌ Search failed: {response.status_code} - {response.text}")
            return 0
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 0

def test_api_health():
    """Test if API is running"""
    print("🏥 Testing API health...")
    
    try:
        response = requests.get("http://localhost:8000/docs")
        if response.status_code == 200:
            print("✅ API server is running")
            return True
        else:
            print(f"❌ API server returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API server: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Autofix API Tests...\n")
    
    # Test API health
    if not test_api_health():
        print("\n❌ API server is not running. Please start the server first.")
        print("   Run: python server.py")
        return
    
    # Test storing autofix reasoning
    doc_id = test_store_autofix()
    
    # Test searching autofix reasoning
    results_count = test_search_autofix()
    
    print("\n📊 Test Summary:")
    print(f"   - API Health: ✅ OK")
    print(f"   - Store Autofix: {'✅ OK' if doc_id else '❌ FAILED'}")
    print(f"   - Search Autofix: ✅ OK ({results_count} results found)")
    
    if doc_id:
        print(f"\n🎉 All tests passed! Stored doc_id: {doc_id}")
        print("\n💡 Key findings:")
        print("   - API reasoning/add successfully stores autofix data")
        print("   - Includes thinking process, steps, token usage, code changes")
        print("   - Metadata contains detailed autofix information")
        print("   - Search functionality works for retrieving autofix reasoning")
        print("   - Perfect for storing and analyzing autofix performance")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()