"""FastAPI application entry point."""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app import models  # noqa: F401  (import registers the models with Base)
from app.database import Base, engine
from app.logging_config import setup_logging
from app.routers import addresses

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create the database tables on startup"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database ready, application started")
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title="Address Book API",
    description="Create, update, delete and search addresses by distance.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requests with status code and duration"""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


app.include_router(addresses.router)


@app.get("/", tags=["health"])
def health_check():
    """Health check"""
    return {"status": "ok"}
