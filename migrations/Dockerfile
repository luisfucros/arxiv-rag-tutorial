FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY ./pyproject.toml .
COPY wheels/ /tmp/py-wheels
RUN uv sync --find-links /tmp/py-wheels

COPY src ./
CMD sleep 5 && uv run --no-sync alembic upgrade head