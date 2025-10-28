import os
from agents import Agent, Runner, trace
from agents.extensions.models.litellm_model import LitellmModel
from .mcp_servers import create_playwright_mcp_server
from .context import get_agent_instructions


async def run_up_rera_scraper_agent() -> str:
    """Run the UP RERA Scraper Agent with optional topic."""

    os.environ["AWS_REGION_NAME"] = os.environ.get(
        "REGION", "ap-south-1")  # LiteLLM's preferred variable
    os.environ["AWS_REGION"] = os.environ.get(
        "REGION", "ap-south-1")  # Boto3 standard
    os.environ["AWS_DEFAULT_REGION"] = os.environ.get(
        "REGION", "ap-south-1")  # Fallback

    MODEL = os.environ.get(
        "LLM_MODEL", "bedrock/anthropic.claude-3-haiku-20240307-v1:0")
    print(f"Using LLM Model: {MODEL}")
    model = LitellmModel(model=MODEL)

    with trace("UP RERA Scraper Agent Execution"):
        async with create_playwright_mcp_server(timeout_seconds=60) as playwright_mcp:
            query = f"Scrape real estate listings from UP RERA website."

            up_rera_agent = Agent(
                name="UP RERA Scraper Agent",
                instructions=get_agent_instructions(),
                model=model,
                mcp_servers=[playwright_mcp])

            result = await Runner.run(up_rera_agent, input=query, max_turns=15)

    return result.final_output
