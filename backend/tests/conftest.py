import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.main import app
import os
from dotenv import load_dotenv
from datetime import datetime
import platform

# Load test environment variables
load_dotenv("tests/.env.test")

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def pytest_html_report_title(report):
    report.title = "Só Golasso - Test Report"

def pytest_configure(config):
    # Create directories for reports if they don't exist
    os.makedirs("test-reports", exist_ok=True)
    
    # Add environment info to the report
    config._metadata = {
        "Project": "Só Golasso",
        "Python version": platform.python_version(),
        "Platform": platform.platform(),
        "Test Environment": "Development",
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

def pytest_html_results_table_header(cells):
    cells.insert(2, "<th>Description</th>")
    cells.insert(1, "<th>Time</th>")
    cells.pop()

def pytest_html_results_table_row(report, cells):
    cells.insert(2, f"<td>{getattr(report, 'description', '')}</td>")
    cells.insert(1, f"<td>{datetime.now().strftime('%H:%M:%S')}</td>")
    cells.pop()

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    description = str(item.function.__doc__)
    setattr(report, "description", description)

@pytest.fixture(scope="session")
def db():
    """Initialize test database."""
    Base.metadata.create_all(bind=engine)
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(db):
    """Create test client."""
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

@pytest.fixture
def test_article():
    """Sample article data for testing."""
    return {
        "title": "Flamengo vence Palmeiras em clássico emocionante",
        "content": "Em uma partida repleta de emoções...",
        "excerpt": "Mengão supera rival em jogo decisivo",
        "category": "match_result",
        "image_url": "https://example.com/image.jpg",
        "team_tags": ["Flamengo", "Palmeiras"],
        "player_tags": ["Gabigol", "Raphael Veiga"],
        "is_featured": True,
        "is_trending": True,
        "author_style": "narracao",
        "author_name": "Pelétrico Silva"
    }

@pytest.fixture
def mock_services(mocker):
    """Mock external services for testing."""
    mocker.patch("app.services.distribution_service.DistributionService._post_to_twitter")
    mocker.patch("app.services.distribution_service.DistributionService._post_to_facebook")
    mocker.patch("app.services.distribution_service.DistributionService._post_to_instagram")
    mocker.patch("app.services.seo_service.SEOService._get_trending_topics")
    mocker.patch("app.services.seo_service.SEOService.submit_to_google_news")
    return mocker 