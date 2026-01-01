"""
FastAPI + FastMCP Server for Compounding Engineering.
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from config import configure_dspy
from server.api.api_router import api_router
from server.config.logging import configure_logging
from server.config.settings import get_settings
from server.infrastructure.celery.app import check_celery_workers

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    logger.info("Starting Compounding Engineering Server")

    # Configure logging
    configure_logging(level="INFO")

    # Configure DSPy
    configure_dspy()

    # Check Celery workers (warning only)
    if not check_celery_workers():
        logger.warning("No Celery workers detected - async tasks will not execute")

    logger.info("Server initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down Compounding Engineering Server")


# Create FastAPI application
app = FastAPI(
    title="Compounding Engineering API",
    description="Multi-repo MCP+API server for DSPy-based compounding engineering",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Localhost-only deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Serve static files
app.mount("/static", StaticFiles(directory="server/ui/static"), name="static")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Compounding Engineering Server",
        "version": "1.0.0",
        "docs": "/docs",
        "mcp": "Run via: python -m server.mcp.server",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    workers_active = check_celery_workers()
    return {"status": "healthy", "celery_workers": workers_active}


if __name__ == "__main__":
    uvicorn.run("server.main:app", host=settings.host, port=settings.port, reload=True)
