import logging
from uuid import UUID

import httpx
from aiogram.utils.i18n import gettext as _

from bot.http_client import get_http_client_manager
from bot.schemas.reaction import ReactionInSchema, ReactionSchema
from bot.schemas.user import UserSchema

logger = logging.getLogger(__name__)


async def get_matches(
    telegram_id: int,
    limit: int = 10,
    offset: int = 0,
) -> list[UserSchema]:
    """Fetch matches for a user.

    Args:
        telegram_id: Telegram user ID
        limit: Maximum number of matches to return
        offset: Pagination offset

    Returns:
        list[UserSchema]: List of matched users

    Raises:
        ValueError: If API call fails

    """
    try:
        http_client = get_http_client_manager()
        response = await http_client.get(
            "/v1/matches",
            telegram_user_id=telegram_id,
            params={"limit": limit, "offset": offset},
        )
        matches = [UserSchema.model_validate(user) for user in response.json()]

        logger.debug(f"Fetched {len(matches)} matches for user {telegram_id}")
        return matches

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.info(f"No matches found for user {telegram_id}")
            return []
        if e.response.status_code == 401:
            logger.warning(f"Authentication failed for user {telegram_id}")
            raise ValueError(_("Authentication failed. Please try again."))
        if e.response.status_code == 403:
            logger.warning(f"Access forbidden for user {telegram_id}")
            raise ValueError(_("Access denied. Please check your account status."))
        logger.error(f"HTTP error fetching matches for user {telegram_id}: {e}")
        raise ValueError(
            _("Unable to fetch matches. Please try again later."),
        )

    except httpx.RequestError as e:
        logger.error(f"Network error fetching matches for user {telegram_id}: {e}")
        raise ValueError(_("Network error. Please check your connection."))

    except Exception as e:
        logger.error(f"Unexpected error fetching matches for user {telegram_id}: {e}")
        raise ValueError(_("An unexpected error occurred. Please try again."))


async def get_best_match(telegram_id: int) -> UserSchema | None:
    """Fetch the best match for the current user.

    Args:
        telegram_id: Telegram user ID

    Returns:
        UserSchema | None: Best match user or None if no matches

    Raises:
        ValueError: If API call fails

    """
    try:
        http_client = get_http_client_manager()
        response = await http_client.get(
            "/v1/matches/find",
            telegram_user_id=telegram_id,
        )

        if not response.json():
            logger.info(f"No best match found for user {telegram_id}")
            return None

        best_match = UserSchema.model_validate(response.json())
        logger.debug(f"Found best match for user {telegram_id}")
        return best_match

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.info(f"No best match found for user {telegram_id}")
            return None
        if e.response.status_code == 401:
            logger.warning(f"Authentication failed for user {telegram_id}")
            raise ValueError(_("Authentication failed. Please try again."))
        if e.response.status_code == 403:
            logger.warning(f"Access forbidden for user {telegram_id}")
            raise ValueError(_("Access denied. Please check your account status."))
        logger.error(f"HTTP error fetching best match for user {telegram_id}: {e}")
        raise ValueError(
            _("Unable to find matches. Please try again later."),
        )

    except httpx.RequestError as e:
        logger.error(f"Network error fetching best match for user {telegram_id}: {e}")
        raise ValueError(_("Network error. Please check your connection."))

    except Exception as e:
        logger.error(
            f"Unexpected error fetching best match for user {telegram_id}: {e}",
        )
        raise ValueError(_("An unexpected error occurred. Please try again."))


async def get_likes(telegram_id: int, limit: int) -> list[UserSchema]:
    """Fetch the likes for the current user.

    Args:
        telegram_id: Telegram user ID
        limit: Maximum number of likes to return

    Returns:
        list[UserSchema]: List of users who liked the current user

    Raises:
        ValueError: If API call fails

    """
    try:
        http_client = get_http_client_manager()
        response = await http_client.get(
            "/v1/likes",
            telegram_user_id=telegram_id,
            params={"limit": limit},
        )
        likes = [UserSchema.model_validate(user) for user in response.json()]

        logger.debug(f"Fetched {len(likes)} likes for user {telegram_id}")
        return likes

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.info(f"No likes found for user {telegram_id}")
            return []
        if e.response.status_code == 401:
            logger.warning(f"Authentication failed for user {telegram_id}")
            raise ValueError(_("Authentication failed. Please try again."))
        if e.response.status_code == 403:
            logger.warning(f"Access forbidden for user {telegram_id}")
            raise ValueError(_("Access denied. Please check your account status."))
        logger.error(f"HTTP error fetching likes for user {telegram_id}: {e}")
        raise ValueError(
            _("Unable to fetch likes. Please try again later."),
        )

    except httpx.RequestError as e:
        logger.error(f"Network error fetching likes for user {telegram_id}: {e}")
        raise ValueError(_("Network error. Please check your connection."))

    except Exception as e:
        logger.error(f"Unexpected error fetching likes for user {telegram_id}: {e}")
        raise ValueError(_("An unexpected error occurred. Please try again."))


