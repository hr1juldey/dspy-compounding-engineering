"""
FastMCP + FastAPI Server for Compounding Engineering
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from server.adapters.dspy.bootstrap import configure_dspy
from server.api import api_router
from server.config.logging import setup_logging

# Import from the project's modules using absolute imports
from server.config.settings import settings
from server.mcp.server import get_mcp_server

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("Starting up Compounding Engineering Server")

    # Initialize services (will be used later)
    # policy_service = PolicyService()
    # usage_service = UsageService()
    # history_service = HistoryService()

    # Configure DSPy
    configure_dspy()

    logger.info("Services initialized and DSPy configured")

    yield  # This is where the application runs

    # Shutdown
    logger.info("Shutting down Compounding Engineering Server")


# Create FastAPI application with lifespan
app = FastAPI(
    title="Compounding Engineering API",
    description="API for DSPy-based compounding engineering system",
    version="1.0.0",
    lifespan=lifespan,
)

# Create FastMCP server instance
mcp = get_mcp_server().get_server()

# Include API routes via the main API router
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Compounding Engineering Server", "version": "1.0.0"}


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Run the combined FastAPI + FastMCP server
    This serves as the uvicorn entrypoint
    """
    uvicorn.run(
        "server.main:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=["server/"] if reload else None,
    )


if __name__ == "__main__":
    run_server(settings.host, settings.port, reload=True)
