FROM python:3.10-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies (uv sync creates .venv by default)
RUN uv sync --frozen

# Place the virtual environment in the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY . .

# Set entrypoint
ENTRYPOINT ["python", "cli.py"]
CMD ["--help"]
