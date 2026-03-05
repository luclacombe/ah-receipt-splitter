.PHONY: install dev test lint format run docker clean

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt
	pre-commit install

test:
	pytest tests/ -v --tb=short

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

run:
	streamlit run app.py

docker:
	docker compose up --build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache .ruff_cache
