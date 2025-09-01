import logging
import signal
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TEST
from aiogram.fsm.storage.mongo import MongoStorage
from motor.motor_asyncio import AsyncIOMotorClient

from app.bot_commands import set_bot_profile
from app.config import EnvironmentTypes, settings
from app.handlers.likes import router as likes_router
from app.handlers.matches import router as matches_router
from app.handlers.menu import router as menu_router
from app.handlers.profile import router as profile_router
from app.handlers.registration import router as registration_router
from app.handlers.search import router as search_router
from app.http_client import initialize_http_client, shutdown_http_client
from app.middlewares import i18n_middleware

logger = logging.getLogger(__name__)


class BotApplication:
    """Bot application with proper lifecycle management."""

    def __init__(self):
        self.bot: Bot | None = None
        self.dispatcher: Dispatcher | None = None
        self._is_running = False
        self._should_stop = False

    async def startup(self) -> None:
        """Initialize all bot components and dependencies."""
        logger.info("Starting bot application...")

        try:
            # Initialize HTTP client manager first
            logger.info("Initializing HTTP client manager...")
            await initialize_http_client(settings)
            logger.info("HTTP client manager initialized successfully")

            # Initialize bot instance
            self.bot = Bot(token=settings.bot_token)
            if EnvironmentTypes.testing == settings.environment:
                session = AiohttpSession(api=TEST)
                self.bot = Bot(token=settings.bot_token, session=session)

            # Set bot profile
            try:
                await set_bot_profile(self.bot)
                logger.info("Bot profile configured")
            except Exception as e:
                logger.warning(f"Failed to set bot profile: {e}")

            # Initialize MongoDB storage
            mongo = AsyncIOMotorClient(
                host=settings.mongo_url,
                uuidRepresentation="standard",
            )
            mongo_storage = MongoStorage(mongo)

            # Initialize dispatcher
            self.dispatcher = Dispatcher(storage=mongo_storage)

            # Setup middleware
            i18n_middleware.setup(self.dispatcher)
            logger.info("I18n middleware configured")

            # Register routers
            self.dispatcher.include_router(registration_router)
            self.dispatcher.include_router(menu_router)
            self.dispatcher.include_router(search_router)
            self.dispatcher.include_router(likes_router)
            self.dispatcher.include_router(profile_router)
            self.dispatcher.include_router(matches_router)

            logger.info("Bot application startup completed successfully")

        except Exception as e:
            logger.error(f"Failed to start bot application: {e}")
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """Properly shutdown all bot components and clean up resources."""
        logger.info("Shutting down bot application...")

        try:
            # Stop polling if running
            if self._is_running and self.dispatcher:
                self._should_stop = True
                logger.info("Stopping bot polling...")

            # Close bot session
            if self.bot:
                await self.bot.session.close()
                logger.info("Bot session closed")

            # Shutdown HTTP client manager
            await shutdown_http_client()
            logger.info("HTTP client manager shut down")

            logger.info("Bot application shutdown completed")

        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}")

    async def run_polling(self) -> None:
        """Run the bot with polling and proper shutdown handling."""
        if not self.bot or not self.dispatcher:
            raise RuntimeError("Bot application not initialized. Call startup() first.")

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum: int, frame: Any) -> None:
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self._should_stop = True

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            self._is_running = True
            logger.info("Starting bot polling...")

            logger.debug(f"Bot token: {self.bot.token}")
            # Start polling with proper shutdown handling
            await self.dispatcher.start_polling(
                self.bot,
                close_bot_session=False,  # We handle session closing manually
            )

        except Exception as e:
            logger.error(f"Error during bot polling: {e}")
            raise
        finally:
            self._is_running = False

    async def run(self) -> None:
        """Run the complete bot lifecycle: startup -> polling -> shutdown."""
        try:
            await self.startup()
            await self.run_polling()
        finally:
            await self.shutdown()


async def run_bot() -> None:
    """Convenience function to run the bot with full lifecycle management."""
    app = BotApplication()
    await app.run()
