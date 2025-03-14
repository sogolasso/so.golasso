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
        self.notification_email = settings.NOTIFICATION_EMAIL

    def send_article_notification(self, article: Article, to_email: str) -> bool:
        try:
            if not all([self.smtp_host, self.smtp_port, self.smtp_user, self.smtp_password]):
                logger.error("SMTP settings are not properly configured")
                return False

            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'New Article Published: {article.title}'
            msg['From'] = self.smtp_user
            msg['To'] = to_email

            # Create HTML content
            html = f"""
            <html>
              <body>
                <h2>New Article Published</h2>
                <p><strong>Title:</strong> {article.title}</p>
                <p><strong>Category:</strong> {article.category}</p>
                <p><strong>Author:</strong> {article.author_name}</p>
                <p><strong>Summary:</strong> {article.summary}</p>
                <p><a href="{settings.FRONTEND_URL}/articles/{article.slug}">Read the full article</a></p>
              </body>
            </html>
            """

            msg.attach(MIMEText(html, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email notification sent successfully for article: {article.title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            return False 