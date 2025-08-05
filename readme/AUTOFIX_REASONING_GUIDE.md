# Hướng dẫn sử dụng API reasoning/add cho Autofix

## Tổng quan

API `reasoning/add` có thể được sử dụng để lưu trữ đầy đủ thông tin autofix response bao gồm:
- **Thinking process** của AI
- **Số bước** thực hiện
- **Token usage** (prompt, completion, total)
- **Vị trí sửa** (file, line, column)
- **Code changes** (original vs fixed)
- **Confidence score**
- **Metadata** chi tiết

## Workflow Autofix với RAG

```
1. Phát hiện bug → 2. Chạy autofix → 3. Nhận response → 4. Lưu vào RAG
                                        ↓
                              ┌─────────────────────┐
                              │ API reasoning/add   │
                              │ - thinking          │
                              │ - steps             │
                              │ - tokens            │
                              │ - code changes      │
                              │ - confidence        │
                              └─────────────────────┘
                                        ↓
                              ┌─────────────────────┐
                              │ RAG Storage         │
                              │ - Searchable        │
                              │ - Retrievable       │
                              │ - Analytics ready   │
                              └─────────────────────┘
```

## API Endpoint

**POST** `/api/reasoning/add`

### Request Format

```json
{
  "content": "=== AUTOFIX REASONING ===\n\n## AI Thinking Process:\n[thinking]\n\n## Fix Steps:\n[steps]\n\n## Token Usage:\n[usage]\n\n## Code Changes:\n[changes]",
  "metadata": {
    "bug_id": "BUG-XXX-001",
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

### Response Format

```json
{
  "doc_id": "reasoning_doc_12345",
  "status": "success"
}
```

## Cấu trúc Content

Content field nên được format theo template sau:

```
=== AUTOFIX REASONING ===

## AI Thinking Process:
[Mô tả quá trình suy nghĩ của AI]

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
[code gốc]
```

### Fixed Code:
```
[code đã sửa]
```

## Confidence Score: [0.0-1.0]

## Fix Summary:
[Tóm tắt kết quả fix]
```

## Metadata Fields

### Required Fields
- `bug_id`: ID của bug được fix
- `test_name`: "autofix" (cố định)
- `iteration`: Lần thử fix thứ mấy
- `category`: "autofix" (cố định)
- `source`: "ai_autofix" (cố định)
- `timestamp`: Thời gian ISO format

### Autofix Metadata
- `source_file`: File chứa bug
- `bug_type`: Loại bug (syntax, type, security, etc.)
- `severity`: Mức độ nghiêm trọng (low, medium, high, critical)
- `fix_iteration`: Lần fix thứ mấy
- `confidence`: Độ tin cậy (0.0-1.0)
- `token_usage`: Chi tiết token sử dụng
- `fix_location`: Vị trí chính xác của fix
- `fix_timestamp`: Thời gian fix

### Tags
Nên bao gồm:
- "autofix" (bắt buộc)
- Bug type: "syntax", "type", "security", etc.
- Severity: "low", "medium", "high", "critical"
- "ai_generated" (bắt buộc)
- Các tag khác tùy context

## Ví dụ sử dụng

### 1. Syntax Error Fix

```python
import requests

def store_syntax_fix(bug_id, thinking, steps, tokens, location, original, fixed, confidence):
    content = f"""=== AUTOFIX REASONING ===

## AI Thinking Process:
{thinking}

## Fix Steps:
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(steps)])}

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
    
    payload = {
        "content": content,
        "metadata": {
            "bug_id": bug_id,
            "test_name": "autofix",
            "iteration": 1,
            "category": "autofix",
            "source": "ai_autofix",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tags": ["autofix", "syntax", "high", "ai_generated"],
            "autofix_metadata": {
                "source_file": location['file'],
                "bug_type": "syntax",
                "severity": "high",
                "fix_iteration": 1,
                "confidence": confidence,
                "token_usage": tokens,
                "fix_location": location,
                "fix_timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    }
    
    response = requests.post(
        "http://localhost:8000/api/reasoning/add",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    return response.json().get('doc_id') if response.status_code == 200 else None
```

### 2. Multiple Bugs Fix

Có thể lưu thông tin fix nhiều bugs cùng lúc:

```python
def store_multiple_bugs_fix(bug_ids, thinking, steps, tokens, locations, changes, confidence):
    content = f"""=== AUTOFIX REASONING - MULTIPLE BUGS ===

## AI Thinking Process:
{thinking}

## Fix Steps:
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(steps)])}

## Token Usage:
- Prompt tokens: {tokens['prompt_tokens']}
- Completion tokens: {tokens['completion_tokens']}
- Total tokens: {tokens['total_tokens']}

## Multiple Fix Locations:
{chr(10).join([f"- Fix {i+1}: {loc['file']}:{loc['line']} ({loc['bug_type']})" for i, loc in enumerate(locations)])}

## Code Changes:
{changes}

## Confidence Score: {confidence}

## Fix Summary:
Successfully applied autofix for {len(bug_ids)} bugs with {len(steps)} steps, using {tokens['total_tokens']} tokens.
Confidence level: {confidence*100:.1f}%
Fixed: {', '.join([loc['bug_type'] for loc in locations])}"""
    
    payload = {
        "content": content,
        "metadata": {
            "bug_id": "|".join(bug_ids),  # Multiple bug IDs
            "test_name": "autofix",
            "iteration": 1,
            "category": "autofix",
            "source": "ai_autofix",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tags": ["autofix", "multiple_bugs", "medium", "ai_generated", "batch_fix"],
            "autofix_metadata": {
                "source_file": locations[0]['file'],  # Primary file
                "bug_type": "multiple",
                "severity": "medium",
                "fix_iteration": 1,
                "confidence": confidence,
                "bugs_fixed_count": len(bug_ids),
                "token_usage": tokens,
                "fix_locations": locations,
                "fix_timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    }
    
    # Store reasoning...
```

## Search Autofix Reasoning

Sau khi lưu, có thể search lại:

```python
def search_autofix_reasoning(query, bug_type=None, k=5):
    search_payload = {
        "query": query,
        "k": k
    }
    
    if bug_type:
        search_payload["filter_criteria"] = {
            "tags": {"$in": ["autofix", bug_type]}
        }
    
    response = requests.post(
        "http://localhost:8000/api/reasoning/search",
        json=search_payload,
        headers={"Content-Type": "application/json"}
    )
    
    return response.json().get('results', [])

# Ví dụ search
results = search_autofix_reasoning("syntax error fix", bug_type="syntax")
for result in results:
    print(f"Bug ID: {result['metadata']['bug_id']}")
    print(f"Confidence: {result['metadata']['autofix_metadata']['confidence']}")
    print(f"Tokens: {result['metadata']['autofix_metadata']['token_usage']['total_tokens']}")
```

## Lợi ích

1. **Traceability**: Theo dõi được toàn bộ quá trình autofix
2. **Analytics**: Phân tích performance, token usage, confidence
3. **Learning**: RAG có thể học từ các fix trước đó
4. **Debugging**: Debug autofix logic khi có vấn đề
5. **Optimization**: Tối ưu autofix dựa trên historical data
6. **Audit**: Audit trail cho compliance

## Kết luận

API `reasoning/add` hoàn toàn có thể đáp ứng yêu cầu lưu trữ autofix response data bao gồm thinking, steps, token usage, và fix location. Với cấu trúc metadata linh hoạt, có thể mở rộng để lưu thêm nhiều thông tin khác khi cần.