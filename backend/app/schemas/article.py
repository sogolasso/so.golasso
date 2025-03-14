from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from app.models.enums import ArticleStatus, AuthorStyle

# Predefined authors by style
ARTICLE_AUTHORS = {
    AuthorStyle.NARRACAO.value: [
        "Pelétrico Silva",
        "Garrincha Lopes",
        "Galvão Romário"
    ],
    AuthorStyle.TATICO.value: [
        "Sócrates do Tático",
        "Didi Estratégico",
        "Tafarel de Dados"
    ],
    AuthorStyle.ZOACAO.value: [
        "Romito Zoando",
        "Ronaldo FenôMeme",
        "NeyJoga e Cai"
    ]
}

class Author(BaseModel):
    name: str
    style: AuthorStyle

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

class Comment(CommentBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ArticleBase(BaseModel):
    title: str
    content: str
    summary: str
    category: str
    author_style: AuthorStyle = AuthorStyle.NARRACAO
    author_name: str
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    featured_image: Optional[str] = None
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    team_tags: List[str] = []
    player_tags: List[str] = []
    is_featured: bool = False
    is_trending: bool = False

class ArticleCreate(ArticleBase):
    slug: str
    status: ArticleStatus = ArticleStatus.DRAFT
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    published_at: Optional[datetime] = None

class ArticleUpdate(ArticleBase):
    slug: Optional[str] = None
    status: Optional[ArticleStatus] = None
    updated_at: datetime = datetime.utcnow()
    published_at: Optional[datetime] = None

class ArticleInDB(ArticleBase):
    id: int
    slug: str
    status: ArticleStatus
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    views_count: int = 0

    class Config:
        from_attributes = True

class ArticleList(BaseModel):
    items: List[ArticleInDB]
    total: int 