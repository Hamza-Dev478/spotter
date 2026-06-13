# ELD Trip Planner — developer shortcuts.
# Requires Python 3.11+ and Node 18+ (the frontend uses Vite 8 / React 18).
# Using nvm with an older default Node? Run `nvm use 20` before the frontend targets.

BACKEND  := backend
FRONTEND := frontend
VENV     := $(BACKEND)/.venv
PIP      := $(VENV)/bin/pip
MANAGE   := cd $(BACKEND) && .venv/bin/python manage.py

.DEFAULT_GOAL := help

.PHONY: help install install-backend install-frontend dev dev-backend dev-frontend \
        migrate test test-backend test-frontend build lint clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: install-backend install-frontend ## Install backend + frontend deps

install-backend: ## Create the venv, install Python deps, run migrations
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r $(BACKEND)/requirements.txt
	$(MANAGE) migrate

install-frontend: ## Install frontend deps
	cd $(FRONTEND) && npm install

dev: ## Run the backend (:8000) and frontend (:5173) together
	@$(MAKE) -j2 dev-backend dev-frontend

dev-backend: ## Run the Django dev server (:8000)
	$(MANAGE) runserver

dev-frontend: ## Run the Vite dev server (:5173)
	cd $(FRONTEND) && npm run dev

migrate: ## Apply database migrations
	$(MANAGE) migrate

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests (pytest)
	cd $(BACKEND) && .venv/bin/python -m pytest -q

test-frontend: ## Run frontend tests (vitest) + type-check/build
	cd $(FRONTEND) && npm run test && npm run build

build: ## Type-check + build the frontend for production
	cd $(FRONTEND) && npm run build

lint: ## Lint the frontend
	cd $(FRONTEND) && npm run lint

clean: ## Remove venv, node_modules, build output and caches
	rm -rf $(VENV) $(BACKEND)/staticfiles $(FRONTEND)/node_modules $(FRONTEND)/dist
	find $(BACKEND) -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	find $(BACKEND) -type d -name .pytest_cache -prune -exec rm -rf {} + 2>/dev/null || true
