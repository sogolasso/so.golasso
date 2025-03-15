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

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
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
        "message": "Welcome to Football Digest API",
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.VERSION
    }

# Keep-alive background task
async def keep_alive():
    """Periodically ping the health check endpoint to keep the service alive"""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # Get the base URL from settings or environment
                base_url = f"http://localhost:{settings.PORT}"
                response = await client.get(f"{base_url}/health")
                logging.info(f"Keep-alive ping successful: {response.status_code}")
            except Exception as e:
                logging.error(f"Keep-alive ping failed: {str(e)}")
            await asyncio.sleep(60)  # Ping every minute

@app.on_event("startup")
async def start_keep_alive():
    """Start the keep-alive task when the application starts"""
    asyncio.create_task(keep_alive())

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 10000))
    
    # Run the application with the specified host and port
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    ) 