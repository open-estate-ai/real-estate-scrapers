import logging
from datetime import datetime, UTC
from fastapi import APIRouter, Query
from .agent import run_up_rera_scraper_agent

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def run_agent(
    max_projects: int = Query(
        default=20, description="Maximum number of projects to scrape")
):
    """Run the UP RERA Scraper Agent.

    S3 bucket and prefix are configured via environment variables:
    - S3_BUCKET: S3 bucket name for upload (optional)
    - S3_PREFIX: S3 key prefix (default: "up-rera-projects")

    Args:
        max_projects: Number of projects to scrape (default: 20)

    Examples:
        - Basic scraping: GET /?max_projects=50
        - Scrape and upload: Set S3_BUCKET env var, then GET /?max_projects=50
    """
    result = await run_up_rera_scraper_agent(max_projects=max_projects)
    logger.info("Scraping result: %s", result)
    return {
        "service": "UP RERA Scraper",
        "status": "success",
        "timestamp": datetime.now(UTC).isoformat(),
        "max_projects": max_projects,
        "agent_response": result,  # Human-readable formatted response from agent
    }
