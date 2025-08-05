#!/usr/bin/env python3
"""
Ví dụ về cách sử dụng API reasoning/add để lưu autofix response data.

Script này minh họa cách lưu trữ thông tin autofix bao gồm:
- Thinking process của AI
- Số bước thực hiện
- Token usage
- Vị trí sửa lỗi
- Code được sửa
"""

import asyncio
import json
import requests
from datetime import datetime
from typing import Dict, Any, List

# Configuration
FIXCHAIN_API_URL = "http://localhost:8000"
API_ENDPOINT = f"{FIXCHAIN_API_URL}/api/reasoning/add"

class AutofixReasoningLogger:
    """Class để log autofix reasoning vào RAG store."""
    
    def __init__(self, api_url: str = FIXCHAIN_API_URL):
        self.api_url = api_url
        self.endpoint = f"{api_url}/api/reasoning/add"
    
    def create_autofix_reasoning_content(self, 
                                       thinking: str,
                                       steps: List[str],
                                       token_usage: Dict[str, int],
                                       fix_location: Dict[str, Any],
                                       original_code: str,
                                       fixed_code: str,
                                       confidence: float) -> str:
        """Tạo nội dung reasoning cho autofix.
        
        Args:
            thinking: Quá trình suy nghĩ của AI
            steps: Danh sách các bước thực hiện
            token_usage: Thông tin về token sử dụng
            fix_location: Vị trí sửa lỗi (file, line, column)
            original_code: Code gốc có lỗi
            fixed_code: Code đã được sửa
            confidence: Độ tin cậy của fix (0-1)
            
        Returns:
            Chuỗi reasoning content đã format
        """
        
        reasoning_content = f"""
=== AUTOFIX REASONING ===

## AI Thinking Process:
{thinking}

## Fix Steps:
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(steps)])}

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

## Confidence Score: {confidence:.2f}

## Fix Summary:
Successfully applied autofix with {len(steps)} steps, using {token_usage.get('total_tokens', 0)} tokens.
Confidence level: {confidence:.1%}
        """.strip()
        
        return reasoning_content
    
    def create_autofix_metadata(self,
                              bug_id: str,
                              source_file: str,
                              bug_type: str,
                              severity: str,
                              fix_iteration: int,
                              token_usage: Dict[str, int],
                              confidence: float) -> Dict[str, Any]:
        """Tạo metadata cho autofix reasoning.
        
        Args:
            bug_id: ID của bug
            source_file: File chứa bug
            bug_type: Loại bug (syntax, type, security, etc.)
            severity: Mức độ nghiêm trọng
            fix_iteration: Lần thử fix thứ mấy
            token_usage: Thông tin token usage
            confidence: Độ tin cậy
            
        Returns:
            Dictionary chứa metadata
        """
        
        metadata = {
            "bug_id": bug_id,
            "test_name": "autofix",
            "iteration": fix_iteration,
            "category": "autofix",
            "source": "ai_autofix",
            "timestamp": datetime.now().isoformat(),
            "tags": ["autofix", bug_type, severity, "ai_generated"],
            
            # Autofix specific metadata
            "autofix_metadata": {
                "source_file": source_file,
                "bug_type": bug_type,
                "severity": severity,
                "fix_iteration": fix_iteration,
                "confidence": confidence,
                "token_usage": token_usage,
                "fix_timestamp": datetime.now().isoformat()
            }
        }
        
        return metadata
    
    def log_autofix_reasoning(self,
                            bug_id: str,
                            source_file: str,
                            bug_type: str,
                            severity: str,
                            thinking: str,
                            steps: List[str],
                            token_usage: Dict[str, int],
                            fix_location: Dict[str, Any],
                            original_code: str,
                            fixed_code: str,
                            confidence: float,
                            fix_iteration: int = 1) -> Dict[str, Any]:
        """Log autofix reasoning vào RAG store.
        
        Returns:
            Response từ API
        """
        
        # Tạo reasoning content
        content = self.create_autofix_reasoning_content(
            thinking=thinking,
            steps=steps,
            token_usage=token_usage,
            fix_location=fix_location,
            original_code=original_code,
            fixed_code=fixed_code,
            confidence=confidence
        )
        
        # Tạo metadata
        metadata = self.create_autofix_metadata(
            bug_id=bug_id,
            source_file=source_file,
            bug_type=bug_type,
            severity=severity,
            fix_iteration=fix_iteration,
            token_usage=token_usage,
            confidence=confidence
        )
        
        # Tạo request payload
        payload = {
            "content": content,
            "metadata": metadata
        }
        
        # Gửi request đến API
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Autofix reasoning logged successfully: {result.get('doc_id')}")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to log autofix reasoning: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise


