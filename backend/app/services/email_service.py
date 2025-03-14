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

    def send_article_notification(self, article_title: str, article_url: str):
        """Send notification email when a new article is published"""
        if not all([self.smtp_host, self.smtp_port, self.smtp_user, self.smtp_password]):
            logger.warning("Email settings not configured. Skipping notification.")
            return

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(self.notification_emails)
            msg['Subject'] = f'New Article Published: {article_title}'

            body = f"""
            A new article has been published on Só Golasso:

            Title: {article_title}
            URL: {article_url}

            Best regards,
            Só Golasso Team
            """
            msg.attach(MIMEText(body, 'plain'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Article notification sent for: {article_title}")

        except Exception as e:
            logger.error(f"Failed to send article notification: {str(e)}")

    def send_error_notification(self, error_message: str):
        """Send notification email when an error occurs"""
        if not all([self.smtp_host, self.smtp_port, self.smtp_user, self.smtp_password]):
            logger.warning("Email settings not configured. Skipping error notification.")
            return

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(self.notification_emails)
            msg['Subject'] = 'Só Golasso System Error'

            body = f"""
            An error occurred in the Só Golasso system:

            Error: {error_message}

            Please check the system logs for more details.

            Best regards,
            Só Golasso Team
            """
            msg.attach(MIMEText(body, 'plain'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info("Error notification sent")

        except Exception as e:
            logger.error(f"Failed to send error notification: {str(e)}") 