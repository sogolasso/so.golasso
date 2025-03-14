from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.models.article import Article
from app.schemas.article import ArticleCreate, ArticleInDB, ArticleList, ArticleUpdate
from app.models.enums import ArticleStatus
from datetime import datetime, timedelta
import random

router = APIRouter()

@router.get("/articles/", response_model=ArticleList)
def list_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all published articles with optional category filtering and pagination.
    """
    query = db.query(Article).filter(Article.status == ArticleStatus.PUBLISHED)
    
    if category:
        query = query.filter(Article.category == category)
    
    total = query.count()
    articles = query.order_by(desc(Article.published_at)).offset(skip).limit(limit).all()
    
    return ArticleList(items=articles, total=total)

@router.get("/articles/{slug}", response_model=ArticleInDB)
def get_article(slug: str, db: Session = Depends(get_db)):
    """
    Get a specific article by its slug.
    """
    article = db.query(Article).filter(
        Article.slug == slug,
        Article.status == ArticleStatus.PUBLISHED
    ).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return article

@router.get("/categories/", response_model=List[str])
def list_categories(db: Session = Depends(get_db)):
    """
    List all available categories of published articles.
    """
    categories = db.query(Article.category).filter(
        Article.status == ArticleStatus.PUBLISHED
    ).distinct().all()
    return [category[0] for category in categories]

@router.get("/articles/category/{category}", response_model=ArticleList)
def list_articles_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List published articles filtered by category.
    """
    query = db.query(Article).filter(
        Article.status == ArticleStatus.PUBLISHED,
        Article.category == category
    )
    
    total = query.count()
    articles = query.order_by(desc(Article.published_at)).offset(skip).limit(limit).all()
    
    return ArticleList(items=articles, total=total)

@router.post("/test/add-articles/")
def add_test_articles(db: Session = Depends(get_db)):
    """
    Add test articles to the database.
    """
    try:
        # Categories for test articles
        categories = ["Notícias", "Análises", "Opinião", "Memes", "Táticas"]
        
        # Sample titles and content
        titles = [
            "Palmeiras vence clássico com gol nos acréscimos",
            "Análise tática: Como o Flamengo venceu o Derby",
            "Opinião: O futuro do futebol brasileiro",
            "Meme do dia: Torcedor dormindo no estádio",
            "Táticas: Como o 4-3-3 está dominando o futebol"
        ]
        
        # Add 10 test articles
        added_articles = []
        for i in range(10):
            category = random.choice(categories)
            title = random.choice(titles)
            article = Article(
                title=title,
                slug=f"test-article-{i+1}",
                content=f"Este é um artigo de teste {i+1} na categoria {category}. Aqui vai o conteúdo do artigo...",
                category=category,
                author_style="NARRACAO",
                status=ArticleStatus.PUBLISHED,
                published_at=datetime.utcnow() - timedelta(days=i),
                created_at=datetime.utcnow() - timedelta(days=i+1),
                updated_at=datetime.utcnow() - timedelta(days=i)
            )
            db.add(article)
            added_articles.append({"title": title, "category": category})
        
        db.commit()
        return {"message": "Test articles added successfully!", "articles": added_articles}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 