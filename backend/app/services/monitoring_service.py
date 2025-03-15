import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.article import Article
from app.services.email_service import EmailService
from app.core.config import settings

logger = logging.getLogger(__name__)

class MonitoringService:
    def __init__(self, db: Session, email_service: EmailService):
        self.db = db
        self.email_service = email_service
        self.last_check = datetime.utcnow()
        
        # Define thresholds
        self.warning_threshold = timedelta(hours=4)  # Send warning if no articles in 4 hours
        self.alert_threshold = timedelta(hours=8)    # Send alert if no articles in 8 hours
        self.critical_threshold = timedelta(hours=12) # Send critical alert if no articles in 12 hours

    def check_article_generation(self, skip_notifications: bool = False):
        """Check if articles are being generated and notify if there are issues"""
        try:
            # Get total article count
            total_articles = self.db.query(Article).count()
            
            # Get published article count
            published_articles = self.db.query(Article).filter(Article.status == 'published').count()
            
            # Get articles from last 24 hours
            yesterday = datetime.now() - timedelta(days=1)
            recent_articles = self.db.query(Article).filter(Article.created_at >= yesterday).count()
            
            # Log current stats
            logger.info(f"Current article stats - Total: {total_articles}, Published: {published_articles}, Last 24h: {recent_articles}")
            
            # Check for potential issues
            if total_articles == 0:
                message = "No articles have been generated yet. This might indicate an issue with the scraping or generation process."
                logger.warning(message)
                if not skip_notifications:
                    self.notify_warning(message)
                
            elif recent_articles == 0:
                message = "No new articles in the last 24 hours. This might indicate an issue with the scraping or generation process."
                logger.warning(message)
                if not skip_notifications:
                    self.notify_warning(message)
                    
            elif published_articles == 0:
                message = "No articles have been published yet. This might indicate an issue with the publishing process."
                logger.warning(message)
                if not skip_notifications:
                    self.notify_warning(message)
                
        except Exception as e:
            error_message = f"Error in monitoring service: {str(e)}"
            logger.error(error_message)
            if not skip_notifications:
                self.notify_error(error_message)
            raise
    
    def notify_warning(self, message: str):
        """Send a warning notification"""
        try:
            self.email_service.send_error_notification(f"WARNING: {message}")
        except Exception as e:
            logger.error(f"Failed to send warning notification: {str(e)}")
    
    def notify_error(self, message: str):
        """Send an error notification"""
        try:
            self.email_service.send_error_notification(f"ERROR: {message}")
        except Exception as e:
            logger.error(f"Failed to send error notification: {str(e)}") 