# FixChain - Multi-Iteration Test Runner System

A robust, extensible test runner system built with SOLID principles for automated code analysis and testing, featuring RAG (Retrieval-Augmented Generation) capabilities.

## 🚀 Features

- **Multi-iteration test execution** with configurable retry logic
- **Static analysis tests** including syntax checking, type checking, and security scanning
- **Extensible architecture** following SOLID principles
- **Parallel and sequential execution** modes
- **Comprehensive logging** and result tracking
- **Docker support** for MongoDB integration
- **RAG (Retrieval-Augmented Generation)** capabilities
- **Vector similarity search** using MongoDB
- **OpenAI embeddings integration**

## 📁 Project Structure

```
FixChain/
├── core/                          # Core test runner logic
│   ├── base.py                    # Abstract base classes and models
│   ├── runner.py                  # TestRunner implementation
│   └── tests/                     # Test implementations
│       └── static/                # Static analysis tests
│           ├── syntax_check.py    # Syntax validation
│           ├── type_check.py      # Type checking
│           └── security_check.py  # Security scanning
├── models/                        # Data models
│   ├── test_result.py            # Test result models
│   └── __init__.py
├── db/                           # Database components
│   ├── interfaces/               # Abstract interfaces
│   │   ├── document_store.py     # Document store interface
│   │   └── bug_store.py          # Bug store interface
│   └── mongo/                    # MongoDB implementations
│       ├── fixchain_db.py        # FixChainDB implementation
│       └── exceptions.py         # Database exceptions
├── rag/                          # RAG system components
│   ├── stores.py                 # Vector store implementations
│   ├── embedding.py              # Embedding providers
│   └── models.py                 # RAG data models
├── config/                       # Configuration management
├── tests/                        # Unit and integration tests
├── docker/                       # Docker configurations
├── logs/                         # Log files
├── example_usage.py              # Usage examples
├── example_db_rag_usage.py       # DB and RAG usage examples
├── main.py                       # CLI application
├── requirements.txt              # Python dependencies
├── Makefile                      # Development commands
└── README.md                     # This file
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Docker (optional, for MongoDB)
- Git

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd FixChain
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up MongoDB (optional):**
   ```bash
   # Using Docker
   make docker-up
   
   # Or use existing MongoDB instance
   # Update MONGODB_URI in .env
   ```

## 🚀 Quick Start

### Running the Example

```bash
# Run the comprehensive example
python example_usage.py
```

### Using the CLI

```bash
# Demo mode
python main.py demo

# Interactive mode
python main.py interactive

# Check configuration
python main.py config-check
```

### Basic Usage

```python
from core.runner import TestRunner
from core.tests.static.syntax_check import SyntaxCheck
from core.tests.static.type_check import TypeCheck
from core.tests.static.security_check import CriticalSecurityCheck

# Create test runner
runner = TestRunner()

# Add tests
runner.add_test(SyntaxCheck(
    target_files=["src/main.py"],
    language="python",
    max_iterations=3
))

runner.add_test(TypeCheck(
    target_files=["src/"],
    language="python",
    type_checker="mypy"
))

runner.add_test(CriticalSecurityCheck(
    target_files=["src/"],
    language="python",
    security_tools=["bandit"]
))

# Run all tests
results = runner.run_all_tests(project_path="./my_project")

# Check results
for test_name, result in results.items():
    print(f"{test_name}: {'PASS' if result.final_result else 'FAIL'}")
```

### Database and RAG System Usage

#### FixChainDB (Document Store)

```python
from db import FixChainDB
from models.test_result import TestExecutionResult

# Initialize database
db = FixChainDB(
    connection_string="mongodb://localhost:27017",
    database_name="fixchain"
)
await db.connect()

# Save test result
result_id = await db.save_test_result(test_result)

# Retrieve test result
retrieved_result = await db.get_test_result(result_id)

# Log changelog
changes = {"status": "fixed", "patch_applied": True}
await db.log_changelog("bug-123", changes, datetime.utcnow())

# Save fix result
await db.save_fix_result("bug-123", patch_content, "applied")

# Get bug list
bugs = await db.get_bug_list("test-123")
```

#### FixChainRAGStore (Vector Store)

```python
from rag.stores import FixChainRAGStore, MongoVectorStore
from rag.embeddings import OpenAIEmbeddingProvider

# Initialize components
embedding_provider = OpenAIEmbeddingProvider(
    api_key="your-openai-api-key",
    model="text-embedding-ada-002"
)

vector_store = MongoVectorStore(
    mongodb_uri="mongodb://localhost:27017",
    database_name="fixchain",
    collection_name="rag_insights"  # New collection name
)

rag_store = FixChainRAGStore(embedding_provider, vector_store)

# Store reasoning with required metadata
metadata = {
    "bug_id": "BUG-001",
    "test_name": "SyntaxCheck",
    "iteration": 3,
    "category": "static",
    "tool": "bandit",
    "status": "fail",
    "tags": ["security", "logic"],
    "timestamp": "2025-07-31T10:00:00",
    "source_file": "src/main.py"
}

# Store reasoning
doc_id = await rag_store.store_reasoning(
    "Analysis of SQL injection vulnerability...",
    metadata
)

# Search for reasoning entries
results = rag_store.search_reasoning(
    "SQL injection vulnerability",
    limit=5,
    filter={"category": "static"}
)

# Delete reasoning entries by bug ID
deleted_count = rag_store.delete_reasoning_by_bug_id("BUG-001")

