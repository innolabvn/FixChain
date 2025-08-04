# MongoDB-Only RAG Setup Guide

## Tổng quan

FixChain hiện đã được cấu hình để sử dụng MongoDB-only RAG storage với local embeddings thay vì phụ thuộc vào OpenAI API. Điều này giúp:

- Loại bỏ phụ thuộc vào OpenAI API key
- Sử dụng local embeddings với HuggingFace sentence-transformers
- Giảm chi phí và tăng tính riêng tư
- Hoạt động hoàn toàn offline

## Cài đặt

### 1. Cài đặt Dependencies

```bash
pip install sentence-transformers
```

### 2. Khởi động MongoDB

```bash
# Khởi động MongoDB container
docker-compose up -d mongodb

# Kiểm tra trạng thái
docker ps
```

### 3. Cấu hình Environment

Tệp `.env` đã được cấu hình với:

```env
# MongoDB Configuration (No Authentication)
MONGODB_URI=mongodb://localhost:27017/fixchain
MONGODB_DATABASE=fixchain
MONGODB_COLLECTION=test_reasoning

# Vector Search Configuration
VECTOR_INDEX_NAME=vector_index
EMBEDDING_DIMENSIONS=384

# Application Settings
APP_NAME=FixChain
APP_VERSION=1.0.0
DEBUG=false
```

## Sử dụng

### Chạy Test Suite với MongoDB RAG

```bash
# Chạy một test cụ thể
python main.py --mode testsuite --file clean_sample.py --tests syntax --enable-rag

# Chạy tất cả tests
python main.py --mode testsuite --file clean_sample.py --tests all --enable-rag

# Chạy với debug
python main.py --mode testsuite --file clean_sample.py --tests all --enable-rag --debug
```

### Kiểm tra dữ liệu đã lưu

```bash
# Kết nối MongoDB để xem dữ liệu
docker exec -it fixchain-mongodb mongosh

# Trong MongoDB shell:
use fixchain
db.test_reasoning.find().pretty()
db.test_reasoning.count()
```

## Tính năng MongoDB-Only RAG

### Local Embeddings
- Sử dụng model `all-MiniLM-L6-v2` từ sentence-transformers
- Embedding dimensions: 384
- Hoạt động hoàn toàn offline
- Không cần OpenAI API key

### MongoDB Storage
- Lưu trữ test reasoning và embeddings
- Hỗ trợ vector search (nếu cần)
- Không cần authentication
- Dữ liệu persistent qua Docker volumes

### Graceful Fallback
- Nếu MongoDB không khả dụng, hệ thống vẫn chạy bình thường
- Chỉ bỏ qua việc lưu trữ RAG data
- Không ảnh hưởng đến test execution

## Cấu trúc dữ liệu

Mỗi reasoning entry được lưu với cấu trúc:

```json
{
  "_id": "ObjectId",
  "test_name": "syntax",
  "attempt_id": "syntax_1",
  "source_file": "clean_sample.py",
  "status": "pass",
  "summary": "No syntax errors found",
  "output": "Test output...",
  "metadata": {
    "iteration": 1,
    "file_size": 1421
  },
  "embedding": [0.1, 0.2, ...], // 384-dimensional vector
  "timestamp": "2025-08-04T11:43:08.782Z"
}
```

## Troubleshooting

### MongoDB Connection Issues

```bash
# Kiểm tra MongoDB logs
docker-compose logs mongodb

# Restart MongoDB
docker-compose restart mongodb
```

### Embedding Model Issues

```bash
# Model sẽ được tự động download lần đầu
# Nếu có lỗi, xóa cache và thử lại
rm -rf ~/.cache/huggingface/
```

### Performance

- Lần đầu chạy có thể chậm do download model
- Các lần sau sẽ nhanh hơn do model đã được cache
- Embedding generation rất nhanh với local model

## So sánh với OpenAI RAG

| Tính năng | MongoDB-Only | OpenAI RAG |
|-----------|--------------|------------|
| API Key | Không cần | Cần OpenAI key |
| Chi phí | Miễn phí | Có phí theo usage |
| Offline | Hoàn toàn | Cần internet |
| Tốc độ | Nhanh (local) | Phụ thuộc network |
| Embedding Quality | Tốt | Rất tốt |
| Setup | Đơn giản | Cần cấu hình API |

## Kết luận

MongoDB-only RAG setup cung cấp một giải pháp hoàn chỉnh, miễn phí và riêng tư cho việc lưu trữ test reasoning trong FixChain. Hệ thống hoạt động ổn định và không phụ thuộc vào các dịch vụ bên ngoài.