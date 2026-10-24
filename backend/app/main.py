"""ParkFlow AI — FastAPI Backend Application Entry Point"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.db.database import init_db
from app.db.seed import seed_database
from app.api.v1.router import api_router
from app.websocket.manager import ws_manager
from app.websocket.endpoint import ws_router
from app.iot.simulator import simulator_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("🚀 ParkFlow AI starting up...")
    
    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")
    
    # Seed database with initial data
    await seed_database()
    logger.info("✅ Database seeded with 100 parking slots across 3 floors")
    
    # Start simulator in background if configured
    if settings.IOT_MODE in ("simulation", "hybrid"):
        asyncio.create_task(simulator_service.start_background())
        logger.info("✅ IoT simulator started in background")
    
    logger.info("🎉 ParkFlow AI ready — http://localhost:8000")
    logger.info("📚 API Docs — http://localhost:8000/docs")
    
    yield
    
    # Shutdown
    logger.info("🛑 ParkFlow AI shutting down...")
    await simulator_service.stop()
    logger.info("✅ Simulator stopped")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ParkFlow AI",
        description="Smart Parking & Indoor Navigation Ecosystem",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Routers
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(ws_router)

    @app.get("/health", tags=["Health"])
    async def root_health():
        return {"status": "ok", "service": "ParkFlow AI", "version": "1.0.0"}

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
