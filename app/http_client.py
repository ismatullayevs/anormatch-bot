import logging
from typing import Any

import httpx

from app.config import BotSettings

logger = logging.getLogger(__name__)


class HTTPClientManager:
    """HTTP client manager with connection pooling and lifecycle management.

    Provides a single httpx.AsyncClient instance with optimized connection pooling
    for efficient API communication. Handles startup/shutdown lifecycle and
    automatic header injection.
    """

    def __init__(self, config: BotSettings):
        self._client: httpx.AsyncClient | None = None
        self._config = config
        self._is_initialized = False

    async def startup(self) -> None:
        """Initialize the HTTP client with connection pooling and base configuration.

        Should be called during bot application startup.
        """
        if self._is_initialized:
            logger.warning("HTTP client manager already initialized")
            return

        try:
            # Configure connection pooling for optimal performance
            limits = httpx.Limits(
                max_keepalive_connections=20,  # Keep 20 connections alive
                max_connections=100,  # Maximum 100 concurrent connections
                keepalive_expiry=30.0,  # Keep connections alive for 30 seconds
            )

            # Configure timeouts for reliable API communication
            timeout = httpx.Timeout(
                connect=10.0,  # 10 seconds to establish connection
                read=30.0,  # 30 seconds to read response
                write=10.0,  # 10 seconds to write request
                pool=5.0,  # 5 seconds to get connection from pool
            )

            # Base headers for all requests
            headers = {
                "X-Internal-Token": self._config.internal_token,
                "User-Agent": "AnorDating-Bot/1.0",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            self._client = httpx.AsyncClient(
                base_url=self._config.api_url,
                limits=limits,
                timeout=timeout,
                headers=headers,
                follow_redirects=True,
            )

            self._is_initialized = True
            logger.info(
                f"HTTP client initialized successfully. "
                f"Base URL: {self._config.api_url}, "
                f"Max connections: {limits.max_connections}, "
                f"Keepalive: {limits.max_keepalive_connections}",
            )

        except Exception as e:
            logger.error(f"Failed to initialize HTTP client: {e}")
            raise

    async def shutdown(self) -> None:
        """Properly close the HTTP client and clean up connections.

        Should be called during bot application shutdown.
        """
        if not self._is_initialized:
            logger.warning("HTTP client manager not initialized")
            return

        try:
            if self._client:
                await self._client.aclose()
                self._client = None

            self._is_initialized = False
            logger.info("HTTP client shutdown successfully")

        except Exception as e:
            logger.error(f"Error during HTTP client shutdown: {e}")
            raise

    def get_client(self) -> httpx.AsyncClient:
        """Get the shared HTTP client instance.

        Returns:
            httpx.AsyncClient: The configured HTTP client

        Raises:
            RuntimeError: If client is not initialized

        """
        if not self._is_initialized or not self._client:
            raise RuntimeError("HTTP client not initialized. Call startup() first.")

        return self._client

    async def request(
        self,
        method: str,
        url: str,
        telegram_user_id: int | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request with automatic header injection.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: URL path (relative to base URL)
            telegram_user_id: Telegram user ID for X-Telegram-User-Id header
            **kwargs: Additional arguments to pass to the request

        Returns:
            httpx.Response: The HTTP response

        Raises:
            RuntimeError: If client is not initialized
            httpx.RequestError: For network-related errors
            httpx.HTTPStatusError: For HTTP error status codes

        """
        client = self.get_client()

        # Inject telegram user ID header if provided
        if telegram_user_id is not None:
            headers = kwargs.get("headers", {})
            headers["X-Telegram-User-Id"] = str(telegram_user_id)
            kwargs["headers"] = headers

        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response  # noqa: TRY300

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP {e.response.status_code} error for {method} {url}: "
                f"{e.response.text}",
            )
            raise

        except httpx.RequestError as e:
            logger.error(f"Request error for {method} {url}: {e}")
            raise

    async def get(
        self,
        url: str,
        telegram_user_id: int | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Convenience method for GET requests."""
        return await self.request("GET", url, telegram_user_id, **kwargs)

    async def post(
        self,
        url: str,
        telegram_user_id: int | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Convenience method for POST requests."""
        return await self.request("POST", url, telegram_user_id, **kwargs)

    async def put(
        self,
        url: str,
        telegram_user_id: int | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Convenience method for PUT requests."""
        return await self.request("PUT", url, telegram_user_id, **kwargs)

    async def delete(
        self,
        url: str,
        telegram_user_id: int | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Convenience method for DELETE requests."""
        return await self.request("DELETE", url, telegram_user_id, **kwargs)

    @property
    def is_initialized(self) -> bool:
        """Check if the HTTP client is initialized."""
        return self._is_initialized

    async def health_check(self) -> bool:
        """Perform a simple health check against the API.

        Returns:
            bool: True if API is reachable, False otherwise

        """
        try:
            client = self.get_client()
            response = await client.get("/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False


# Global instance placeholder - will be initialized in the app factory
http_client_manager: HTTPClientManager | None = None


def get_http_client_manager() -> HTTPClientManager:
    """Get the global HTTP client manager instance.

    Returns:
        HTTPClientManager: The global HTTP client manager

    Raises:
        RuntimeError: If the manager is not initialized

    """
    if http_client_manager is None:
        raise RuntimeError(
            "HTTP client manager not initialized. "
            "Initialize it in the application startup.",
        )
    return http_client_manager


async def initialize_http_client(config: BotSettings) -> HTTPClientManager:
    """Initialize the global HTTP client manager.

    Args:
        config: Bot configuration settings

    Returns:
        HTTPClientManager: The initialized HTTP client manager

    """
    global http_client_manager

    if http_client_manager is not None:
        logger.warning(
            "HTTP client manager already exists, shutting down previous instance",
        )
        await http_client_manager.shutdown()

    http_client_manager = HTTPClientManager(config)
    await http_client_manager.startup()
    return http_client_manager


async def shutdown_http_client() -> None:
    """Shutdown the global HTTP client manager."""
    global http_client_manager

    if http_client_manager is not None:
        await http_client_manager.shutdown()
        http_client_manager = None
