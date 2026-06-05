.PHONY: test test-cov lint sync migrate

sync:
	uv sync

test:
	uv run pytest

test-cov:
	uv run pytest --cov=features --cov-report=term-missing

lint:
	uv run ruff check .

migrate:
	uv run python manage.py migrate

run:
	uv run python manage.py runserver
