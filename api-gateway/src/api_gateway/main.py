"""
API Gateway Main Entry Point

Initializes the FastAPI application with routes, middleware, and configuration.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn

from api_gateway import __version__
from api_gateway.config import load_config
from api_gateway.log_config import get_logger, setup_logging

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    config = load_config()
    setup_logging(config.log_level)
    logger = get_logger()

    logger.info(
        f"Starting API Gateway v{__version__}",
        extra={
            "host": config.host,
            "port": config.port,
            "timeout": config.timeout,
            "routes_count": len(config.routes),
        },
    )

    for route in config.routes:
        logger.info(
            f"Registered route: {route.prefix} -> {route.target_url}",
            extra={"target_service": route.name},
        )

    yield

    # Shutdown
    logger.info("Shutting down API Gateway")


app = FastAPI(
    title="API Gateway",
    description="Single entry point for the microservices architecture",
    version=__version__,
    lifespan=lifespan,
)

# Import and include routers/middleware after app creation to avoid circular imports
from api_gateway.api import router  # noqa: E402
from api_gateway.middleware import RequestLoggingMiddleware  # noqa: E402

# Add middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(router)


if __name__ == "__main__":
    config = load_config()
    uvicorn.run(
        "api_gateway.main:app",
        host=config.host,
        port=config.port,
    )
