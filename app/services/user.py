import logging
from uuid import UUID

from app.http_client import get_http_client_manager
from app.schemas.user import UserSchema, UserUpdateSchema

logger = logging.getLogger(__name__)


async def get_user(user_id: UUID) -> UserSchema:
    """Get a user by ID.

    Args:
        user_id: UUID of the user to fetch

    Returns:
        UserSchema: The user data

    """
    http_client = get_http_client_manager()
    response = await http_client.get(f"/v1/users/{user_id}")
    logger.debug(f"User {user_id} fetched from API")
    return UserSchema.model_validate(response.json())


async def get_current_user(telegram_id: int) -> UserSchema:
    """Get the current user.

    Args:
        telegram_id: Telegram user ID

    Returns:
        UserSchema: The current user data

    """
    http_client = get_http_client_manager()
    response = await http_client.get(
        "/v1/users/me",
        telegram_user_id=telegram_id,
    )
    logger.debug(f"Current user {telegram_id} fetched from API")
    return UserSchema.model_validate(response.json())


async def update_user(
    telegram_id: int,
    user_data: UserUpdateSchema,
) -> UserSchema:
    """Update user data.

    Args:
        telegram_id: Telegram user ID
        user_data: Updated user data

    Returns:
        UserSchema: The updated user data

    """
    http_client = get_http_client_manager()
    response = await http_client.put(
        "/v1/users/me",
        telegram_user_id=telegram_id,
        json=user_data.model_dump(exclude_unset=True, mode="json"),
    )
    logger.debug(f"User {telegram_id} updated successfully")
    return UserSchema.model_validate(response.json())


async def delete_user(telegram_id: int) -> None:
    """Delete user.

    Args:
        telegram_id: Telegram user ID

    Returns:
        None

    Raises:
        httpx.HTTPStatusError: If the API request fails

    """
    http_client = get_http_client_manager()
    response = await http_client.delete(
        "/v1/users/me",
        telegram_user_id=telegram_id,
    )
    response.raise_for_status()

    logger.debug(f"User {telegram_id} deleted successfully")


async def is_user_banned(telegram_id: int) -> bool:
    """Check if a user is currently banned.

    Args:
        telegram_id: Telegram user ID

    Returns:
        bool: True if the user is banned, False otherwise

    """
    http_client = get_http_client_manager()
    response = await http_client.get(
        f"/v1/bans/check/{telegram_id}",
        telegram_user_id=telegram_id,
    )
    response.raise_for_status()
    ban_status = response.json()
    logger.debug(f"Ban status for user {telegram_id}: {ban_status}")
    return ban_status.get("is_banned", False)
