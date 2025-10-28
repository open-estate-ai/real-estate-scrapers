import logging
from datetime import datetime, UTC
from fastapi import APIRouter
from .agent import run_up_rera_scraper_agent

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def run_agent():
    """Run the UP RERA Scraper Agent."""

    result = await run_up_rera_scraper_agent()
    logger.info("Scraping result: %s", result)
    return {
        "service": "UP RERA Scraper",
        "status": "running",
        "timestamp": datetime.now(UTC).isoformat(),
    }
