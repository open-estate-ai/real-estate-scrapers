from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from .healthz import router as healthz_router
from .agent import router as agent_router
# Load environment
load_dotenv(override=True)


def create_app() -> FastAPI:

    app = FastAPI(title="UP RERA Scraper",
                  description="API for UP RERA real estate data scraping",
                  version="1.0.0")

    app.include_router(healthz_router, prefix="/healthz", tags=["healthz"])
    app.include_router(agent_router, prefix="/agent", tags=["agent"])
    return app
