# FixChain API Specification

## Tổng quan

Tài liệu này mô tả các API endpoints để import dữ liệu Bug và VectorDB vào hệ thống FixChain, hỗ trợ việc xây dựng dữ liệu tích cực cho AI learning.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
```http
Authorization: Bearer <your_api_token>
Content-Type: application/json
```

---

## 1. API Import Bug Data

### Endpoint
```http
POST /bugs/import
```

### Mục đích
Import dữ liệu bug đã được phát hiện và verified vào hệ thống để AI học hỏi từ historical data.

### Input Schema

#### Single Bug Import
```json
{
  "bug": {
    "bug_id": "string (optional)",
    "source_file": "string (required)",
    "bug_type": "string (required)",
    "severity": "string (required)",
    "line_number": "number (required)",
    "column_number": "number (optional)",
    "description": "string (required)",
    "code_snippet": "string (required)",
    "suggested_fix": "string (optional)",
    "actual_fix": "string (optional)",
    "detection_method": "string (required)",
    "ai_confidence": "number (0-1, optional)",
    "detection_iteration": "number (optional)",
    "fix_iteration": "number (optional)",
    "status": "string (required)",
    "human_feedback": {
      "is_valid_bug": "boolean (required)",
      "fix_quality": "string (optional)",
      "introduced_new_bugs": "boolean (optional)",
      "feedback_notes": "string (optional)"
    },
    "related_bugs": ["string"],
    "fix_impact": {
      "lines_changed": "number (optional)",
      "files_affected": ["string"],
      "test_results_after_fix": {
        "syntax_pass": "boolean (optional)",
        "type_pass": "boolean (optional)",
        "security_pass": "boolean (optional)"
      }
    }
  }
}
```

#### Batch Bug Import
```json
{
  "bugs": [
    {
      // Bug object như trên
    },
    {
      // Bug object khác
    }
  ],
  "batch_metadata": {
    "source": "string (optional)",
    "import_date": "ISO8601 (optional)",
    "imported_by": "string (optional)",
    "notes": "string (optional)"
  }
}
```

### Field Descriptions

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|-------------|
| `bug_type` | string | Yes | Loại bug | `"syntax"`, `"type"`, `"security"`, `"logic"`, `"performance"` |
| `severity` | string | Yes | Mức độ nghiêm trọng | `"critical"`, `"high"`, `"medium"`, `"low"` |
| `detection_method` | string | Yes | Phương pháp phát hiện | `"static_analysis"`, `"dynamic_analysis"`, `"manual_review"`, `"ai_detection"` |
| `status` | string | Yes | Trạng thái bug | `"detected"`, `"fixed"`, `"verified"`, `"rejected"`, `"in_progress"` |
| `fix_quality` | string | No | Chất lượng fix | `"excellent"`, `"good"`, `"acceptable"`, `"poor"` |

### Example Request
```json
{
  "bug": {
    "source_file": "src/utils/validator.py",
    "bug_type": "syntax",
    "severity": "high",
    "line_number": 45,
    "column_number": 12,
    "description": "Missing closing parenthesis in function call",
    "code_snippet": "def validate_input(data:\n    return len(data > 0",
    "suggested_fix": "def validate_input(data):\n    return len(data) > 0",
    "actual_fix": "def validate_input(data):\n    return len(data) > 0",
    "detection_method": "static_analysis",
    "ai_confidence": 0.95,
    "detection_iteration": 1,
    "fix_iteration": 1,
    "status": "fixed",
    "human_feedback": {
      "is_valid_bug": true,
      "fix_quality": "excellent",
      "introduced_new_bugs": false,
      "feedback_notes": "Perfect fix, no side effects"
    },
    "fix_impact": {
      "lines_changed": 1,
      "files_affected": ["src/utils/validator.py"],
      "test_results_after_fix": {
        "syntax_pass": true,
        "type_pass": true,
        "security_pass": true
      }
    }
  }
}
```

### Response
```json
{
  "success": true,
  "message": "Bug imported successfully",
  "data": {
    "bug_id": "68903a5c37120fdff5251c99",
    "created_at": "2025-08-04T12:00:00Z",
    "updated_at": "2025-08-04T12:00:00Z"
  }
}
```

---

## 2. API Import Vector Database

### Endpoint
```http
POST /vectordb/import
```

### Mục đích
Import test reasoning data với embeddings vào vector database để hỗ trợ RAG và similarity search.

### Input Schema

