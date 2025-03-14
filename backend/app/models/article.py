from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime
from app.models.enums import ArticleStatus, AuthorStyle

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    summary = Column(Text)
    category = Column(String, index=True)
    author_name = Column(String)
    author_style = Column(Enum(AuthorStyle), default=AuthorStyle.NARRACAO)
    source_url = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    status = Column(Enum(ArticleStatus), default=ArticleStatus.DRAFT)
    featured_image = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    excerpt = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    team_tags = Column(JSON, default=list)
    player_tags = Column(JSON, default=list)
    is_featured = Column(Boolean, default=False)
    is_trending = Column(Boolean, default=False)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    comments = Column(JSON, default=list)

    def __repr__(self):
        return f"<Article {self.title} by {self.author_name}>" 