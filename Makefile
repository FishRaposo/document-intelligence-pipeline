.PHONY: install dev test lint format typecheck docker-up docker-down demo clean help worker migrate upgrade

install: ## Install shared-core (with extras) and project dependencies
	pip install -e '../shared-core[dev,docparse,embeddings]'
	pip install -e '.[dev]'

dev: ## Start the FastAPI development server
	python -m uvicorn doc_pipeline.main:app --app-dir src --reload --port 8000

test: ## Run unit tests with pytest
	pytest

lint: ## Lint source code with ruff
	ruff check .

format: ## Auto-format source code with ruff
	ruff format .

typecheck: ## Static type checking with pyright
	pyright src/

docker-up: ## Start PostgreSQL and Redis containers
	docker compose up -d

docker-down: ## Stop all Docker containers
	docker compose down

demo: ## Run the demonstration script
	python examples/run_demo.py

worker: ## Start the Celery worker
	celery -A doc_pipeline.worker:celery_app worker --loglevel=info

migrate: ## Generate a new Alembic migration
	alembic revision --autogenerate -m "auto"

upgrade: ## Apply all pending Alembic migrations
	alembic upgrade head

clean: ## Remove caches and temporary files
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; shutil.rmtree('.pytest_cache', ignore_errors=True); shutil.rmtree('.ruff_cache', ignore_errors=True)"

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
