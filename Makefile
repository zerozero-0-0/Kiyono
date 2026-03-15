.PHONY: help install dev-backend dev-frontend dev lint format typecheck test clean

help:
	@echo "Available commands:"
	@echo "  make install       Install dependencies using uv"
	@echo "  make dev-backend   Run FastAPI backend with hot-reload (Port 8000)"
	@echo "  make dev-frontend  Run Streamlit frontend (Port 8501)"
	@echo "  make dev           Run both backend and frontend concurrently"
	@echo "  make lint          Run linter (ruff)"
	@echo "  make format        Run formatter and fix auto-fixable issues (ruff)"
	@echo "  make typecheck     Run type checker (pyright)"
	@echo "  make test          Run tests (pytest)"
	@echo "  make clean         Remove cache directories"

install:
	uv pip install -e ".[dev]"

dev-backend:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	uv run streamlit run frontend/app.py --server.port 8501

dev:
	@echo "Starting backend and frontend concurrently... (Press Ctrl+C to stop both)"
	@trap 'kill 0' SIGINT; \
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload & \
	uv run streamlit run frontend/app.py --server.port 8501 & \
	wait

lint:
	uvx ruff check .

format:
	uvx ruff check --fix .
	uvx ruff format .

typecheck:
	uvx pyright .

test:
	uv run pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
