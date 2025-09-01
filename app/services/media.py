import contextlib
import logging
from uuid import UUID

import httpx
from aiogram.utils.i18n import gettext as _

from bot.http_client import get_http_client_manager
from bot.schemas.media import FileSchema

logger = logging.getLogger(__name__)


async def get_media(user_id: UUID) -> list[FileSchema]:
    """Fetch media files for a user.

    Args:
        user_id: UUID of the user whose media to fetch

    Returns:
        list[FileSchema]: List of user's media files

    Raises:
        ValueError: If API call fails or user not found

    """
    http_client = get_http_client_manager()
    response = await http_client.get(
        "/v1/media",
        params={"user_id": str(user_id)},
    )
    media_list = [FileSchema.model_validate(file) for file in response.json()]

    logger.debug(f"Fetched {len(media_list)} media files for user {user_id}")
    return media_list


async def get_user_media(telegram_user_id: int) -> list[FileSchema]:
    """Fetch media files for the current authenticated user.

    Args:
        telegram_user_id: Telegram user ID

    Returns:
        list[FileSchema]: List of user's media files

    Raises:
        ValueError: If API call fails or authentication error

    """
    # Get current user first to get their UUID
    from bot.services.user import get_current_user

    user = await get_current_user(telegram_user_id)
    media_list = await get_media(user.id)

    logger.debug(
        f"Fetched {len(media_list)} media files for telegram user {telegram_user_id}",
    )
    return media_list


def validate_media_list(media_list: list[FileSchema]) -> bool:
    """Validate a list of media files.

    Args:
        media_list: List of media files to validate

    Returns:
        bool: True if valid, False otherwise

    Raises:
        ValueError: If validation fails with specific error message

    """
    if not media_list:
        raise ValueError(_("At least one media file is required"))

    if len(media_list) > 10:  # Max from bot config
        raise ValueError(_("Too many media files. Maximum 10 allowed."))

    # Check for duplicate telegram IDs
    telegram_ids = [media.telegram_id for media in media_list if media.telegram_id]
    if len(telegram_ids) != len(set(telegram_ids)):
        raise ValueError(_("Duplicate media files detected"))

    # Validate individual files
    for media in media_list:
        if not media.telegram_id:
            raise ValueError(_("Media file missing telegram ID"))

        # Basic file type validation
        if media.file_type not in ["image", "video", "audio", "document", "other"]:
            raise ValueError(
                _("Invalid file type: {type}").format(type=media.file_type),
            )

    logger.debug(f"Validated {len(media_list)} media files successfully")
    return True


async def batch_add_media(
    telegram_user_id: int,
    media_data: list[dict],
) -> list[FileSchema]:
    """Add multiple media files for a user.

    Args:
        telegram_user_id: Telegram user ID
        media_data: List of media file data dictionaries

    Returns:
        list[FileSchema]: List of added media files

    Raises:
        ValueError: If API call fails

    """
    http_client = get_http_client_manager()
    response = await http_client.post(
        "/v1/media/batch-add",
        telegram_user_id=telegram_user_id,
        json=media_data,
    )
    media_list = [FileSchema.model_validate(file) for file in response.json()]

    logger.debug(
        f"Added {len(media_list)} media files for telegram user {telegram_user_id}",
    )
    return media_list


async def replace_all_media(
    telegram_user_id: int,
    media_data: list[dict],
) -> list[FileSchema]:
    """Replace all media files for a user.

    This deletes all existing media and adds the new media files.

    Args:
        telegram_user_id: Telegram user ID
        media_data: List of new media file data dictionaries

    Returns:
        list[FileSchema]: List of new media files

    Raises:
        ValueError: If API call fails

    """
    http_client = get_http_client_manager()

    # First, get current media to delete
    current_media = await get_user_media(telegram_user_id)

    # Delete all current media
    for media_file in current_media:
        if media_file.id:
            with contextlib.suppress(httpx.HTTPStatusError):
                await http_client.delete(
                    f"/v1/media/{media_file.id}",
                    telegram_user_id=telegram_user_id,
                )

    # Add new media
    return await batch_add_media(telegram_user_id, media_data)
