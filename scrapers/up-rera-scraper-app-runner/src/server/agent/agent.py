import os
import logging
from typing import Optional
from agents import Agent, Runner, trace
from agents.extensions.models.litellm_model import LitellmModel
from agents.mcp import MCPServerStdio
from .context import get_agent_instructions, get_default_query
from .tools import ingest_scraped_data, upload_to_s3
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[AGENT] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_up_rera_scraper_agent(max_projects: int = 20) -> str:
    """Run the UP RERA Scraper Agent with optional S3 upload.

    S3 configuration is read from environment variables:
    - S3_BUCKET: S3 bucket name for upload (optional). If not set, only scrapes and verifies.
    - S3_PREFIX: S3 key prefix for organizing data (default: "up-rera-projects")

    Args:
        max_projects: Maximum number of projects to scrape (default: 20)
    """
    # Read S3 configuration from environment variables
    s3_bucket = os.environ.get("S3_BUCKET")
    s3_prefix = os.environ.get("S3_PREFIX", "up-rera-projects")

    logger.info(f"🔧 Configuration:")
    logger.info(f"   Max Projects: {max_projects}")
    logger.info(f"   S3 Bucket: {s3_bucket or 'Not configured (no upload)'}")
    logger.info(f"   S3 Prefix: {s3_prefix}")

    os.environ["AWS_REGION_NAME"] = os.environ.get(
        "REGION", "us-east-1")  # LiteLLM's preferred variable
    os.environ["AWS_REGION"] = os.environ.get(
        "REGION", "us-east-1")  # Boto3 standard
    os.environ["AWS_DEFAULT_REGION"] = os.environ.get(
        "REGION", "us-east-1")  # Fallback

    MODEL = os.environ.get(
        "LLM_MODEL", "bedrock/anthropic.claude-3-haiku-20240307-v1:0")
    logger.info(f"🤖 Using LLM Model: {MODEL}")

    model = LitellmModel(model=MODEL)

    with trace("UP RERA Scraper Agent Execution"):

        params = {"command": "uv", "args": [
            "run", "./src/server/agent/mcp_servers.py"]}
        # Increase timeout to 300 seconds (5 minutes) for slow scraping
        async with MCPServerStdio(params=params, client_session_timeout_seconds=300) as mcp_server:
            logger.info("✅ Started mcp_servers MCP server")

            # Build query based on parameters
            query = get_default_query(
                max_projects=max_projects,
                s3_bucket=s3_bucket,
                s3_prefix=s3_prefix
            )
            logger.info(f"📝 Query: {query}")

            mcp_tools = await mcp_server.list_tools()
            logger.info(
                f"🛠️  Available MCP Tools: {[tool.name for tool in mcp_tools]}")

            logger.info("🚀 Creating agent and starting execution...")
            up_rera_agent = Agent(
                name="UP RERA Scraper Agent",
                instructions=get_agent_instructions(),
                model=model,
                tools=[ingest_scraped_data, upload_to_s3],
                mcp_servers=[mcp_server])

            logger.info(
                "⏳ Running agent (this may take 1-2 minutes for scraping)...")
            result = await Runner.run(up_rera_agent, input=query, max_turns=15)
            logger.info("✅ Agent execution completed")

    logger.info("🎉 UP RERA Scraper Agent run completed")
    logger.info(
        f"📊 Final Output (first 500 chars): {str(result.final_output)[:500]}")
    return result.final_output
