# Format code with ruff
format:
    uv run ruff format .

# Lint code with ruff
lint:
    uv run ruff check .

# Run tests with pytest
test:
    uv run pytest

# Run development server
dev:
    uv run uvicorn main:app --reload