def demo_autofix_reasoning():
    """Demo sử dụng AutofixReasoningLogger."""
    
    logger = AutofixReasoningLogger()
    
    # Ví dụ 1: Syntax Error Fix
    print("=== Demo 1: Syntax Error Fix ===")
    
    result1 = logger.log_autofix_reasoning(
        bug_id="BUG-SYNTAX-001",
        source_file="src/utils/validator.py",
        bug_type="syntax",
        severity="high",
        thinking="Phát hiện thiếu dấu đóng ngoặc trong function call. Cần thêm ')' để hoàn thành syntax. Đây là lỗi cú pháp đơn giản có thể sửa tự động.",
        steps=[
            "Phân tích syntax error tại line 45",
            "Xác định vị trí thiếu closing parenthesis",
            "Thêm ')' vào cuối expression",
            "Validate syntax sau khi fix"
        ],
        token_usage={
            "prompt_tokens": 150,
            "completion_tokens": 75,
            "total_tokens": 225
        },
        fix_location={
            "file": "src/utils/validator.py",
            "line": 45,
            "column": 25
        },
        original_code="def validate_input(data:\n    return len(data > 0",
        fixed_code="def validate_input(data):\n    return len(data) > 0",
        confidence=0.95,
        fix_iteration=1
    )
    
    # Ví dụ 2: Type Error Fix
    print("\n=== Demo 2: Type Error Fix ===")
    
    result2 = logger.log_autofix_reasoning(
        bug_id="BUG-TYPE-002",
        source_file="src/models/user.py",
        bug_type="type",
        severity="medium",
        thinking="Function expect string parameter nhưng có thể nhận int. Cần thêm type conversion hoặc update type hint để handle cả hai loại. Chọn cách convert to string để đảm bảo compatibility.",
        steps=[
            "Phân tích type mismatch error",
            "Xác định expected type vs actual type",
            "Thêm str() conversion",
            "Update function để handle multiple types",
            "Test với cả string và int inputs"
        ],
        token_usage={
            "prompt_tokens": 200,
            "completion_tokens": 120,
            "total_tokens": 320
        },
        fix_location={
            "file": "src/models/user.py",
            "line": 28,
            "column": 15
        },
        original_code="def format_user_id(user_id):\n    return user_id.upper()",
        fixed_code="def format_user_id(user_id):\n    return str(user_id).upper()",
        confidence=0.88,
        fix_iteration=1
    )
    
    # Ví dụ 3: Security Issue Fix
    print("\n=== Demo 3: Security Issue Fix ===")
    
    result3 = logger.log_autofix_reasoning(
        bug_id="BUG-SEC-003",
        source_file="src/database/queries.py",
        bug_type="security",
        severity="critical",
        thinking="Phát hiện SQL injection vulnerability do string concatenation. Cần thay thế bằng parameterized query để prevent injection attacks. Đây là security issue nghiêm trọng cần fix ngay lập tức.",
        steps=[
            "Phát hiện SQL injection vulnerability",
            "Phân tích cách user input được sử dụng",
            "Thay thế string concatenation bằng parameterized query",
            "Thêm input validation",
            "Test với malicious inputs để verify fix"
        ],
        token_usage={
            "prompt_tokens": 300,
            "completion_tokens": 180,
            "total_tokens": 480
        },
        fix_location={
            "file": "src/database/queries.py",
            "line": 67,
            "column": 20
        },
        original_code="query = f\"SELECT * FROM users WHERE id = {user_id}\"\ncursor.execute(query)",
        fixed_code="query = \"SELECT * FROM users WHERE id = %s\"\ncursor.execute(query, (user_id,))",
        confidence=0.92,
        fix_iteration=2
    )
    
    print("\n✅ All autofix reasoning examples logged successfully!")
    return [result1, result2, result3]


if __name__ == "__main__":
    print("🚀 Starting Autofix Reasoning Demo...")
    print(f"API Endpoint: {API_ENDPOINT}")
    print("\nMake sure FixChain server is running on http://localhost:8000")
    print("\n" + "="*60)
    
    try:
        results = demo_autofix_reasoning()
        print("\n" + "="*60)
        print("📊 Summary:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Document ID: {result.get('doc_id')}")
        
        print("\n🎉 Demo completed successfully!")
        print("\n💡 Tip: You can now search for these autofix reasoning entries using:")
        print("   POST /api/reasoning/search")
        print("   with queries like 'syntax error fix', 'SQL injection', etc.")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("\nPlease ensure:")
        print("1. FixChain server is running on http://localhost:8000")
        print("2. RAG store is properly configured")
        print("3. MongoDB is accessible")