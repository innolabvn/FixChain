# 🚀 Hướng dẫn vận hành FixChain Test Suite

## 🎯 Mục tiêu

Tài liệu này hướng dẫn kỹ sư phần mềm cách vận hành FixChain Test Suite từ A-Z, bao gồm:
- Cách khởi chạy test suite theo nhiều phương thức khác nhau
- Thiết lập môi trường và kết nối MongoDB
- Các lệnh terminal thường dùng và ví dụ thực tế
- Kiểm tra và xác minh hệ thống hoạt động đúng

## 🧱 Yêu cầu môi trường

### Phần mềm cần thiết
- **Python 3.11+** (bắt buộc)
- **MongoDB** (local hoặc Docker)
- **Git** (để clone repository)

### Kiểm tra phiên bản Python
```bash
python --version
# Kết quả mong đợi: Python 3.11.x hoặc cao hơn
```

## 📦 Cài đặt dependencies

### Bước 1: Clone repository (nếu chưa có)
```bash
git clone https://github.com/innolabvn/FixChain.git
cd FixChain
```

### Bước 2: Cài đặt Python packages
```bash
# Cài đặt tất cả dependencies
pip install -r requirements.txt

# Hoặc cài đặt từng package chính
pip install motor pymongo pydantic pytest mypy bandit
```

### Bước 3: Xác minh cài đặt
```bash
# Kiểm tra các tool quan trọng
python -c "import motor, pymongo, pydantic; print('Dependencies OK')"
mypy --version
bandit --version
```

## 🔌 Kết nối MongoDB

### Cách 1: MongoDB với Docker (Khuyến nghị)

**Khởi động MongoDB:**
```bash
# Khởi động MongoDB container
docker-compose up -d mongo

# Kiểm tra container đang chạy
docker ps | grep mongo
```

**Dừng MongoDB:**
```bash
# Dừng MongoDB container
docker-compose down
```

**Logs và troubleshooting:**
```bash
# Xem logs MongoDB
docker-compose logs mongo

# Restart nếu có vấn đề
docker-compose restart mongo
```

### Cách 2: MongoDB Local

**Cài đặt MongoDB (Windows):**
```bash
# Download từ https://www.mongodb.com/try/download/community
# Hoặc dùng chocolatey
choco install mongodb
```

**Khởi động MongoDB local:**
```bash
# Tạo thư mục data
mkdir C:\data\db

# Khởi động MongoDB
mongod --dbpath C:\data\db

# Hoặc dùng Windows Service
net start MongoDB
```

**Kiểm tra kết nối:**
```bash
# Test connection
mongo --eval "db.adminCommand('ismaster')"
```

## 🚀 Các cách chạy FixChain Test Suite

### Cách 1: Command Line với `main.py`

**Chạy toàn bộ test suite:**
```bash
# Chạy tất cả test (syntax, type, security)
python main.py --file sample_code_with_issues.py --tests all

# Với số iteration tùy chỉnh (mặc định 5)
python main.py --file sample_code_with_issues.py --tests all --max-iterations 3
```

**Chạy test cụ thể:**
```bash
# Chỉ chạy syntax check
python main.py --file sample_code_with_issues.py --tests syntax

# Chạy syntax + security
python main.py --file sample_code_with_issues.py --tests syntax,security

# Chạy type check
python main.py --file sample_code_with_issues.py --tests type
```

**Chạy với file khác:**
```bash
# Test file Python bất kỳ
python main.py --file path/to/your/code.py --tests all

# Test nhiều file (nếu hỗ trợ)
python main.py --file "*.py" --tests syntax
```

**Các tùy chọn khác:**
```bash
# Verbose output
python main.py --file sample_code_with_issues.py --tests all --verbose

# Save results to file
python main.py --file sample_code_with_issues.py --tests all --output results.json

# Help
python main.py --help
```

### Cách 2: Python API

