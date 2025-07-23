.PHONY: help setup install redis-up redis-down redis-fresh gateway worker test clean clean-containers logs-containers

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
	@echo "  make redis-fresh - Stop Redis and restart with fresh volume"
	@echo ""
	@echo "Service Commands:"
	@echo "  make gateway     - Start FastAPI gateway"
	@echo "  make worker      - Start Celery worker"
	@echo "  make flower      - Start Celery monitoring (Flower)"
	@echo ""
	@echo "Development Commands:"
	@echo "  make test        - Run tests"
	@echo "  make clean       - Clean up temporary files"
	@echo "  make clean-containers - Stop and remove all sandbox containers"
	@echo "  make logs-containers  - Show logs of all running sandbox containers"
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
	cd backend && uv sync

# Redis with Docker
redis-up:
	@echo "Starting Redis..."
	docker run -d --name doc-analyser-redis \
		-p 6379:6379 \
		-v doc-analyser-redis-data:/data \
		--restart unless-stopped \
		redis:7-alpine

redis-down:
	@echo "Stopping Redis..."
	docker stop doc-analyser-redis || true
	docker rm doc-analyser-redis || true

redis-fresh:
	@echo "Stopping Redis and cleaning volume..."
	docker stop doc-analyser-redis || true
	docker rm doc-analyser-redis || true
	docker volume rm doc-analyser-redis-data || true
	@echo "Starting fresh Redis with new volume..."
	docker run -d --name doc-analyser-redis \
		-p 6379:6379 \
		-v doc-analyser-redis-data:/data \
		--restart unless-stopped \
		redis:7-alpine

# Services
gateway:
	@echo "Starting FastAPI gateway..."
	cd backend && uv run -m backend.gateway.main

worker:
	@echo "Starting Celery worker..."
	cd backend && uv run celery -A backend.worker.celery_app worker --loglevel=info --concurrency=5 --queues=analysis,execution

flower:
	@echo "Starting Celery monitoring..."
	cd backend && uv run celery -A backend.worker.celery_app flower --port=5555

format:
	@echo "Formatting code..."
	cd backend && uv run black backend/
	cd backend && uv run isort backend/

lint:
	@echo "Linting code..."
	cd backend && uv run flake8 backend/
	cd backend && uv run mypy backend/

# Cleanup
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	docker stop doc-analyser-redis || true
	docker rm doc-analyser-redis || true

# Clean up sandbox containers
clean-containers:
	@echo "Stopping and removing all doc-analyser-sandbox containers..."
	@docker ps -q --filter ancestor=doc-analyser-sandbox:latest | xargs -r docker stop || true
	@docker ps -a -q --filter ancestor=doc-analyser-sandbox:latest | xargs -r docker rm -f || true
	@echo "Sandbox containers cleaned up!"

# Show logs of all running sandbox containers
logs-containers:
	@echo "Showing logs of all running doc-analyser-sandbox containers..."
	@docker ps -q --filter ancestor=doc-analyser-sandbox:latest | xargs -I {} sh -c 'echo "=== Container {} ===" && docker logs {} --tail=50 && echo ""'
	
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