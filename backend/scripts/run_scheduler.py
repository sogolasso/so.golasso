import sys
import os
import logging
import asyncio
import signal
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from app.core.scraping_scheduler import run_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to stdout for Render
    ]
)

logger = logging.getLogger(__name__)

# Flag to control the scheduler
should_continue = True

def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully"""
    global should_continue
    logger.info(f"Received signal {signum}. Starting graceful shutdown...")
    should_continue = False

async def main():
    """Main function to run the scheduler"""
    global should_continue
    
    try:
        # Set up signal handlers
        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)
        
        # Log startup information
        logger.info("Starting scraping scheduler (Background Worker)...")
        logger.info(f"Python path: {sys.path}")
        logger.info(f"Current directory: {os.getcwd()}")
        logger.info(f"Backend directory: {backend_dir}")
        
        # Run the scheduler until shutdown signal
        while should_continue:
            try:
                await run_scheduler()
            except Exception as e:
                if "Checkpoint required" in str(e):
                    # Extract the checkpoint URL from the error message
                    try:
                        error_msg = str(e)
                        checkpoint_url = error_msg.split("Point your browser to ")[1].split(" -")[0]
                        logger.error("Instagram requires security verification!")
                        logger.error("Please follow these steps:")
                        logger.error("1. Visit this URL in your browser:")
                        logger.error(checkpoint_url)
                        logger.error("2. Complete the security verification")
                        logger.error("3. Delete the Instagram session file (if it exists)")
                        logger.error("4. Restart this service")
                    except Exception:
                        logger.error("Could not extract checkpoint URL from error message")
                else:
                    logger.error(f"Error in scheduler cycle: {str(e)}", exc_info=True)
                
                # Wait before retrying
                await asyncio.sleep(60)
        
        logger.info("Scheduler shutdown complete")
        
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 