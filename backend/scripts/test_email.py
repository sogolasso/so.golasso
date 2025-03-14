import os
import sys
import logging
from datetime import datetime
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@dataclass
class TestArticle:
    title: str
    slug: str
    content: str
    summary: str
    category: str
    author_name: str

def test_email_notification():
    try:
        logger.info("Starting email notification test...")
        logger.info(f"SMTP Settings: Host={settings.SMTP_HOST}, Port={settings.SMTP_PORT}, User={settings.SMTP_USER}")
        
        # Create a test article
        logger.info("Creating test article...")
        test_article = TestArticle(
            title="Test Article",
            slug="test-article",
            content="This is a test article content.",
            summary="This is a test summary.",
            category="Test",
            author_name="Test Author"
        )

        logger.info("Preparing email...")
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'New Article Published: {test_article.title}'
        msg['From'] = settings.SMTP_USER
        msg['To'] = settings.NOTIFICATION_EMAIL or settings.SMTP_USER

        # Create HTML content
        html = f"""
        <html>
          <body>
            <h2>New Article Published</h2>
            <p><strong>Title:</strong> {test_article.title}</p>
            <p><strong>Category:</strong> {test_article.category}</p>
            <p><strong>Author:</strong> {test_article.author_name}</p>
            <p><strong>Summary:</strong> {test_article.summary}</p>
            <p><a href="{settings.FRONTEND_URL}/articles/{test_article.slug}">Read the full article</a></p>
          </body>
        </html>
        """

        msg.attach(MIMEText(html, 'html'))

        logger.info("Sending test email...")
        # Send email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Test email sent successfully!")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_email_notification() 