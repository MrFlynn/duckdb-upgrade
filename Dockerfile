# Define build container
FROM debian:12-slim AS build

# Install Python
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes python3 python3-pip

# Install PDM
RUN pip install --break-system-packages --user pdm

# Copy current directory to app directory
WORKDIR /app
COPY src/ .
COPY pyproject.toml .
COPY pdm.lock .

# Create virtual environment and install dependencies
RUN python3 -m pdm venv create -f && \
    python3 -m pdm install --venv in-project

# Define application container
FROM gcr.io/distroless/python3-debian12:latest
COPY --from=build /app /app

# Runtime
WORKDIR /app
ENTRYPOINT [".venv/bin/python3", "-m", "duckdb_upgrade"]
