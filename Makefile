# WeedGo AI Engine Services - Makefile

.PHONY: help install build test deploy clean

# Variables
DOTNET_PROJECT = src/dotnet/WeedGo.AI.Api
PYTHON_SERVICE = src/python
DOCKER_REGISTRY = weedgo
VERSION = 1.0.0

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-15s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# Development Setup
install: ## Install all dependencies
	@echo "Installing .NET dependencies..."
	cd $(DOTNET_PROJECT) && dotnet restore
	@echo "Installing Python dependencies..."
	cd $(PYTHON_SERVICE) && pip install -r requirements.txt
	@echo "Setting up pre-commit hooks..."
	pre-commit install

dev-env: ## Setup development environment
	cp .env.example .env
	docker-compose -f docker-compose.dev.yml up -d postgres redis milvus
	@echo "Development environment ready!"

# Data Management
load-data: ## Load Canadian strain database
	@echo "Loading strain database..."
	python scripts/load_strain_data.py --source data/datasets/canadian_strains.json
	@echo "Creating vector embeddings..."
	python scripts/create_embeddings.py
	@echo "Data loading complete!"

migrate: ## Run database migrations
	cd $(DOTNET_PROJECT) && dotnet ef database update
	python scripts/migrate_vectors.py

# Build
build-dotnet: ## Build .NET services
	cd $(DOTNET_PROJECT) && dotnet build -c Release

build-python: ## Build Python services
	cd $(PYTHON_SERVICE) && python -m compileall .

build-docker: ## Build Docker images
	docker build -t $(DOCKER_REGISTRY)/ai-api:$(VERSION) -f deployment/docker/Dockerfile.dotnet .
	docker build -t $(DOCKER_REGISTRY)/ai-ml:$(VERSION) -f deployment/docker/Dockerfile.python .

build: build-dotnet build-python build-docker ## Build all components

# Testing
test-unit: ## Run unit tests
	cd $(DOTNET_PROJECT) && dotnet test ../../../tests/unit
	cd $(PYTHON_SERVICE) && pytest tests/unit

test-integration: ## Run integration tests
	docker-compose -f docker-compose.test.yml up -d
	cd tests/integration && dotnet test
	cd tests/integration && pytest
	docker-compose -f docker-compose.test.yml down

test-load: ## Run load tests
	cd tests/load && k6 run load_test.js

test: test-unit test-integration ## Run all tests

# Quality Checks
lint-dotnet: ## Lint .NET code
	cd $(DOTNET_PROJECT) && dotnet format --verify-no-changes

lint-python: ## Lint Python code
	cd $(PYTHON_SERVICE) && black --check .
	cd $(PYTHON_SERVICE) && flake8 .
	cd $(PYTHON_SERVICE) && mypy .

lint: lint-dotnet lint-python ## Run all linters

security-scan: ## Run security scans
	cd $(DOTNET_PROJECT) && dotnet list package --vulnerable
	cd $(PYTHON_SERVICE) && safety check
	trivy image $(DOCKER_REGISTRY)/ai-api:$(VERSION)
	trivy image $(DOCKER_REGISTRY)/ai-ml:$(VERSION)

# Development
run-dotnet: ## Run .NET service locally
	cd $(DOTNET_PROJECT) && dotnet run

run-python: ## Run Python service locally
	cd $(PYTHON_SERVICE) && python -m ml_service.server

run-local: ## Run all services locally
	docker-compose up

watch: ## Run with hot reload
	docker-compose -f docker-compose.dev.yml up

# Training
train-models: ## Train ML models
	python scripts/train_recommendation_model.py
	python scripts/train_face_recognition.py
	python scripts/train_pricing_model.py
	python scripts/train_nlp_models.py

evaluate-models: ## Evaluate model performance
	python scripts/evaluate_models.py --output reports/model_evaluation.html

# Deployment
deploy-dev: ## Deploy to development environment
	kubectl apply -f deployment/kubernetes/dev/
	kubectl rollout status deployment/ai-service -n weedgo-dev

deploy-staging: ## Deploy to staging environment
	kubectl apply -f deployment/kubernetes/staging/
	kubectl rollout status deployment/ai-service -n weedgo-staging

deploy-prod: ## Deploy to production
	@echo "Production deployment requires approval"
	kubectl apply -f deployment/kubernetes/production/
	kubectl rollout status deployment/ai-service -n weedgo-prod