# Search for relevant context (legacy method)
context_results = await rag_store.search_context(
    "SQL injection vulnerability fix",
    limit=5,
    tags=["security", "logic"]
)
```

## 🧪 Test Categories

### Static Analysis Tests

#### 1. SyntaxCheck
- **Purpose:** Validates code syntax
- **Supports:** Python (extensible to other languages)
- **Features:** AST parsing, error reporting, file discovery

```python
syntax_check = SyntaxCheck(
    target_files=["src/"],
    language="python",
    max_iterations=3
)
```

#### 2. TypeCheck
- **Purpose:** Verifies type annotations and type safety
- **Supports:** Python (mypy, pyright)
- **Features:** Strict mode, configurable checkers, pattern matching

```python
type_check = TypeCheck(
    target_files=["src/"],
    language="python",
    type_checker="mypy",
    strict_mode=True
)
```

#### 3. CriticalSecurityCheck
- **Purpose:** Scans for security vulnerabilities
- **Tools:** Bandit, Safety, Semgrep
- **Features:** Severity filtering, custom rules, comprehensive reporting

```python
security_check = CriticalSecurityCheck(
    target_files=["src/"],
    language="python",
    security_tools=["bandit", "safety"],
    severity_threshold="high"
)
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=fixchain
MONGODB_COLLECTION=embeddings

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Application Configuration
MAX_RETRIES=3
REQUEST_TIMEOUT=30
LOG_LEVEL=INFO
DEBUG_MODE=false
```

### Test Configuration

Tests can be configured with various parameters:

```python
# Maximum iterations per test
max_iterations = 5

# Target files/directories
target_files = ["src/", "tests/"]

# Language-specific settings
language = "python"
type_checker = "mypy"  # or "pyright"
security_tools = ["bandit", "safety", "semgrep"]

# Severity thresholds
severity_threshold = "medium"  # low, medium, high, critical
```

## 🏗️ Architecture

### Core Components

1. **TestCase (Abstract Base Class)**
   - Defines the interface for all test implementations
   - Handles multi-iteration logic
   - Provides result validation

2. **TestRunner**
   - Manages test execution
   - Supports parallel and sequential execution
   - Tracks execution history and results

3. **Test Result Models**
   - Structured data models using Pydantic
   - Comprehensive result tracking
   - Serializable for storage and analysis

4. **FixChainDB (MongoDB Document Store)**
   - Async MongoDB implementation for structured data
   - Test results, bug tracking, and changelog management
   - SOLID principles with clear interfaces
   - Motor-based async operations

5. **FixChainRAGStore (MongoDB Vector Store)**
   - MongoDB-based vector storage for semantic search
   - OpenAI embedding integration
   - Reasoning storage and context retrieval
   - Bug insight and fix recommendation system

### Design Principles

- **Single Responsibility:** Each class has a focused purpose
- **Open/Closed:** Extensible without modifying existing code
- **Liskov Substitution:** Test implementations are interchangeable
- **Interface Segregation:** Clean, focused interfaces
- **Dependency Inversion:** Depends on abstractions, not concretions

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test categories
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m slow
```

### Test Structure

```bash
tests/
├── test_syntax_check.py      # SyntaxCheck unit tests
├── test_type_check.py        # TypeCheck unit tests
├── test_security_check.py    # SecurityCheck unit tests
├── test_runner.py            # TestRunner unit tests
└── integration/              # Integration tests
```

## 🐳 Docker Support

### MongoDB with Docker

```bash
# Start MongoDB
make docker-up

# Stop MongoDB
make docker-down

# View logs
make docker-logs

# Clean up
make docker-clean
```

### Docker Compose

The project includes `docker-compose.yml` for easy MongoDB setup:

```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
```

## 📊 Development Tools

### Makefile Commands

```bash
# Development setup
make install          # Install dependencies
make dev-setup        # Complete development setup

# Code quality
make lint             # Run linting
make format           # Format code
make type-check       # Run type checking

# Testing
make test             # Run tests
make test-coverage    # Run tests with coverage

# Docker operations
make docker-up        # Start services
make docker-down      # Stop services
make docker-clean     # Clean up containers

# Application modes
make demo             # Run demo mode
make interactive      # Run interactive mode
make config-check     # Check configuration

# Cleanup
make clean            # Clean generated files
```

### Code Quality Tools

- **Black:** Code formatting
- **Flake8:** Linting
- **MyPy:** Type checking
- **Pytest:** Testing framework
- **Coverage:** Test coverage reporting

## 🔮 Future Extensions

### Planned Test Categories

1. **Dynamic Tests**
   - Runtime behavior analysis
   - Performance testing
   - Memory usage monitoring

2. **Simulation Tests**
   - Load testing
   - Stress testing
   - Chaos engineering

### Additional Features

- **Web UI:** Browser-based test management
- **CI/CD Integration:** GitHub Actions, Jenkins support
- **Report Generation:** HTML, PDF, JSON reports
- **Notification System:** Email, Slack, webhook notifications
- **Plugin System:** Custom test implementations

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/new-test-type`
3. **Make changes and add tests**
4. **Run quality checks:** `make lint format type-check test`
5. **Commit changes:** `git commit -m "Add new test type"`
6. **Push to branch:** `git push origin feature/new-test-type`
7. **Create Pull Request**

### Adding New Test Types

1. **Create test class** inheriting from `TestCase`
2. **Implement required methods:** `run()`, `validate()`
3. **Add to appropriate category module**
4. **Write unit tests**
5. **Update documentation**

## 📝 License

[Add your license information here]

## 📞 Support

- **Issues:** [GitHub Issues](link-to-issues)
- **Documentation:** [Wiki](link-to-wiki)
- **Discussions:** [GitHub Discussions](link-to-discussions)

---

**Built with ❤️ using Python and SOLID principles**
