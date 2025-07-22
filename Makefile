.PHONY: help setup install redis-up redis-down gateway worker test clean

# Default target
help:
	@echo "Doc Analyser - Development Commands"
	@echo "==================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  make setup       - Complete project setup"
	@echo "  make install     - Install Python dependencies"
	@echo ""
	@echo "Infrastructure Commands:"
	@echo "  make redis-up    - Start Redis with Docker"
	@echo "  make redis-down  - Stop Redis"
	@echo ""
	@echo "Service Commands:"
	@echo "  make gateway     - Start FastAPI gateway"
	@echo "  make worker      - Start Celery worker"
	@echo "  make flower      - Start Celery monitoring (Flower)"
	@echo ""
	@echo "Development Commands:"
	@echo "  make test        - Run tests"
	@echo "  make clean       - Clean up temporary files"
	@echo "  make format      - Format code"
	@echo "  make lint        - Lint code"
	@echo ""

# Setup
setup: install redis-up
	@echo "Project setup complete! <�"
	@echo ""
	@echo "To start development:"
	@echo "1. In one terminal: make gateway"
	@echo "2. In another terminal: make worker"
	@echo "3. Visit http://localhost:8000/docs for API documentation"

# Install Python dependencies
install:
	@echo "Installing Python dependencies..."
	cd backend && pip install -e .
	cd backend && pip install -e .[dev]

# Redis with Docker
redis-up:
	@echo "Starting Redis..."
	docker run -d --name doc-analyser-redis \
		-p 6379:6379 \
		--restart unless-stopped \
		redis:7-alpine

redis-down:
	@echo "Stopping Redis..."
	docker stop doc-analyser-redis || true
	docker rm doc-analyser-redis || true

# Services
gateway:
	@echo "Starting FastAPI gateway..."
	cd backend && python -m backend.gateway.main

worker:
	@echo "Starting Celery worker..."
	cd backend && celery -A backend.worker.celery_app worker --loglevel=info --concurrency=2

flower:
	@echo "Starting Celery monitoring..."
	cd backend && celery -A backend.worker.celery_app flower --port=5555

# Development
test:
	@echo "Running tests..."
	cd backend && python -m pytest tests/ -v

format:
	@echo "Formatting code..."
	cd backend && black backend/
	cd backend && isort backend/

lint:
	@echo "Linting code..."
	cd backend && flake8 backend/
	cd backend && mypy backend/

# Cleanup
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	docker stop doc-analyser-redis || true
	docker rm doc-analyser-redis || true
	
# Check health
health:
	@echo "Checking system health..."
	@curl -f http://localhost:8000/docs || echo "Gateway not responding"
	@docker ps | grep doc-analyser-redis || echo "Redis not running"
	@echo "Redis health: $$(docker exec doc-analyser-redis redis-cli ping || echo 'DOWN')"

# Quick start
start: redis-up
	@echo "Starting all services..."
	@make gateway &
	@sleep 5
	@make worker