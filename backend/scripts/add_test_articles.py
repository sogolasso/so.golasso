from app.db.session import SessionLocal
from app.models.article import Article
from app.models.enums import ArticleStatus
from datetime import datetime, timedelta
import random

def add_test_articles():
    db = SessionLocal()
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
        
        db.commit()
        print("Test articles added successfully!")
        
    except Exception as e:
        print(f"Error adding test articles: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_articles() 