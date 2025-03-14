from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.monitoring import monitor
from app.database import SessionLocal
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Check system health including database, redis, and scraper status."""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Check database
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        health_data["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_data["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "degraded"
    finally:
        db.close()
    
    # Check Redis and scraper stats
    try:
        stats = monitor.get_stats()
        recent_errors = monitor.get_recent_errors(5)
        
        # Check if scraper is running (should have run in last hour)
        last_run = None
        for source in ['ge', 'espn', 'lance']:
            last_run_key = f"{source}:last_run_end"
            if last_run_key in stats:
                last_run = max(last_run or stats[last_run_key], stats[last_run_key])
        
        if last_run:
            last_run_time = datetime.fromisoformat(last_run)
            if datetime.now() - last_run_time > timedelta(hours=1):
                health_data["components"]["scraper"] = {
                    "status": "warning",
                    "message": "No recent scrapes",
                    "last_run": last_run
                }
                health_data["status"] = "degraded"
            else:
                health_data["components"]["scraper"] = {
                    "status": "healthy",
                    "last_run": last_run
                }
        
        health_data["components"]["redis"] = {"status": "healthy"}
        
        if recent_errors:
            health_data["components"]["recent_errors"] = recent_errors
            
    except Exception as e:
        health_data["components"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "degraded"
    
    return health_data

@router.get("/stats")
async def get_scraper_stats() -> Dict[str, Any]:
    """Get detailed scraper statistics."""
    try:
        stats = monitor.get_stats()
        recent_errors = monitor.get_recent_errors()
        
        return {
            "stats": stats,
            "recent_errors": recent_errors,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching stats: {str(e)}"
        ) 