.PHONY: help install dev backend frontend test lint docker-up docker-down seed

help:
	@echo "GovtAssist AI — Available commands:"
	@echo "  make install     Install all dependencies"
	@echo "  make dev         Start backend + frontend locally"
	@echo "  make backend     Start backend only"
	@echo "  make frontend    Start frontend only"
	@echo "  make test        Run backend tests"
	@echo "  make lint        Run linters"
	@echo "  make docker-up   Start all services via Docker"
	@echo "  make docker-down Stop Docker services"
	@echo "  make seed        Seed the database"

install:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && . .venv/bin/activate && pytest tests/ -v

lint:
	cd backend && . .venv/bin/activate && ruff check app/ tests/
	cd frontend && npm run lint

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

seed:
	cd backend && . .venv/bin/activate && python -m scripts.seed_data
