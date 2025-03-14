from app import app
from scheduler import start_scheduler
import atexit

# Start the scraper scheduler when application starts
# This ensures it runs both in development and production
scheduler = start_scheduler()

# Register a function to shut down the scheduler when the app exits
if scheduler:
    atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    # Run the Flask app in development mode
    app.run(host="0.0.0.0", port=5000, debug=True)
