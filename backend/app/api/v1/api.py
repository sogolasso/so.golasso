from fastapi import APIRouter

api_router = APIRouter()

# Add your API endpoints here
@api_router.get("/health")
async def health_check():
    return {"status": "ok"} 