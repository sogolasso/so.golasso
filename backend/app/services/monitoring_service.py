import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.article import Article
from app.services.email_service import EmailService
from app.core.config import settings

logger = logging.getLogger(__name__)

class MonitoringService:
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
        self.last_check = datetime.utcnow()
        
        # Define thresholds
        self.warning_threshold = timedelta(hours=4)  # Send warning if no articles in 4 hours
        self.alert_threshold = timedelta(hours=8)    # Send alert if no articles in 8 hours
        self.critical_threshold = timedelta(hours=12) # Send critical alert if no articles in 12 hours

    def check_article_generation(self):
        """Check if articles are being generated regularly"""
        try:
            now = datetime.utcnow()
            
            # Get the most recent article
            latest_article = self.db.query(Article).order_by(Article.created_at.desc()).first()
            
            if not latest_article:
                message = "No articles have been generated yet. This might indicate an issue with the scraping or generation process."
                logger.warning(message)
                self.email_service.send_error_notification(message)
                return
            
            time_since_last_article = now - latest_article.created_at
            
            # Check against thresholds
            if time_since_last_article > self.critical_threshold:
                message = f"""
                CRITICAL ALERT: No articles have been generated in the last {time_since_last_article.total_seconds() / 3600:.1f} hours!
                
                This is significantly longer than expected and requires immediate attention.
                Last article: "{latest_article.title}" at {latest_article.created_at}
                
                Please check:
                1. Scraping functionality
                2. AI generation service
                3. Database connectivity
                4. API rate limits
                5. System logs for errors
                """
                logger.error(message)
                self.email_service.send_error_notification(message)
                
            elif time_since_last_article > self.alert_threshold:
                message = f"""
                ALERT: No articles have been generated in the last {time_since_last_article.total_seconds() / 3600:.1f} hours.
                
                This is longer than expected and should be investigated.
                Last article: "{latest_article.title}" at {latest_article.created_at}
                """
                logger.error(message)
                self.email_service.send_error_notification(message)
                
            elif time_since_last_article > self.warning_threshold:
                message = f"""
                WARNING: No articles have been generated in the last {time_since_last_article.total_seconds() / 3600:.1f} hours.
                
                This might indicate a potential issue.
                Last article: "{latest_article.title}" at {latest_article.created_at}
                """
                logger.warning(message)
                self.email_service.send_error_notification(message)
            
            # Update last check time
            self.last_check = now
            
        except Exception as e:
            error_message = f"Error in monitoring service: {str(e)}"
            logger.error(error_message)
            self.email_service.send_error_notification(error_message) 