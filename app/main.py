import asyncio
import logging

from app.app import run_bot

# Configure logging for the bot service
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the bot service."""
    logger.info("Starting AnorDating Bot Service...")

    try:
        await run_bot()
    except KeyboardInterrupt:
        logger.info("Bot service interrupted by user")
    except Exception as e:
        logger.error(f"Bot service failed with error: {e}")
        raise
    finally:
        logger.info("Bot service shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