async def get_rewinds(
    telegram_id: int,
    limit: int = 10,
    offset: int = 0,
) -> list[UserSchema]:
    """Fetch the rewinds for the current user.

    Args:
        telegram_id: Telegram user ID
        limit: Maximum number of rewinds to return
        offset: Pagination offset

    Returns:
        list[UserSchema]: List of users from rewind history

    Raises:
        ValueError: If API call fails

    """
    try:
        http_client = get_http_client_manager()
        response = await http_client.get(
            "/v1/rewinds",
            telegram_user_id=telegram_id,
            params={"limit": limit, "offset": offset},
        )
        rewinds = [UserSchema.model_validate(user) for user in response.json()]

        logger.debug(f"Fetched {len(rewinds)} rewinds for user {telegram_id}")
        return rewinds

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            logger.warning(f"Rewind limit exceeded for user {telegram_id}")
            raise ValueError(_("Rewind limit exceeded. Try again later."))
        if e.response.status_code == 404:
            logger.info(f"No rewinds found for user {telegram_id}")
            return []
        if e.response.status_code == 401:
            logger.warning(f"Authentication failed for user {telegram_id}")
            raise ValueError(_("Authentication failed. Please try again."))
        if e.response.status_code == 403:
            logger.warning(f"Access forbidden for user {telegram_id}")
            raise ValueError(_("Access denied. Please check your account status."))
        logger.error(f"HTTP error fetching rewinds for user {telegram_id}: {e}")
        raise ValueError(
            _("Unable to fetch rewind history. Please try again later."),
        )

    except httpx.RequestError as e:
        logger.error(f"Network error fetching rewinds for user {telegram_id}: {e}")
        raise ValueError(_("Network error. Please check your connection."))

    except Exception as e:
        logger.error(f"Unexpected error fetching rewinds for user {telegram_id}: {e}")
        raise ValueError(_("An unexpected error occurred. Please try again."))


async def create_or_update_reaction(
    user_telegram_id: int,
    reaction_data: ReactionInSchema,
) -> ReactionSchema:
    """React to a user (like/dislike).

    Args:
        user_telegram_id: Telegram ID of the user making the reaction
        reaction_data: Reaction data (target user and reaction type)

    Returns:
        ReactionSchema: Created or updated reaction

    Raises:
        ValueError: If API call fails

    """
    try:
        http_client = get_http_client_manager()
        response = await http_client.put(
            "/v1/reactions",
            telegram_user_id=user_telegram_id,
            json={
                "to_user_id": str(reaction_data.to_user_id),
                "reaction_type": reaction_data.reaction_type,
            },
        )
        reaction = ReactionSchema.model_validate(response.json())

        logger.info(
            f"User {user_telegram_id} reacted {reaction_data.reaction_type} "
            f"to user {reaction_data.to_user_id}",
        )
        return reaction

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            logger.warning(f"Invalid reaction data from user {user_telegram_id}")
            raise ValueError(_("Invalid reaction data. Please try again."))
        if e.response.status_code == 401:
            logger.warning(f"Authentication failed for user {user_telegram_id}")
            raise ValueError(_("Authentication failed. Please try again."))
        if e.response.status_code == 403:
            logger.warning(f"Access forbidden for user {user_telegram_id}")
            raise ValueError(_("Access denied. Please check your account status."))
        if e.response.status_code == 404:
            logger.warning(f"Target user {reaction_data.to_user_id} not found")
            raise ValueError(_("User not found. They may have been removed."))
        logger.error(f"HTTP error creating reaction for user {user_telegram_id}: {e}")
        raise ValueError(
            _("Unable to save your reaction. Please try again later."),
        )

    except httpx.RequestError as e:
        logger.error(
            f"Network error creating reaction for user {user_telegram_id}: {e}",
        )
        raise ValueError(_("Network error. Please check your connection."))

    except Exception as e:
        logger.error(
            f"Unexpected error creating reaction for user {user_telegram_id}: {e}",
        )
        raise ValueError(_("An unexpected error occurred. Please try again."))


async def check_match(user_telegram_id: int, match_id: UUID) -> bool:
    """Check if a match exists between two users.

    Args:
        user_telegram_id: Telegram ID of the current user
        match_id: UUID of the potential match user

    Returns:
        bool: True if users are matched, False otherwise

    Raises:
        ValueError: If API call fails

    """
    try:
        http_client = get_http_client_manager()
        response = await http_client.get(
            "/v1/matches/check",
            telegram_user_id=user_telegram_id,
            params={"match_id": str(match_id)},
        )
        is_match = response.json()["is_match"]

        logger.debug(
            f"Match check: user {user_telegram_id} and {match_id} = {is_match}",
        )
        return is_match

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.info(f"Match check: user {match_id} not found")
            return False
        if e.response.status_code == 401:
            logger.warning(f"Authentication failed for user {user_telegram_id}")
            raise ValueError(_("Authentication failed. Please try again."))
        if e.response.status_code == 403:
            logger.warning(f"Access forbidden for user {user_telegram_id}")
            raise ValueError(_("Access denied. Please check your account status."))
        logger.error(f"HTTP error checking match for user {user_telegram_id}: {e}")
        raise ValueError(
            _("Unable to check match status. Please try again later."),
        )

    except httpx.RequestError as e:
        logger.error(f"Network error checking match for user {user_telegram_id}: {e}")
        raise ValueError(_("Network error. Please check your connection."))

    except Exception as e:
        logger.error(
            f"Unexpected error checking match for user {user_telegram_id}: {e}",
        )
        raise ValueError(_("An unexpected error occurred. Please try again."))
