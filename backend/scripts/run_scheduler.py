import sys
import os
import logging
import asyncio
from pathlib import Path

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

async def main():
    """Main entry point for the scheduler"""
    try:
        setup_environment()
        
        # Import after environment setup
        from app.core.scraping_scheduler import run_scheduler
        from app.core.config import settings
        
        # Log port configuration
        logger.info(f"Port configured: {settings.PORT}")
        
        # Run the scheduler
        await run_scheduler()
        
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1) 