from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.models.article import Article
from app.schemas.article import ArticleCreate, ArticleInDB, ArticleList, ArticleUpdate
from app.models.enums import ArticleStatus

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