import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from app.models.article import Article

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.notification_emails = settings.NOTIFICATION_EMAILS
        
        # Verify we have all required settings
        if not all([self.smtp_host, self.smtp_port, self.smtp_user, self.smtp_password]):
            logger.error("Missing required email settings")
            raise ValueError("Missing required email settings")
        
        if not self.notification_emails:
            logger.warning("No notification emails configured")
    
    def send_error_notification(self, error_message: str):
        """Send error notification email"""
        if not self.notification_emails:
            logger.warning("No notification emails configured, skipping error notification")
            return
            
        subject = "Só Golasso Error Alert"
        body = f"""
        An error occurred in the Só Golasso system:
        
        {error_message}
        
        Please check the logs for more details.
        """
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(self.notification_emails)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server with explicit SSL/TLS
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                
            logger.info("Error notification email sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {str(e)}")
            if "InvalidSecondFactor" in str(e):
                logger.error("Gmail requires an App Password for this account. Please generate one at https://myaccount.google.com/apppasswords")
            raise
    
    def send_article_notification(self, article_title: str, article_url: str):
        """Send notification about new article"""
        if not self.notification_emails:
            logger.warning("No notification emails configured, skipping article notification")
            return
            
        subject = f"New Article: {article_title}"
        body = f"""
        A new article has been published on Só Golasso:
        
        Title: {article_title}
        URL: {article_url}
        
        Check it out!
        """
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(self.notification_emails)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server with explicit SSL/TLS
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                
            logger.info(f"Article notification email sent successfully for: {article_title}")
            
        except Exception as e:
            logger.error(f"Failed to send article notification: {str(e)}")
            if "InvalidSecondFactor" in str(e):
                logger.error("Gmail requires an App Password for this account. Please generate one at https://myaccount.google.com/apppasswords")
            raise 