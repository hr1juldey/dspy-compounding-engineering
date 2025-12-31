FROM python:3.12-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Configure uv to install into /venv, decoupling it from the source directory
ENV UV_PROJECT_ENVIRONMENT="/venv"

# Copy dependency files and README (required for metadata)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
# --no-dev: Exclude development dependencies
RUN uv sync --frozen --no-dev

# Place the virtual environment in the PATH
ENV PATH="/venv/bin:$PATH"

# Copy application code
COPY . .

# Set entrypoint
ENTRYPOINT ["python", "cli.py"]
CMD ["--help"]