#### Single Reasoning Entry
```json
{
  "reasoning": {
    "test_name": "string (required)",
    "attempt_id": "string (required)",
    "source_file": "string (required)",
    "status": "string (required)",
    "summary": "string (required)",
    "output": "string (required)",
    "metadata": {
      "iteration": "number (required)",
      "file_size": "number (optional)",
      "execution_time": "number (optional)",
      "token_usage": {
        "prompt_tokens": "number (optional)",
        "completion_tokens": "number (optional)",
        "total_tokens": "number (optional)"
      },
      "confidence_level": "string (optional)",
      "severity_level": "string (optional)",
      "custom_patterns_checked": "number (optional)"
    },
    "embedding": "array<number> (optional)",
    "human_verified": "boolean (optional)",
    "verification_result": {
      "is_correct": "boolean (optional)",
      "false_positive": "boolean (optional)",
      "false_negative": "boolean (optional)",
      "verifier": "string (optional)",
      "verification_date": "ISO8601 (optional)",
      "notes": "string (optional)"
    }
  }
}
```

#### Batch Reasoning Import
```json
{
  "reasoning_entries": [
    {
      // Reasoning object như trên
    }
  ],
  "batch_metadata": {
    "source": "string (optional)",
    "embedding_model": "string (optional)",
    "embedding_dimensions": "number (optional)",
    "import_date": "ISO8601 (optional)",
    "imported_by": "string (optional)"
  }
}
```

#### Auto-Generate Embedding Option
```json
{
  "reasoning": {
    // Reasoning data without embedding
  },
  "generate_embedding": true,
  "embedding_config": {
    "model": "all-MiniLM-L6-v2",
    "text_fields": ["summary", "output"],
    "normalize": true
  }
}
```

### Field Descriptions

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|-------------|
| `test_name` | string | Yes | Loại test | `"syntax"`, `"type"`, `"security"`, `"performance"` |
| `status` | string | Yes | Kết quả test | `"pass"`, `"fail"`, `"error"`, `"skip"` |
| `confidence_level` | string | No | Mức độ tin cậy | `"high"`, `"medium"`, `"low"` |
| `severity_level` | string | No | Mức độ nghiêm trọng | `"critical"`, `"high"`, `"medium"`, `"low"` |
| `embedding` | array | No | Vector 384-dimensional | Array of 384 float numbers |

### Example Request
```json
{
  "reasoning": {
    "test_name": "syntax",
    "attempt_id": "syntax_1",
    "source_file": "clean_sample.py",
    "status": "pass",
    "summary": "No syntax errors found",
    "output": "Checking syntax for: clean_sample.py\n[OK] Syntax check passed",
    "metadata": {
      "iteration": 1,
      "file_size": 1421,
      "execution_time": 150,
      "token_usage": {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150
      },
      "confidence_level": "high",
      "custom_patterns_checked": 7
    },
    "human_verified": true,
    "verification_result": {
      "is_correct": true,
      "false_positive": false,
      "false_negative": false,
      "verifier": "john.doe@company.com",
      "verification_date": "2025-08-04T12:00:00Z",
      "notes": "Correct analysis, no issues found"
    }
  },
  "generate_embedding": true,
  "embedding_config": {
    "model": "all-MiniLM-L6-v2",
    "text_fields": ["summary", "output"],
    "normalize": true
  }
}
```

### Response
```json
{
  "success": true,
  "message": "Reasoning entry imported successfully",
  "data": {
    "entry_id": "68903a70cc8f44a7eaffc241",
    "embedding_generated": true,
    "embedding_dimensions": 384,
    "created_at": "2025-08-04T12:00:00Z"
  }
}
```

---

## 3. API Import Execution Session

### Endpoint
```http
POST /sessions/import
```

### Input Schema
```json
{
  "session": {
    "session_id": "string (optional)",
    "source_file": "string (required)",
    "session_number": "number (required)",
    "test_types": ["string"],
    "start_time": "ISO8601 (required)",
    "end_time": "ISO8601 (required)",
    "total_duration": "number (required)",
    "total_tokens_used": "number (optional)",
    "bugs_detected": "number (required)",
    "bugs_fixed": "number (required)",
    "new_bugs_introduced": "number (optional)",
    "overall_status": "string (required)",
    "performance_metrics": {
      "avg_response_time": "number (optional)",
      "token_efficiency": "number (optional)",
      "accuracy_rate": "number (required)",
      "false_positive_rate": "number (optional)",
      "false_negative_rate": "number (optional)"
    },
    "comparison_with_previous": {
      "token_usage_change": "number (optional)",
      "time_change": "number (optional)",
      "accuracy_change": "number (optional)",
      "improvement_areas": ["string"],
      "regression_areas": ["string"]
    }
  }
}
```

---

## 4. Bulk Import API

### Endpoint
```http
POST /import/bulk
```

