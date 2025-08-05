# 📋 Hướng dẫn sử dụng FixChain Test Suite

## 🧭 Mục tiêu của FixChain Test Suite

### Tại sao cần Test Suite trong hệ thống FixChain?

FixChain Test Suite là thành phần cốt lõi trong hệ sinh thái FixChain, được thiết kế để tự động hóa quy trình kiểm tra và sửa lỗi mã nguồn. Thay vì chỉ phát hiện bug một cách thụ động, Test Suite tích hợp khả năng học hỏi và cải thiện liên tục thông qua việc lưu trữ reasoning và kinh nghiệm từ các lần fix trước đó.

### Mục tiêu về kiểm tra chất lượng mã và quản lý vòng đời bug

- **Kiểm tra toàn diện**: Phân tích mã nguồn từ nhiều góc độ (cú pháp, kiểu dữ liệu, bảo mật)
- **Tự động sửa lỗi**: Thực hiện tối đa 5 vòng lặp để tự động khắc phục các vấn đề được phát hiện
- **Học hỏi từ kinh nghiệm**: Lưu trữ reasoning và cách tiếp cận để tái sử dụng trong tương lai
- **Quản lý vòng đời bug**: Theo dõi từ phát hiện → sửa chữa → xác minh → lưu trữ kinh nghiệm

## 🧰 Tính năng chính

### Static Test Support
- **Syntax Check**: Kiểm tra cú pháp Python sử dụng AST parser
- **Type Check**: Phân tích kiểu dữ liệu với MyPy
- **Security Check**: Quét lỗ hổng bảo mật bằng Bandit

### Dynamic & Simulation Test (Đang phát triển)
- **Runtime Analysis**: Kiểm tra hành vi runtime
- **Performance Testing**: Đánh giá hiệu suất
- **Integration Testing**: Kiểm tra tích hợp

### RAG-powered Reasoning Storage
- Lưu trữ reasoning và thinking process vào MongoDB Vector Store
- Tái sử dụng kinh nghiệm từ các lần fix trước
- Cải thiện chất lượng fix theo thời gian

### Document Database Integration
- Lưu trữ metadata và kết quả test
- Theo dõi lịch sử thay đổi
- Quản lý false-positive và bug classification

### Iteration Control
- Tối đa 5 lần lặp cho mỗi test case
- Dừng sớm khi đạt được kết quả mong muốn
- Tự động rollback nếu fix gây ra regression

## 🔁 Quy trình chạy Test

### Vòng lặp Scan → Fix → Verify

```
1. SCAN: Chạy test suite để phát hiện issues
   ├── Syntax Check
   ├── Type Check
   └── Security Check

2. ANALYZE: Phân tích kết quả và tạo fix plan
   ├── Truy xuất reasoning từ RAG store
   ├── Đánh giá mức độ nghiêm trọng
   └── Tạo strategy sửa lỗi

3. FIX: Thực hiện sửa lỗi
   ├── Apply fix theo strategy
   ├── Lưu reasoning vào RAG
   └── Backup original code

4. VERIFY: Kiểm tra lại sau khi fix
   ├── Chạy lại test suite
   ├── Detect regression
   └── Validate fix quality

5. ITERATE: Lặp lại nếu cần (tối đa 5 lần)
   ├── Nếu còn issues → quay lại bước 2
   ├── Nếu có regression → rollback và thử cách khác
   └── Nếu đạt quality threshold → kết thúc
```

### Cơ chế tự động kiểm tra lại

- **Early Success Detection**: Dừng ngay khi không còn issues
- **Regression Prevention**: So sánh kết quả trước và sau fix
- **Quality Degradation Alert**: Cảnh báo khi fix gây ra vấn đề mới
- **Rollback Mechanism**: Tự động khôi phục nếu fix không hiệu quả

## 🧠 Quản lý thông tin

### RAG Store (MongoDB Vector Store)

**Lưu trữ:**
- **Reasoning Process**: Cách suy nghĩ và tiếp cận vấn đề
- **Fix Strategies**: Các chiến lược sửa lỗi đã thử
- **Context & Patterns**: Ngữ cảnh và pattern của bug
- **Learning Insights**: Kinh nghiệm học được từ mỗi lần fix
- **Code Changelog**: Lịch sử thay đổi mã nguồn

**Mục đích:**
- Tái sử dụng kinh nghiệm cho các bug tương tự
- Cải thiện chất lượng fix theo thời gian
- Xây dựng knowledge base về bug patterns

### Document Store (MongoDB)

**Lưu trữ:**
- **Test Results**: Kết quả chi tiết của từng test
- **Bug Metadata**: Thông tin về bug (severity, category, status)
- **Execution History**: Lịch sử chạy test và fix
- **False Positive List**: Danh sách false positive đã xác định
- **Performance Metrics**: Thống kê hiệu suất và thời gian fix

**Mục đích:**
- Tracking và reporting
- Phân tích xu hướng bug
- Quản lý false positive
- Đánh giá hiệu quả của hệ thống

