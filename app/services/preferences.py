import logging

from app.http_client import get_http_client_manager
from app.schemas.preferences import (
    PreferencesInSchema,
    PreferencesSchema,
    PreferencesUpdateSchema,
)

logger = logging.getLogger(__name__)


async def get_preferences(telegram_user_id: int) -> PreferencesSchema:
    """Get user preferences.

    Args:
        telegram_user_id: Telegram user ID

    Returns:
        PreferencesSchema: The user's preferences

    Raises:
        ValueError: If preferences not found or API error

    """
    http_client = get_http_client_manager()
    response = await http_client.get(
        "/v1/preferences",
        telegram_user_id=telegram_user_id,
    )
    response_data = response.json()
    logger.debug(f"Preferences fetched for telegram user {telegram_user_id}")
    return PreferencesSchema(**response_data)


async def create_preferences(
    telegram_user_id: int,
    preferences_data: PreferencesInSchema,
) -> PreferencesSchema:
    """Create user preferences.

    Args:
        telegram_user_id: Telegram user ID
        preferences_data: Preferences data to create

    Returns:
        PreferencesSchema: The created preferences

    Raises:
        ValueError: If creation fails or validation error

    """
    http_client = get_http_client_manager()
    response = await http_client.post(
        "/v1/preferences",
        telegram_user_id=telegram_user_id,
        json=preferences_data.model_dump(exclude_unset=True, mode="json"),
    )
    response_data = response.json()
    created_preferences = PreferencesSchema(**response_data)

    logger.info(f"Preferences created for telegram user {telegram_user_id}")
    return created_preferences


async def update_preferences(
    telegram_user_id: int,
    preferences_data: PreferencesUpdateSchema,
) -> PreferencesSchema:
    """Update user preferences.

    Args:
        telegram_user_id: Telegram user ID
        preferences_data: Updated preferences data

    Returns:
        PreferencesSchema: The updated preferences

    Raises:
        ValueError: If update fails or validation error

    """
    http_client = get_http_client_manager()

    update_dict = preferences_data.model_dump(exclude_unset=True, mode="json")

    response = await http_client.put(
        "/v1/preferences",
        telegram_user_id=telegram_user_id,
        json=update_dict,
    )
    response_data = response.json()
    updated_preferences = PreferencesSchema(**response_data)

    logger.info(f"Preferences updated for telegram user {telegram_user_id}")
    return updated_preferences
