import logging
from datetime import datetime, UTC
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "UP RERA Scraper",
        "status": "healthy2",
        "timestamp": datetime.now(UTC).isoformat(),
    }