**Tạo script test đơn giản:**
```python
# test_my_code.py
import asyncio
from core.test_executor import TestExecutor
from testsuite.static_tests.syntax_check import SyntaxCheckTest
from testsuite.static_tests.type_check import TypeCheckTest
from testsuite.static_tests.security_check import SecurityCheckTest

async def run_tests():
    # Khởi tạo executor
    executor = TestExecutor()
    
    # Test syntax
    syntax_result = await executor.execute_single_test(
        source_file="sample_code_with_issues.py",
        test_case=SyntaxCheckTest()
    )
    
    print(f"Syntax Test: {syntax_result.final_status}")
    print(f"Issues found: {len(syntax_result.attempts[-1].issues)}")
    
    # Test security
    security_result = await executor.execute_single_test(
        source_file="sample_code_with_issues.py",
        test_case=SecurityCheckTest()
    )
    
    print(f"Security Test: {security_result.final_status}")
    print(f"Issues found: {len(security_result.attempts[-1].issues)}")

# Chạy tests
asyncio.run(run_tests())
```

**Chạy script:**
```bash
python test_my_code.py
```

**Batch processing nhiều files:**
```python
# batch_test.py
import asyncio
from core.test_executor import TestExecutor
from testsuite.static_tests.syntax_check import SyntaxCheckTest

async def batch_test():
    executor = TestExecutor()
    files = ["file1.py", "file2.py", "file3.py"]
    
    for file_path in files:
        try:
            result = await executor.execute_single_test(
                source_file=file_path,
                test_case=SyntaxCheckTest()
            )
            print(f"{file_path}: {result.final_status}")
        except Exception as e:
            print(f"{file_path}: ERROR - {e}")

asyncio.run(batch_test())
```

### Cách 3: Script ví dụ có sẵn

**`example_usage.py` - Sử dụng cơ bản:**
```bash
# Chạy ví dụ cơ bản (không cần MongoDB)
python example_usage.py
```
*Khi nào dùng:* Muốn test nhanh framework mà không cần setup database.

**`example_db_rag_usage.py` - Với Database + RAG:**
```bash
# Chạy ví dụ với MongoDB và RAG store (cần MongoDB)
python example_db_rag_usage.py
```
*Khi nào dùng:* Muốn test đầy đủ tính năng lưu trữ reasoning và metadata.

**`example_rag_insights_usage.py` - RAG Insights:**
```bash
# Chạy ví dụ về RAG insights và learning (cần MongoDB)
python example_rag_insights_usage.py
```
*Khi nào dùng:* Muốn test tính năng học hỏi và tái sử dụng reasoning từ các lần fix trước.

## ✅ Kiểm tra hệ thống hoạt động

### Bước 1: Chạy Unit Tests
```bash
# Chạy tất cả tests
pytest tests/test_testsuite.py -v

# Kết quả mong đợi: 20 passed, X warnings
```

**Chạy test cụ thể:**
```bash
# Test TestExecutor
pytest tests/test_testsuite.py::TestTestExecutor -v

# Test SyntaxCheck
pytest tests/test_testsuite.py::TestSyntaxCheckTest -v

# Test với output chi tiết
pytest tests/test_testsuite.py::TestTestExecutor::test_execute_single_test -vvs
```

### Bước 2: Test nhanh với sample code
```bash
# Test syntax check
python main.py --file sample_code_with_issues.py --tests syntax

# Kết quả mong đợi: Tìm thấy một số syntax issues
```

### Bước 3: Kiểm tra MongoDB connection
```bash
# Chạy example cần MongoDB
python example_db_rag_usage.py

# Nếu thành công: Không có error về MongoDB connection
```

### Troubleshooting

**Lỗi thường gặp và cách fix:**

```bash
# Lỗi: ModuleNotFoundError
pip install -r requirements.txt

# Lỗi: MongoDB connection
docker-compose up -d mongo
# hoặc
net start MongoDB

# Lỗi: Permission denied
# Windows: Chạy terminal as Administrator
# Linux/Mac: sudo python main.py ...

# Lỗi: Port already in use
docker-compose down
docker-compose up -d mongo
```

## 📋 Các lệnh terminal phổ biến