rollback: ## Rollback last deployment
	kubectl rollout undo deployment/ai-service

# Monitoring
logs: ## View service logs
	docker-compose logs -f

metrics: ## View metrics dashboard
	open http://localhost:3000/grafana

monitoring: ## Start monitoring stack
	docker-compose -f docker-compose.monitoring.yml up -d

# Database
db-console: ## Open database console
	docker exec -it postgres psql -U weedgo -d ai_service

redis-cli: ## Open Redis CLI
	docker exec -it redis redis-cli

vector-console: ## Open Milvus console
	open http://localhost:19530

# Cleanup
clean-docker: ## Clean Docker resources
	docker-compose down -v
	docker system prune -f

clean-build: ## Clean build artifacts
	cd $(DOTNET_PROJECT) && dotnet clean
	find $(PYTHON_SERVICE) -type d -name __pycache__ -exec rm -rf {} +
	find $(PYTHON_SERVICE) -type f -name "*.pyc" -delete

clean-data: ## Clean data files
	rm -rf data/models/checkpoints/*
	rm -rf data/datasets/cache/*

clean: clean-build clean-docker ## Clean everything

# Utilities
format: ## Format code
	cd $(DOTNET_PROJECT) && dotnet format
	cd $(PYTHON_SERVICE) && black .
	cd $(PYTHON_SERVICE) && isort .

update-deps: ## Update dependencies
	cd $(DOTNET_PROJECT) && dotnet outdated
	cd $(PYTHON_SERVICE) && pip-review --auto

generate-docs: ## Generate documentation
	cd docs && mkdocs build
	open docs/site/index.html

benchmark: ## Run performance benchmarks
	python scripts/benchmark_inference.py
	python scripts/benchmark_scraping.py
	dotnet run --project tests/benchmark

# ML Model Management
export-models: ## Export models for production
	python scripts/export_models.py --format onnx --output data/models/production/

import-models: ## Import pre-trained models
	python scripts/import_models.py --source s3://weedgo-models/

model-info: ## Show model information
	python scripts/model_info.py

# Data Management
backup-data: ## Backup databases
	./scripts/backup.sh

restore-data: ## Restore databases
	./scripts/restore.sh

validate-data: ## Validate data integrity
	python scripts/validate_strain_data.py
	python scripts/validate_embeddings.py

# Quick Commands
up: ## Start all services and load data
	@echo "🚀 Starting WeedGo AI Engine Service..."
	@echo "Starting database services..."
	docker-compose up -d postgres redis milvus etcd minio
	@echo "Waiting for databases to be ready..."
	sleep 15
	@echo "Running database migrations..."
	docker exec -i $$(docker-compose ps -q postgres) psql -U weedgo -d ai_engine < data/migrations/001_create_ai_engine_schema.sql || true
	@echo "Loading complete OCS data pipeline..."
	DB_HOST=localhost DB_PORT=5434 DB_NAME=ai_engine DB_USER=weedgo DB_PASSWORD=weedgo123 MILVUS_HOST=localhost MILVUS_PORT=19531 REDIS_HOST=localhost REDIS_PORT=6381 python3 scripts/load_complete_data.py
	@echo "Starting application services..."
	docker-compose up -d ai-api ai-ml
	@echo "Waiting for services to be ready..."
	sleep 10
	@echo ""
	@echo "✅ WeedGo AI Engine started successfully!"
	@echo ""
	@echo "🔗 Service URLs:"
	@echo "  API Documentation: http://localhost:5100"
	@echo "  ML Service:        http://localhost:8501/health"
	@echo "  Grafana:           http://localhost:3000 (admin/admin)"
	@echo "  Jupyter:           http://localhost:8888 (token: weedgo)"
	@echo ""
	@echo "🧪 Quick Tests:"
	@echo "  Health Check:   curl http://localhost:8501/health"
	@echo "  API Health:     curl http://localhost:5100/health"
	@echo "  Virtual Budtender:"
	@echo "    curl -X POST http://localhost:8501/budtender/chat \\"
	@echo "         -H 'Content-Type: application/json' \\"
	@echo "         -d '{\"message\": \"I need help finding a relaxing strain\"}'"
	@echo ""
	@echo "📊 Check status with: make status"

down: clean ## Tear down everything

restart: down up ## Restart everything

status: ## Check service status
	docker-compose ps
	kubectl get pods -n weedgo

# Default target
.DEFAULT_GOAL := help