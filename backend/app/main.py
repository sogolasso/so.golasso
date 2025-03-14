from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import articles
from app.db.session import engine
from app.models import article

# Create database tables
article.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(articles.router, prefix=settings.API_V1_STR, tags=["articles"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Só Golasso API",
        "docs": "/docs",
        "redoc": "/redoc"
    } 