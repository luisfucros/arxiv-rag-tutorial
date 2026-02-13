FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y python3-dev build-essential curl libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY wheels/ /tmp/py-wheels
RUN uv sync --find-links /tmp/py-wheels --no-cache

COPY ./src .

CMD ["uv", "run", "celery", "-A", "tasks.app", "worker", "--loglevel=info"]