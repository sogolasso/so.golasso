import sys
import os
import logging
import asyncio
from pathlib import Path
from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Setup the Python path and environment"""
    current_dir = Path.cwd()
    backend_dir = current_dir
    if current_dir.name == "scripts":
        backend_dir = current_dir.parent
    
    # Add backend directory to Python path
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    logger.info("Starting scraping scheduler (Background Worker)...")
    logger.info(f"Python path: {sys.path}")
    logger.info(f"Current directory: {current_dir}")
    logger.info(f"Backend directory: {backend_dir}")
    
    # Change to backend directory
    os.chdir(backend_dir)

# Create FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start scheduler in background task
    scheduler_task = asyncio.create_task(run_scheduler_loop())
    yield
    # Cleanup on shutdown
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

async def run_scheduler_loop():
    """Run the scheduler in a loop"""
    try:
        # Import after environment setup
        from app.core.scraping_scheduler import run_scheduler
        from app.core.config import settings
        
        # Run the scheduler continuously
        while True:
            try:
                await run_scheduler()
                logger.info(f"Waiting {settings.SCRAPING_INTERVAL_MINUTES} minutes until next cycle")
                await asyncio.sleep(settings.SCRAPING_INTERVAL_MINUTES * 60)
            except Exception as e:
                logger.error(f"Error in scheduler cycle: {str(e)}", exc_info=True)
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
                
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {str(e)}", exc_info=True)
        sys.exit(1)

def main():
    """Main entry point"""
    try:
        setup_environment()
        
        # Import settings after environment setup
        from app.core.config import settings
        
        # Start uvicorn server
        port = settings.PORT
        logger.info(f"Starting server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 