### Quản lý Dependencies
```bash
# Cài đặt packages
pip install -r requirements.txt
pip install motor pymongo pydantic pytest mypy bandit

# Upgrade packages
pip install --upgrade -r requirements.txt

# Kiểm tra packages đã cài
pip list | grep -E "motor|pymongo|pydantic|pytest|mypy|bandit"
```

### MongoDB Operations
```bash
# Docker MongoDB
docker-compose up -d mongo          # Khởi động
docker-compose down                  # Dừng
docker-compose logs mongo            # Xem logs
docker-compose restart mongo         # Restart

# Local MongoDB
net start MongoDB                    # Windows start
net stop MongoDB                     # Windows stop
mongod --dbpath /path/to/data        # Manual start
```

### Testing Commands
```bash
# Pytest
pytest tests/test_testsuite.py -v                    # Chạy tất cả
pytest tests/test_testsuite.py::TestClass -v         # Chạy class
pytest tests/test_testsuite.py::test_function -vvs   # Chạy function
pytest --tb=short                                    # Short traceback
pytest --maxfail=1                                   # Stop after first fail

# Main.py
python main.py --file sample_code_with_issues.py --tests all
python main.py --file mycode.py --tests syntax,security --max-iterations 3
python main.py --help
```

### Development Commands
```bash
# Code quality
mypy core/ testsuite/                # Type checking
bandit -r core/ testsuite/           # Security scan
python -m py_compile main.py         # Syntax check

# Git operations
git status
git add .
git commit -m "feat: add new feature"
git push
```

## 🔧 Cấu hình nâng cao

### Tùy chỉnh số vòng lặp (Iterations)

**Trong command line:**
```bash
# Mặc định: 5 iterations
python main.py --file code.py --tests all

# Tùy chỉnh: 3 iterations
python main.py --file code.py --tests all --max-iterations 3

# Chỉ 1 lần (no retry)
python main.py --file code.py --tests all --max-iterations 1
```

**Trong Python API:**
```python
result = await executor.execute_single_test(
    source_file="code.py",
    test_case=SyntaxCheckTest(),
    max_iterations=3  # Tùy chỉnh số lần
)
```

### Environment Variables
```bash
# Tạo file .env
cp .env.example .env

# Chỉnh sửa cấu hình
# MONGODB_URL=mongodb://localhost:27017
# DATABASE_NAME=fixchain
# LOG_LEVEL=INFO
```

### Logging Configuration
```bash
# Xem logs chi tiết
export LOG_LEVEL=DEBUG
python main.py --file code.py --tests all

# Lưu logs vào file
python main.py --file code.py --tests all > test_results.log 2>&1
```

## 📚 Ghi chú mở rộng

### Giới hạn hiện tại
- **Ngôn ngữ**: Chỉ hỗ trợ Python (các ngôn ngữ khác đang phát triển)
- **Test Types**: Dynamic và Simulation tests chưa hoàn thiện
- **Performance**: Chưa có parallel processing cho multiple files
- **Platform**: Tối ưu cho Windows, Linux/Mac cần test thêm

### Tính năng sắp tới
- Multi-language support (JavaScript, Java, C++)
- LLM-powered fix generation
- Web UI cho việc monitoring
- CI/CD integration

### Best Practices
1. **Luôn chạy pytest trước khi deploy**
2. **Backup MongoDB data định kỳ**
3. **Sử dụng Docker cho MongoDB trong production**
4. **Monitor logs để detect issues sớm**
5. **Update dependencies thường xuyên**

### Support & Troubleshooting
- **GitHub Issues**: https://github.com/innolabvn/FixChain/issues
- **Documentation**: Xem USAGE_GUIDE.md cho chi tiết architecture
- **Logs**: Kiểm tra `logs/` directory cho debug info

---

*Tài liệu này cung cấp hướng dẫn thực hành để vận hành FixChain Test Suite. Để hiểu sâu hơn về architecture và design, vui lòng tham khảo USAGE_GUIDE.md.*