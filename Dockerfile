# Use Python 3.11 as that's what Debian 12 shipped with.
FROM ghcr.io/astral-sh/uv:python3.11-bookworm AS build

# Copy current directory to app directory
WORKDIR /app
COPY src/ src/
COPY pyproject.toml .
COPY uv.lock .
COPY README.md .
COPY vendor/duckdb/src/storage/version_map.json src/duckdb_upgrade/data/version_map.json

# Create virtual environment and install dependencies
RUN uv venv .venv && \
    uv sync --python .venv/bin/python --no-dev

# Application container
FROM gcr.io/distroless/python3-debian12:latest

# Copy virtualenv from build container.
COPY --from=build /app/src /app/src
COPY --from=build /app/.venv/lib/python3.11/site-packages /app/.venv/lib/python3.11/site-packages
WORKDIR /app

# Tell built-in python executable where to find packages.
ENV PYTHONPATH="/app/src:/app/.venv/lib/python3.11/site-packages"

ENTRYPOINT ["python3", "-m", "duckdb_upgrade"]
