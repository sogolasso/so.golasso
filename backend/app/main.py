import os
import sys
from pathlib import Path
from datetime import datetime
import asyncio
import logging
import httpx

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import engine, Base

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version=getattr(settings, "VERSION", "1.0.0"),  # Use getattr with default
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Football Digest API is running",
        "version": settings.VERSION
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": getattr(settings, "VERSION", "1.0.0"),  # Use getattr with default
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Keep-alive background task
async def keep_alive():
    """Periodically ping the health check endpoint to keep the service alive"""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # Use environment variable for host
                host = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:10000")
                response = await client.get(f"{host}/health")
                logger.info(f"Keep-alive ping successful: {response.status_code}")
            except Exception as e:
                logger.error(f"Keep-alive ping failed: {str(e)}")
            await asyncio.sleep(60)  # Ping every minute

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting up Football Digest API...")
    # Start keep-alive task
    asyncio.create_task(keep_alive())
    logger.info("Keep-alive task started")

# Import and include API router
try:
    app.include_router(api_router, prefix=settings.API_V1_STR)
    logger.info("API routes registered successfully")
except Exception as e:
    logger.error(f"Failed to register API routes: {str(e)}")

if __name__ == "__main__":
    # Get port from environment variable
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    ) 