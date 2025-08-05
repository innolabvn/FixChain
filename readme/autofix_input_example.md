# Input cần thiết để sử dụng API reasoning/add cho Autofix

## Tổng quan

Để lưu autofix response data vào RAG thông qua API `reasoning/add`, bạn cần chuẩn bị 2 phần chính:

1. **Content** - Nội dung autofix reasoning (string)
2. **Metadata** - Thông tin metadata chi tiết (object)

## 1. Content Input

Content nên được format theo template sau:

```
=== AUTOFIX REASONING ===

## AI Thinking Process:
[Quá trình suy nghĩ của AI khi phân tích bug]

## Fix Steps:
1. [Bước 1]
2. [Bước 2]
3. [Bước 3]
...

## Token Usage:
- Prompt tokens: [số]
- Completion tokens: [số]
- Total tokens: [số]

## Fix Location:
- File: [đường dẫn file]
- Line: [số dòng]
- Column: [số cột]

## Code Changes:

### Original Code:
```
[code gốc có bug]
```

### Fixed Code:
```
[code đã được sửa]
```

## Confidence Score: [0.0-1.0]

## Fix Summary:
[Tóm tắt kết quả fix]
```

## 2. Metadata Input

### Required Fields (Bắt buộc)

```json
{
  "bug_id": "BUG-XXX-001",           // ID của bug
  "test_name": "autofix",             // Luôn là "autofix"
  "iteration": 1,                     // Lần thử fix thứ mấy
  "category": "autofix",              // Luôn là "autofix"
  "source": "ai_autofix",             // Luôn là "ai_autofix"
  "timestamp": "2025-01-15T10:30:00.000Z", // Thời gian ISO format
  "tags": ["autofix", "syntax", "high", "ai_generated"] // Tags để filter
}
```

### Autofix Metadata (Tùy chọn nhưng khuyến khích)

```json
{
  "autofix_metadata": {
    "source_file": "src/utils/validator.py",  // File chứa bug
    "bug_type": "syntax",                     // Loại bug
    "severity": "high",                       // Mức độ nghiêm trọng
    "fix_iteration": 1,                       // Lần fix thứ mấy
    "confidence": 0.95,                       // Độ tin cậy (0.0-1.0)
    "token_usage": {                          // Chi tiết token
      "prompt_tokens": 150,
      "completion_tokens": 75,
      "total_tokens": 225
    },
    "fix_location": {                         // Vị trí chính xác
      "file": "src/utils/validator.py",
      "line": 45,
      "column": 25
    },
    "fix_timestamp": "2025-01-15T10:30:00.000Z" // Thời gian fix
  }
}
```

## 3. Ví dụ Input hoàn chỉnh

### Ví dụ 1: Syntax Error Fix

