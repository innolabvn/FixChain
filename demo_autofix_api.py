#!/usr/bin/env python3
"""
Demo script showing how to use the reasoning/add API to store autofix response data.
This script demonstrates the complete workflow of running autofix and storing results in RAG.
"""

import requests
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

class AutofixAPIDemo:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.reasoning_endpoint = f"{base_url}/api/reasoning/add"
        self.search_endpoint = f"{base_url}/api/reasoning/search"
    
    def store_autofix_reasoning(self, 
                              bug_id: str,
                              thinking_process: str,
                              steps: List[str],
                              token_usage: Dict[str, int],
                              fix_location: Dict[str, Any],
                              original_code: str,
                              fixed_code: str,
                              confidence: float,
                              bug_type: str = "unknown",
                              severity: str = "medium",
                              iteration: int = 1) -> Optional[str]:
        """
        Store autofix reasoning data using the reasoning/add API.
        
        Returns:
            doc_id if successful, None if failed
        """
        
        # Format the reasoning content
        steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
        
        content = f"""=== AUTOFIX REASONING ===

## AI Thinking Process:
{thinking_process}

## Fix Steps:
{steps_text}

## Token Usage:
- Prompt tokens: {token_usage.get('prompt_tokens', 0)}
- Completion tokens: {token_usage.get('completion_tokens', 0)}
- Total tokens: {token_usage.get('total_tokens', 0)}

## Fix Location:
- File: {fix_location.get('file', 'unknown')}
- Line: {fix_location.get('line', 0)}
- Column: {fix_location.get('column', 0)}

## Code Changes:

### Original Code:
```
{original_code}
```

### Fixed Code:
```
{fixed_code}
```

## Confidence Score: {confidence}

## Fix Summary:
Successfully applied autofix with {len(steps)} steps, using {token_usage.get('total_tokens', 0)} tokens.
Confidence level: {confidence*100:.1f}%"""
        
        # Prepare metadata
        metadata = {
            "bug_id": bug_id,
            "test_name": "autofix",
            "iteration": iteration,
            "category": "autofix",
            "source": "ai_autofix",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "tags": ["autofix", bug_type, severity, "ai_generated"],
            "autofix_metadata": {
                "source_file": fix_location.get('file', 'unknown'),
                "bug_type": bug_type,
                "severity": severity,
                "fix_iteration": iteration,
                "confidence": confidence,
                "token_usage": token_usage,
                "fix_location": fix_location,
                "fix_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
        }
        
        # Prepare request payload
        payload = {
            "content": content,
            "metadata": metadata
        }
        
        try:
            response = requests.post(
                self.reasoning_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                doc_id = result.get('doc_id')
                print(f"✅ Autofix reasoning stored successfully with doc_id: {doc_id}")
                return doc_id
            else:
                print(f"❌ Failed to store autofix reasoning: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error storing autofix reasoning: {str(e)}")
            return None
    
    def search_autofix_reasoning(self, query: str, k: int = 5, bug_type: Optional[str] = None) -> List[Dict]:
        """
        Search for stored autofix reasoning entries.
        """
        search_payload = {
            "query": query,
            "k": k
        }
        
        if bug_type:
            search_payload["filter_criteria"] = {
                "tags": {"$in": ["autofix", bug_type]}
            }
        
        try:
            response = requests.post(
                self.search_endpoint,
                json=search_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                response_data = response.json()
                # Handle both possible response formats
                if isinstance(response_data, list):
                    results = response_data
                else:
                    results = response_data.get('results', [])
                print(f"🔍 Found {len(results)} autofix reasoning entries")
                return results
            else:
                print(f"❌ Search failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching autofix reasoning: {str(e)}")
            return []

def demo_syntax_error_autofix():
    """Demo: Store autofix reasoning for a syntax error"""
    print("\n=== DEMO: Syntax Error Autofix ===")
    
    api = AutofixAPIDemo()
    
    # Simulate autofix response data
    bug_id = "BUG-SYNTAX-001"
    thinking = "Phát hiện thiếu dấu đóng ngoặc trong function call. Cần thêm ')' để hoàn thành syntax. Đây là lỗi cú pháp đơn giản có thể sửa tự động."
    
    steps = [
        "Phân tích syntax error tại line 45",
        "Xác định vị trí thiếu closing parenthesis",
        "Thêm ')' vào cuối expression",
        "Validate syntax sau khi fix"
    ]
    
    token_usage = {
        "prompt_tokens": 150,
        "completion_tokens": 75,
        "total_tokens": 225
    }
    
    fix_location = {
        "file": "src/utils/validator.py",
        "line": 45,
        "column": 25
    }
    
    original_code = """def validate_input(data):
    return len(data > 0"""
    
    fixed_code = """def validate_input(data):
    return len(data) > 0"""
    
    # Store the autofix reasoning
    doc_id = api.store_autofix_reasoning(
        bug_id=bug_id,
        thinking_process=thinking,
        steps=steps,
        token_usage=token_usage,
        fix_location=fix_location,
        original_code=original_code,
        fixed_code=fixed_code,
        confidence=0.95,
        bug_type="syntax",
        severity="high"
    )
    
    return doc_id

def demo_type_error_autofix():
    """Demo: Store autofix reasoning for a type error"""
    print("\n=== DEMO: Type Error Autofix ===")
    
    api = AutofixAPIDemo()
    
    bug_id = "BUG-TYPE-002"
    thinking = "Function expect string parameter nhưng có thể nhận int. Cần thêm type conversion hoặc update type hint để handle cả hai loại. Chọn cách convert to string để đảm bảo compatibility."
    
    steps = [
        "Phân tích type mismatch error",
        "Xác định expected type vs actual type",
        "Thêm str() conversion",
        "Update function để handle multiple types",
        "Test với cả string và int inputs"
    ]
    
    token_usage = {
        "prompt_tokens": 200,
        "completion_tokens": 120,
        "total_tokens": 320
    }
    
    fix_location = {
        "file": "src/models/user.py",
        "line": 28,
        "column": 15
    }
    
    original_code = """def format_user_id(user_id):
    return user_id.upper()"""
    
    fixed_code = """def format_user_id(user_id):
    return str(user_id).upper()"""
    
    doc_id = api.store_autofix_reasoning(
        bug_id=bug_id,
        thinking_process=thinking,
        steps=steps,
        token_usage=token_usage,
        fix_location=fix_location,
        original_code=original_code,
        fixed_code=fixed_code,
        confidence=0.88,
        bug_type="type",
        severity="medium"
    )
    
    return doc_id

def demo_security_issue_autofix():
    """Demo: Store autofix reasoning for a security issue"""
    print("\n=== DEMO: Security Issue Autofix ===")
    
    api = AutofixAPIDemo()
    
    bug_id = "BUG-SEC-003"
    thinking = "Phát hiện SQL injection vulnerability do string concatenation. Cần thay thế bằng parameterized query để prevent injection attacks. Đây là security issue nghiêm trọng cần fix ngay lập tức."
    
    steps = [
        "Phát hiện SQL injection vulnerability",
        "Phân tích cách user input được sử dụng",
        "Thay thế string concatenation bằng parameterized query",
        "Thêm input validation",
        "Test với malicious inputs để verify fix"
    ]
    
    token_usage = {
        "prompt_tokens": 300,
        "completion_tokens": 180,
        "total_tokens": 480
    }
    
    fix_location = {
        "file": "src/database/queries.py",
        "line": 67,
        "column": 20
    }
    
    original_code = """query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)"""
    
    fixed_code = """query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))"""
    
    doc_id = api.store_autofix_reasoning(
        bug_id=bug_id,
        thinking_process=thinking,
        steps=steps,
        token_usage=token_usage,
        fix_location=fix_location,
        original_code=original_code,
        fixed_code=fixed_code,
        confidence=0.92,
        bug_type="security",
        severity="critical",
        iteration=2
    )
    
    return doc_id

def demo_search_autofix_reasoning():
    """Demo: Search for stored autofix reasoning"""
    print("\n=== DEMO: Search Autofix Reasoning ===")
    
    api = AutofixAPIDemo()
    
    # Search for syntax-related autofix
    print("\n🔍 Searching for syntax autofix...")
    results = api.search_autofix_reasoning("syntax error autofix", k=3, bug_type="syntax")
    
    for i, result in enumerate(results[:2]):
        print(f"\nResult {i+1}:")
        print(f"  Doc ID: {result.get('doc_id', 'N/A')}")
        print(f"  Score: {result.get('score', 0):.3f}")
        metadata = result.get('metadata', {})
        autofix_meta = metadata.get('autofix_metadata', {})
        print(f"  Bug ID: {metadata.get('bug_id', 'N/A')}")
        print(f"  Bug Type: {autofix_meta.get('bug_type', 'N/A')}")
        print(f"  Confidence: {autofix_meta.get('confidence', 0):.2f}")
        print(f"  Tokens Used: {autofix_meta.get('token_usage', {}).get('total_tokens', 0)}")
    
    # Search for security-related autofix
    print("\n🔍 Searching for security autofix...")
    results = api.search_autofix_reasoning("SQL injection security fix", k=3, bug_type="security")
    
    for i, result in enumerate(results[:2]):
        print(f"\nResult {i+1}:")
        print(f"  Doc ID: {result.get('doc_id', 'N/A')}")
        print(f"  Score: {result.get('score', 0):.3f}")
        metadata = result.get('metadata', {})
        autofix_meta = metadata.get('autofix_metadata', {})
        print(f"  Bug ID: {metadata.get('bug_id', 'N/A')}")
        print(f"  Severity: {autofix_meta.get('severity', 'N/A')}")
        print(f"  Fix Location: {autofix_meta.get('fix_location', {}).get('file', 'N/A')}")

def main():
    """Run all demos"""
    print("🚀 Starting Autofix API Demo...")
    print("This demo shows how to use the reasoning/add API to store autofix response data.")
    
    # Store different types of autofix reasoning
    syntax_doc_id = demo_syntax_error_autofix()
    type_doc_id = demo_type_error_autofix()
    security_doc_id = demo_security_issue_autofix()
    
    # Search for stored reasoning
    demo_search_autofix_reasoning()
    
    print("\n✅ Demo completed!")
    print("\nStored document IDs:")
    if syntax_doc_id:
        print(f"  - Syntax fix: {syntax_doc_id}")
    if type_doc_id:
        print(f"  - Type fix: {type_doc_id}")
    if security_doc_id:
        print(f"  - Security fix: {security_doc_id}")
    
    print("\n📝 Summary:")
    print("- API reasoning/add có thể lưu đầy đủ autofix response data")
    print("- Bao gồm: thinking process, steps, token usage, code changes")
    print("- Metadata chứa thông tin chi tiết về fix process")
    print("- Có thể search và retrieve autofix reasoning sau này")
    print("- Hỗ trợ tracking confidence, severity, và performance metrics")

if __name__ == "__main__":
    main()