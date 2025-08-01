# Makefile for FixChain RAG System

.PHONY: help install test lint format docker-build docker-up docker-down clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-up   - Start services with Docker Compose"
	@echo "  docker-down - Stop services"
	@echo "  clean       - Clean up generated files"
	@echo "  demo        - Run demonstration"
	@echo "  interactive - Run interactive mode"

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	pytest

# Run linting
lint:
	flake8 rag/ models/ config/ tests/ main.py
	mypy rag/ models/ config/ main.py

# Format code
format:
	black rag/ models/ config/ tests/ main.py

# Docker operations
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Application operations
demo:
	python main.py --mode demo

interactive:
	python main.py --mode interactive

config-check:
	python main.py --config-check

# Clean up
clean:
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Development setup
dev-setup: install
	cp .env.example .env
	@echo "Please edit .env file with your configuration"

# Full test with coverage
test-coverage:
	pytest --cov=rag --cov=models --cov=config --cov-report=html --cov-report=term

# Type checking
type-check:
	mypy rag/ models/ config/ main.py --ignore-missing-imports