```json
{
  "content": "=== AUTOFIX REASONING ===\n\n## AI Thinking Process:\nPhát hiện thiếu dấu đóng ngoặc trong function call. Cần thêm ')' để hoàn thành syntax. Đây là lỗi cú pháp đơn giản có thể sửa tự động.\n\n## Fix Steps:\n1. Phân tích syntax error tại line 45\n2. Xác định vị trí thiếu closing parenthesis\n3. Thêm ')' vào cuối expression\n4. Validate syntax sau khi fix\n\n## Token Usage:\n- Prompt tokens: 150\n- Completion tokens: 75\n- Total tokens: 225\n\n## Fix Location:\n- File: src/utils/validator.py\n- Line: 45\n- Column: 25\n\n## Code Changes:\n\n### Original Code:\n```\ndef validate_input(data):\n    return len(data > 0\n```\n\n### Fixed Code:\n```\ndef validate_input(data):\n    return len(data) > 0\n```\n\n## Confidence Score: 0.95\n\n## Fix Summary:\nSuccessfully applied autofix with 4 steps, using 225 tokens.\nConfidence level: 95.0%",
  "metadata": {
    "bug_id": "BUG-SYNTAX-001",
    "test_name": "autofix",
    "iteration": 1,
    "category": "autofix",
    "source": "ai_autofix",
    "timestamp": "2025-01-15T10:30:00.000Z",
    "tags": ["autofix", "syntax", "high", "ai_generated"],
    "autofix_metadata": {
      "source_file": "src/utils/validator.py",
      "bug_type": "syntax",
      "severity": "high",
      "fix_iteration": 1,
      "confidence": 0.95,
      "token_usage": {
        "prompt_tokens": 150,
        "completion_tokens": 75,
        "total_tokens": 225
      },
      "fix_location": {
        "file": "src/utils/validator.py",
        "line": 45,
        "column": 25
      },
      "fix_timestamp": "2025-01-15T10:30:00.000Z"
    }
  }
}
```

### Ví dụ 2: Security Issue Fix

```json
{
  "content": "=== AUTOFIX REASONING ===\n\n## AI Thinking Process:\nPhát hiện SQL injection vulnerability do string concatenation. Cần thay thế bằng parameterized query để prevent injection attacks. Đây là security issue nghiêm trọng cần fix ngay lập tức.\n\n## Fix Steps:\n1. Phát hiện SQL injection vulnerability\n2. Phân tích cách user input được sử dụng\n3. Thay thế string concatenation bằng parameterized query\n4. Thêm input validation\n5. Test với malicious inputs để verify fix\n\n## Token Usage:\n- Prompt tokens: 300\n- Completion tokens: 180\n- Total tokens: 480\n\n## Fix Location:\n- File: src/database/queries.py\n- Line: 67\n- Column: 20\n\n## Code Changes:\n\n### Original Code:\n```\nquery = f\"SELECT * FROM users WHERE id = {user_id}\"\ncursor.execute(query)\n```\n\n### Fixed Code:\n```\nquery = \"SELECT * FROM users WHERE id = %s\"\ncursor.execute(query, (user_id,))\n```\n\n## Confidence Score: 0.92\n\n## Fix Summary:\nSuccessfully applied autofix with 5 steps, using 480 tokens.\nConfidence level: 92.0%",
  "metadata": {
    "bug_id": "BUG-SEC-003",
    "test_name": "autofix",
    "iteration": 2,
    "category": "autofix",
    "source": "ai_autofix",
    "timestamp": "2025-01-15T10:40:00.000Z",
    "tags": ["autofix", "security", "critical", "ai_generated", "sql_injection"],
    "autofix_metadata": {
      "source_file": "src/database/queries.py",
      "bug_type": "security",
      "severity": "critical",
      "fix_iteration": 2,
      "confidence": 0.92,
      "token_usage": {
        "prompt_tokens": 300,
        "completion_tokens": 180,
        "total_tokens": 480
      },
      "fix_location": {
        "file": "src/database/queries.py",
        "line": 67,
        "column": 20
      },
      "fix_timestamp": "2025-01-15T10:40:00.000Z"
    }
  }
}
```

## 4. Các loại Bug Type phổ biến

- `"syntax"` - Lỗi cú pháp
- `"type"` - Lỗi kiểu dữ liệu
- `"security"` - Lỗi bảo mật
- `"logic"` - Lỗi logic
- `"performance"` - Lỗi hiệu suất
- `"import"` - Lỗi import/dependency
- `"unused"` - Code không sử dụng
- `"multiple"` - Nhiều lỗi cùng lúc

## 5. Các mức Severity

- `"low"` - Ít nghiêm trọng
- `"medium"` - Trung bình
- `"high"` - Nghiêm trọng
- `"critical"` - Cực kỳ nghiêm trọng

## 6. Tags khuyến nghị

Luôn bao gồm:
- `"autofix"` (bắt buộc)
- Bug type: `"syntax"`, `"security"`, etc.
- Severity: `"low"`, `"medium"`, `"high"`, `"critical"`
- `"ai_generated"` (bắt buộc)

Tùy chọn:
- `"batch_fix"` - Nếu fix nhiều bugs cùng lúc
- `"sql_injection"`, `"xss"`, etc. - Specific security issues
- `"test"` - Nếu là test data

## 7. Cách sử dụng trong code

```python
import requests
from datetime import datetime, timezone

def store_autofix_reasoning(bug_id, thinking, steps, tokens, location, original, fixed, confidence, bug_type="unknown", severity="medium"):
    # Format content
    steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
    
    content = f"""=== AUTOFIX REASONING ===

## AI Thinking Process:
{thinking}

## Fix Steps:
{steps_text}

## Token Usage:
- Prompt tokens: {tokens['prompt_tokens']}
- Completion tokens: {tokens['completion_tokens']}
- Total tokens: {tokens['total_tokens']}

## Fix Location:
- File: {location['file']}
- Line: {location['line']}
- Column: {location['column']}

## Code Changes:

### Original Code:
```
{original}
```

### Fixed Code:
```
{fixed}
```

## Confidence Score: {confidence}

## Fix Summary:
Successfully applied autofix with {len(steps)} steps, using {tokens['total_tokens']} tokens.
Confidence level: {confidence*100:.1f}%"""
    
    # Prepare payload
    payload = {
        "content": content,
        "metadata": {
            "bug_id": bug_id,
            "test_name": "autofix",
            "iteration": 1,
            "category": "autofix",
            "source": "ai_autofix",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "tags": ["autofix", bug_type, severity, "ai_generated"],
            "autofix_metadata": {
                "source_file": location['file'],
                "bug_type": bug_type,
                "severity": severity,
                "fix_iteration": 1,
                "confidence": confidence,
                "token_usage": tokens,
                "fix_location": location,
                "fix_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
        }
    }
    
    # Send to API
    response = requests.post(
        "http://localhost:8000/api/reasoning/add",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    return response.json().get('doc_id') if response.status_code == 200 else None

# Ví dụ sử dụng
doc_id = store_autofix_reasoning(
    bug_id="BUG-001",
    thinking="Phát hiện syntax error...",
    steps=["Phân tích lỗi", "Xác định fix", "Apply fix", "Validate"],
    tokens={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    location={"file": "test.py", "line": 10, "column": 5},
    original="print('hello'",
    fixed="print('hello')",
    confidence=0.95,
    bug_type="syntax",
    severity="high"
)
```

## Tóm tắt

Input cần thiết:
1. **Content**: Autofix reasoning được format theo template
2. **Metadata**: Thông tin bug_id, timestamps, tags, và autofix_metadata chi tiết
3. **API endpoint**: `POST /api/reasoning/add`
4. **Headers**: `Content-Type: application/json`

Với input này, bạn có thể lưu trữ đầy đủ thông tin autofix response vào RAG để phân tích và học hỏi sau này.