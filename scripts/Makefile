.PHONY: help install dev-install test lint clean docker-build docker-run deploy

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install -r requirements.txt

dev-install: ## Install development dependencies
	pip install -r requirements.txt
	pip install pytest coverage bandit mypy

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=lib --cov-report=html

lint: ## Run linting
	flake8 lib/ app.py
	mypy lib/ app.py

security: ## Run security scan
	bandit -r lib/ -x Identitas,Intermediarium

clean: ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -f bandit-report.html

docker-build: ## Build Docker image
	docker build -t siteforge .

docker-run: ## Run with Docker Compose
	docker-compose up --build

docker-run-detached: ## Run with Docker Compose in background
	docker-compose up --build -d

deploy: ## Deploy to production (requires proper setup)
	@echo "Deploying to production..."
	# Add your deployment commands here

dev-server: ## Run development server
	python run.py

prod-server: ## Run production server with gunicorn
	gunicorn --bind 0.0.0.0:5000 --workers 4 run:create_app()