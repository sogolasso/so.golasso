import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.article import Article
from app.schemas.article import ArticleCreate, ArticleUpdate
from app.services.article_service import ArticleService

client = TestClient(app)

@pytest.fixture
def test_article():
    return {
        "title": "Flamengo vence Palmeiras em clássico emocionante",
        "content": "Em uma partida eletrizante no Maracanã...",
        "content_type": "MATCH_RESULT",
        "engagement_count": 0,
        "is_trending": False,
        "has_engagement": False
    }

def test_create_article(test_article):
    response = client.post("/api/articles/", json=test_article)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == test_article["title"]
    assert data["content_type"] == test_article["content_type"]

def test_get_article(test_article):
    # First create an article
    response = client.post("/api/articles/", json=test_article)
    article_id = response.json()["id"]
    
    # Then retrieve it
    response = client.get(f"/api/articles/{article_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == test_article["title"]

def test_list_articles(test_article):
    # Create a test article
    client.post("/api/articles/", json=test_article)
    
    # List all articles
    response = client.get("/api/articles/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

def test_update_article(test_article):
    # First create an article
    response = client.post("/api/articles/", json=test_article)
    article_id = response.json()["id"]
    
    # Update the article
    update_data = {
        "title": "Título atualizado: Flamengo empata com Palmeiras",
        "is_trending": True
    }
    response = client.patch(f"/api/articles/{article_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["is_trending"] == update_data["is_trending"]

def test_distribute_article(client, test_article, mock_services):
    """Test manual distribution of an article."""
    # Create an article
    create_response = client.post("/api/v1/articles/", json=test_article)
    article_id = create_response.json()["id"]
    
    # Trigger distribution
    response = client.post(f"/api/v1/articles/{article_id}/distribute")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "distribution" in data["results"]
    assert "seo" in data["results"]
    assert "monetization" in data["results"] 