## 📊 Kết quả & Phân tích

### So sánh chất lượng sau mỗi iteration

**Metrics được theo dõi:**
- **Issue Count**: Số lượng issues trước và sau fix
- **Severity Distribution**: Phân bố mức độ nghiêm trọng
- **Code Quality Score**: Điểm chất lượng tổng thể
- **Test Coverage**: Độ bao phủ test
- **Performance Impact**: Ảnh hưởng đến hiệu suất

**Phương pháp đánh giá:**
```python
# Ví dụ cấu trúc kết quả
{
  "iteration": 3,
  "before_fix": {
    "syntax_issues": 5,
    "type_issues": 2,
    "security_issues": 1,
    "quality_score": 6.5
  },
  "after_fix": {
    "syntax_issues": 0,
    "type_issues": 1,
    "security_issues": 0,
    "quality_score": 8.2
  },
  "improvement": {
    "issues_resolved": 6,
    "quality_gain": 1.7,
    "regression_detected": false
  }
}
```

### Truy xuất reasoning để tái sử dụng

**Query Pattern:**
- Tìm kiếm theo bug signature
- Filter theo ngôn ngữ và framework
- Ranking theo success rate
- Contextual similarity matching

**Reuse Strategy:**
- Áp dụng fix pattern đã thành công
- Tránh các approach đã fail
- Kết hợp multiple strategies
- Adaptive learning từ feedback

## 🚀 Cách khởi chạy

### Khởi chạy Test Suite với một file mã nguồn

**Cách 1: Sử dụng Python API**
```python
from core.test_executor import TestExecutor
from testsuite.static_tests.syntax_check import SyntaxCheckTest

# Khởi tạo executor
executor = TestExecutor()

# Chạy test cho một file
result = await executor.execute_single_test(
    source_file="path/to/your/code.py",
    test_case=SyntaxCheckTest()
)

print(f"Test completed: {result.final_status}")
print(f"Issues found: {len(result.attempts[-1].issues)}")
```

**Cách 2: Sử dụng Command Line**
```bash
# Chạy full test suite
python main.py --file path/to/code.py --tests all

# Chạy specific test
python main.py --file path/to/code.py --tests syntax,security

# Với custom iteration limit
python main.py --file path/to/code.py --max-iterations 3
```

**Cách 3: Batch Processing**
```python
# Chạy test cho nhiều files
files = ["src/module1.py", "src/module2.py"]
results = await executor.execute_test_suite(files)

for file_path, result in results.items():
    print(f"{file_path}: {result.final_status}")
```

### Môi trường yêu cầu

**Phần mềm cần thiết:**
- Python 3.11+
- MongoDB (cho Document Store và Vector Store)
- Motor (MongoDB async driver)
- Pytest (cho testing framework)

**Dependencies chính:**
- `pydantic` - Data validation
- `motor` - MongoDB async driver
- `pymongo` - MongoDB sync driver
- `mypy` - Type checking
- `bandit` - Security analysis
- `ast` - Syntax parsing

**Cấu hình MongoDB:**
```bash
# Khởi động MongoDB với Docker
docker-compose up -d mongo

# Hoặc local MongoDB
mongod --dbpath /path/to/data
```

## 📌 Lưu ý và giới hạn

### Tính năng hiện tại

**✅ Đã hỗ trợ:**
- Static Analysis (Syntax, Type, Security)
- RAG-powered reasoning storage
- Iteration control với early stopping
- MongoDB integration
- Async/await compatibility
- Comprehensive test coverage

**🚧 Đang phát triển:**
- Dynamic Testing (runtime analysis)
- Simulation Testing (integration scenarios)
- LLM-powered fix generation
- Advanced pattern recognition
- Multi-language support

### Giới hạn hiện tại

**Ngôn ngữ:**
- Hiện tại chỉ hỗ trợ Python
- Các ngôn ngữ khác đang được phát triển

**Test Types:**
- Dynamic và Simulation tests chưa hoàn thiện
- Một số edge cases chưa được cover

**Performance:**
- Iteration limit cố định (5 lần)
- Chưa có parallel processing cho multiple files

### Tích hợp với hệ thống chính

**Quan trọng**: FixChain Test Suite không phải là standalone application. Nó được thiết kế để tích hợp vào hệ thống FixChain lớn hơn:

- **Được gọi từ**: Main FixChain orchestrator
- **Input**: Source code files và test configuration
- **Output**: Test results và reasoning data
- **Integration**: Thông qua API calls và shared database

**Workflow tích hợp:**
```
FixChain Main System
    ↓
[Code Analysis Request]
    ↓
Test Suite Executor
    ↓
[Results + Reasoning]
    ↓
Main System (Decision Making)
```

---

*Tài liệu này cung cấp cái nhìn tổng quan về cách sử dụng FixChain Test Suite. Để biết thêm chi tiết về implementation và API reference, vui lòng tham khảo documentation kỹ thuật.*