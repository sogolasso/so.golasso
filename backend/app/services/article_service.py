from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import Depends
from app.models.article import Article as ArticleModel
from app.schemas.article import ArticleCreate, ArticleUpdate, ARTICLE_AUTHORS, AuthorStyle
from app.core.database import get_db
from app.core.security import generate_slug
from datetime import datetime
import uuid
import random

class ArticleService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def _select_author(self, category: str) -> tuple[AuthorStyle, str]:
        """Select an appropriate author based on article category."""
        if category in ['tactical', 'team_update']:
            style = AuthorStyle.TATICO
        elif category == 'meme':
            style = AuthorStyle.ZOACAO
        else:  # match_result, transfer, rumor
            style = AuthorStyle.NARRACAO
        
        # Randomly select an author from the appropriate list
        author_name = random.choice(ARTICLE_AUTHORS[style])
        return style, author_name

    async def get_articles(
        self,
        skip: int = 0,
        limit: int = 10,
        category: Optional[str] = None,
        team: Optional[str] = None,
        is_trending: Optional[bool] = None,
        author_style: Optional[AuthorStyle] = None
    ) -> List[ArticleModel]:
        query = self.db.query(ArticleModel)
        
        if category:
            query = query.filter(ArticleModel.category == category)
        if team:
            query = query.filter(ArticleModel.team_tags.contains([team]))
        if is_trending is not None:
            query = query.filter(ArticleModel.is_trending == is_trending)
        if author_style:
            query = query.filter(ArticleModel.author_style == author_style)
        
        return query.order_by(ArticleModel.created_at.desc()).offset(skip).limit(limit).all()

    async def get_trending_articles(self, limit: int = 10) -> List[ArticleModel]:
        return (
            self.db.query(ArticleModel)
            .filter(ArticleModel.is_trending == True)
            .order_by(
                ArticleModel.views_count.desc(),
                ArticleModel.likes_count.desc(),
                ArticleModel.created_at.desc()
            )
            .limit(limit)
            .all()
        )

    async def get_article(self, article_id: str) -> Optional[ArticleModel]:
        return self.db.query(ArticleModel).filter(ArticleModel.id == article_id).first()

    async def create_article(self, article: ArticleCreate) -> ArticleModel:
        # Select appropriate author if not provided
        if not article.author_style or not article.author_name:
            style, name = self._select_author(article.category)
            article_dict = article.dict()
            article_dict["author_style"] = style
            article_dict["author_name"] = name
        else:
            article_dict = article.dict()

        db_article = ArticleModel(
            id=str(uuid.uuid4()),
            slug=generate_slug(article.title),
            **article_dict,
            created_at=datetime.utcnow()
        )
        self.db.add(db_article)
        self.db.commit()
        self.db.refresh(db_article)
        return db_article

    async def update_article(
        self,
        article_id: str,
        article: ArticleUpdate
    ) -> Optional[ArticleModel]:
        db_article = await self.get_article(article_id)
        if not db_article:
            return None

        update_data = article.dict(exclude_unset=True)
        
        # Update author if category changes
        if "category" in update_data and "author_style" not in update_data:
            style, name = self._select_author(update_data["category"])
            update_data["author_style"] = style
            update_data["author_name"] = name

        if "title" in update_data:
            update_data["slug"] = generate_slug(update_data["title"])
        
        for field, value in update_data.items():
            setattr(db_article, field, value)
        
        db_article.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_article)
        return db_article

    async def delete_article(self, article_id: str) -> bool:
        db_article = await self.get_article(article_id)
        if not db_article:
            return False
        
        self.db.delete(db_article)
        self.db.commit()
        return True

    async def toggle_like(self, article_id: str, user_id: str) -> bool:
        db_article = await self.get_article(article_id)
        if not db_article:
            return False
        
        # In a real application, you would check if the user has already liked
        # the article and toggle accordingly. This is a simplified version.
        db_article.likes_count += 1
        self.db.commit()
        return True

    async def add_comment(
        self,
        article_id: str,
        user_id: str,
        content: str
    ) -> bool:
        db_article = await self.get_article(article_id)
        if not db_article:
            return False
        
        # Create and add comment
        comment = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "content": content,
            "created_at": datetime.utcnow()
        }
        db_article.comments.append(comment)
        db_article.comments_count += 1
        self.db.commit()
        return True 