### Input Schema
```json
{
  "import_type": "mixed",
  "data": {
    "bugs": [
      // Array of bug objects
    ],
    "reasoning_entries": [
      // Array of reasoning objects
    ],
    "sessions": [
      // Array of session objects
    ]
  },
  "options": {
    "generate_embeddings": true,
    "validate_data": true,
    "skip_duplicates": true,
    "update_existing": false
  },
  "metadata": {
    "source": "string",
    "import_batch_id": "string",
    "imported_by": "string",
    "notes": "string"
  }
}
```

---

## 5. Data Validation Rules

### Bug Data Validation
- `source_file`: Phải là đường dẫn file hợp lệ
- `line_number`: Phải > 0
- `ai_confidence`: Phải trong khoảng 0-1
- `bug_type`: Phải thuộc enum values
- `severity`: Phải thuộc enum values

### Reasoning Data Validation
- `embedding`: Nếu có, phải có đúng 384 dimensions
- `iteration`: Phải > 0
- `token_usage.total_tokens`: Phải = prompt_tokens + completion_tokens
- `status`: Phải thuộc enum values

### Session Data Validation
- `end_time`: Phải > start_time
- `total_duration`: Phải = end_time - start_time (ms)
- `bugs_fixed`: Phải <= bugs_detected
- `accuracy_rate`: Phải trong khoảng 0-1

---

## 6. Error Responses

### Validation Error
```json
{
  "success": false,
  "error": "validation_error",
  "message": "Invalid input data",
  "details": {
    "field": "bug_type",
    "error": "Invalid value. Must be one of: syntax, type, security, logic, performance",
    "received": "invalid_type"
  }
}
```

### Duplicate Error
```json
{
  "success": false,
  "error": "duplicate_entry",
  "message": "Bug with same source_file and line_number already exists",
  "existing_id": "68903a5c37120fdff5251c99"
}
```

### Server Error
```json
{
  "success": false,
  "error": "internal_error",
  "message": "Failed to process import request",
  "details": "Database connection failed"
}
```

---

## 7. Rate Limiting

- **Single Import**: 100 requests/minute
- **Batch Import**: 10 requests/minute
- **Bulk Import**: 5 requests/minute

## 8. File Upload Support

### Endpoint
```http
POST /import/file
```

### Supported Formats
- JSON (.json)
- CSV (.csv)
- Excel (.xlsx)

### Example CSV Format for Bugs
```csv
source_file,bug_type,severity,line_number,description,status,is_valid_bug
src/utils.py,syntax,high,45,Missing parenthesis,fixed,true
src/main.py,type,medium,120,Type mismatch,detected,true
```

---

## 9. Query APIs (Bonus)

### Search Similar Bugs
```http
GET /bugs/similar?source_file=src/utils.py&bug_type=syntax&limit=10
```

### Get Reasoning History
```http
GET /reasoning/history?source_file=clean_sample.py&test_name=syntax
```

### Performance Analytics
```http
GET /analytics/performance?source_file=src/main.py&from_date=2025-01-01&to_date=2025-08-04
```

---

## 10. Implementation Example

### Python Client Example
```python
import requests
import json

class FixChainAPIClient:
    def __init__(self, base_url, api_token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
    
    def import_bug(self, bug_data):
        url = f"{self.base_url}/bugs/import"
        response = requests.post(url, json={"bug": bug_data}, headers=self.headers)
        return response.json()
    
    def import_reasoning(self, reasoning_data, generate_embedding=True):
        url = f"{self.base_url}/vectordb/import"
        payload = {
            "reasoning": reasoning_data,
            "generate_embedding": generate_embedding
        }
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()
    
    def bulk_import(self, bugs=None, reasoning_entries=None, sessions=None):
        url = f"{self.base_url}/import/bulk"
        payload = {
            "import_type": "mixed",
            "data": {
                "bugs": bugs or [],
                "reasoning_entries": reasoning_entries or [],
                "sessions": sessions or []
            },
            "options": {
                "generate_embeddings": True,
                "validate_data": True,
                "skip_duplicates": True
            }
        }
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()

# Usage
client = FixChainAPIClient("http://localhost:8000/api/v1", "your_api_token")

# Import a bug
bug = {
    "source_file": "src/utils.py",
    "bug_type": "syntax",
    "severity": "high",
    "line_number": 45,
    "description": "Missing closing parenthesis",
    "status": "fixed",
    "human_feedback": {
        "is_valid_bug": True,
        "fix_quality": "excellent"
    }
}

result = client.import_bug(bug)
print(f"Bug imported: {result['data']['bug_id']}")
```

API này cung cấp đầy đủ các endpoints cần thiết để import dữ liệu bug và vector database, hỗ trợ việc xây dựng hệ thống AI learning hiệu quả cho FixChain.