# FixChain Test Suite - Hướng Dẫn Setup

## Giới Thiệu

FixChain Test Suite là một framework kiểm thử tự động cho mã Python, có khả năng phát hiện lỗi cú pháp, kiểm tra kiểu dữ liệu và phân tích bảo mật.

## Yêu Cầu Hệ Thống

### Phần Mềm Cần Thiết
- **Python**: Phiên bản 3.8 trở lên
- **Git**: Để clone repository
- **MongoDB** (tùy chọn): Cho chức năng lưu trữ database
- **Docker** (tùy chọn): Để chạy MongoDB

### Kiểm Tra Phiên Bản Python
```bash
python --version
# hoặc
python3 --version
```

## Hướng Dẫn Setup

### Bước 1: Clone Repository
```bash
git clone https://github.com/innolabvn/FixChain.git
cd FixChain
```

### Bước 2: Tạo Virtual Environment (Khuyến Nghị)
```bash
# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
# Trên Windows:
venv\Scripts\activate

# Trên macOS/Linux:
source venv/bin/activate
```

### Bước 3: Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

### Bước 4: Cài Đặt Bandit (Cho Security Check)
```bash
pip install bandit
```

### Bước 5: Setup MongoDB (Tùy Chọn)

#### Sử Dụng Docker (Khuyến Nghị)
```bash
# Khởi động MongoDB với Docker
docker-compose up -d mongodb

# Kiểm tra trạng thái
docker-compose ps
```

#### Cài Đặt MongoDB Local
1. Tải MongoDB Community Server từ [mongodb.com](https://www.mongodb.com/try/download/community)
2. Cài đặt và khởi động MongoDB service
3. MongoDB sẽ chạy trên port 27017 (mặc định)

### Bước 6: Cấu Hình Environment (Tùy Chọn)
```bash
# Copy file cấu hình mẫu
cp .env.example .env

# Chỉnh sửa file .env theo nhu cầu
# Ví dụ: OPENAI_API_KEY, MONGODB_URI, etc.
```

## Kiểm Tra Setup

### Test 1: Chạy Test Suite Cơ Bản
```bash
# Kiểm tra với file mẫu có lỗi
python main.py --mode testsuite --file sample_code_with_issues.py --tests all

# Kiểm tra với file mẫu sạch
python main.py --mode testsuite --file clean_sample.py --tests all
```

### Test 2: Chạy Pytest
```bash
# Chạy tất cả unit tests
pytest

# Chạy với verbose output
pytest -v
```

### Test 3: Kiểm Tra Từng Loại Test
```bash
# Chỉ kiểm tra syntax
python main.py --mode testsuite --file sample_code_with_issues.py --tests syntax

# Chỉ kiểm tra type
python main.py --mode testsuite --file sample_code_with_issues.py --tests type

# Chỉ kiểm tra security
python main.py --mode testsuite --file sample_code_with_issues.py --tests security
```

## Cách Sử Dụng

### Command Line Interface
```bash
# Cú pháp cơ bản
python main.py --mode testsuite --file <đường_dẫn_file> --tests <loại_test>

# Các tùy chọn:
# --file: Đường dẫn đến file Python cần kiểm tra
# --tests: syntax, type, security, hoặc all
# --max-iterations: Số lần thử tối đa (mặc định: 5)
```

### Ví Dụ Sử Dụng
```bash
# Kiểm tra tất cả
python main.py --mode testsuite --file mycode.py --tests all

# Kiểm tra syntax và security
python main.py --mode testsuite --file mycode.py --tests syntax,security

# Với số lần thử tùy chỉnh
python main.py --mode testsuite --file mycode.py --tests all --max-iterations 3
```

### Python API
```python
from testsuite.static_tests.syntax_check import SyntaxCheckTest
from testsuite.static_tests.type_check import TypeCheckTest
from testsuite.static_tests.security_check import SecurityCheckTest

# Tạo test instance
syntax_test = SyntaxCheckTest(max_iterations=5)

# Chạy test
result = await syntax_test.run(
    source_file="mycode.py",
    attempt_id="test_1"
)

print(f"Status: {result.status}")
print(f"Summary: {result.summary}")
```

## Troubleshooting

### Lỗi Thường Gặp

#### 1. "bandit command not found"
```bash
pip install bandit
```

#### 2. "No module named 'testsuite'"
```bash
# Đảm bảo bạn đang ở thư mục gốc của project
cd FixChain
python main.py --mode testsuite --file sample_code_with_issues.py --tests syntax
```

#### 3. MongoDB Connection Error
```bash
# Kiểm tra MongoDB đang chạy
docker-compose ps

# Hoặc chạy mà không cần database
python main.py --mode testsuite --file mycode.py --tests all
```

#### 4. Unicode Encoding Error (Windows)
- Framework đã được cập nhật để tránh lỗi này
- Sử dụng ký tự ASCII thay vì emoji

### Kiểm Tra Log
```bash
# Xem log chi tiết
python main.py --mode testsuite --file mycode.py --tests all --debug
```

## Cấu Trúc Project

```
FixChain/
├── main.py                 # Entry point chính
├── testsuite/             # Test suite framework
│   ├── static_tests/      # Static analysis tests
│   │   ├── syntax_check.py
│   │   ├── type_check.py
│   │   └── security_check.py
│   └── interfaces/        # Test interfaces
├── core/                  # Core framework
├── db/                    # Database components
├── rag/                   # RAG system
├── models/                # Data models
└── config/                # Configuration
```

## Các Loại Test

### 1. Syntax Check
- Kiểm tra cú pháp Python
- Phát hiện lỗi syntax errors
- Sử dụng Python AST parser

### 2. Type Check
- Kiểm tra kiểu dữ liệu
- Sử dụng mypy
- Phát hiện type hints issues

### 3. Security Check
- Phân tích bảo mật
- Sử dụng bandit + custom patterns
- Phát hiện security vulnerabilities

## Tính Năng Nâng Cao

### Chạy với Database
1. Setup MongoDB (xem bước 5)
2. Cấu hình .env file
3. Sử dụng example scripts:
```bash
python example_db_rag_usage.py
python example_rag_insights_usage.py
```

### Custom Configuration
- Chỉnh sửa `config/settings.py`
- Cấu hình logging levels
- Tùy chỉnh test parameters

## Hỗ Trợ

- **Documentation**: Xem `OPERATION_GUIDE.md` cho hướng dẫn chi tiết
- **Issues**: Báo cáo lỗi trên GitHub repository
- **Examples**: Xem các file `example_*.py`

## Phiên Bản

- **Current**: v1.0.0
- **Python Support**: 3.8+
- **Platform**: Windows, macOS, Linux

---

**Lưu ý**: Framework này đang trong giai đoạn phát triển. Một số tính năng có thể thay đổi trong các phiên bản tương lai.