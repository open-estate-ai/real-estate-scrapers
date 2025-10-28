from src.server import create_app
import logging


logging.basicConfig(level="INFO")
app = create_app()
logging.getLogger().info("FastAPI app created and module loaded")
