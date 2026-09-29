from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health():
    """Health endpoint for API versioned routes."""
    return {"status": "ok"}
