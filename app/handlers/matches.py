import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from httpx import HTTPStatusError

from app.config import settings
from app.handlers.menu import show_menu
from app.keyboards import get_matches_keyboard
from app.services.match import get_matches
from app.services.media import get_media
from app.services.user import get_current_user
from app.states import AppStates
from app.utils import get_profile_card

router = Router()

logger = logging.getLogger(__name__)


@router.message(AppStates.matches, F.text.in_(["⬅️", "➡️"]))
@router.message(AppStates.menu, F.text == __("❤️ Matches"))
async def show_matches(
    message: types.Message,
    state: FSMContext,
    from_user: types.User | None = None,
) -> None:
    """Show matches for the user."""
    from_user = from_user or message.from_user
    if not from_user:
        return
    user = await get_current_user(from_user.id)

    index = 0 if message.text == _("❤️ Matches") else await state.get_value("index") or 0

    if message.text == "⬅️":
        index += 1
    elif message.text == "➡️" and index > 0:
        index -= 1

    has_previous, has_next = False, index > 0
    try:
        matches = await get_matches(user.telegram_id, limit=2, offset=index)
    except HTTPStatusError as e:
        logger.error(f"Failed to fetch matches for user {user.telegram_id}: {e}")
        await message.answer(_("Failed to fetch matches"))
        await show_menu(message, state)
        return
    if not matches:  # TODO: Return the last match instead
        await message.answer(_("No matches found"))
        await show_menu(message, state)
        return
    if len(matches) == 2:
        has_previous = True

    match = matches[0]
    media = await get_media(user_id=match.id)
    profile = await get_profile_card(match, media, user)
    await state.update_data(match_id=match.id)
    await message.answer_media_group(profile)

    await message.answer(
        _(
            "You both liked each other. Start a chat with"
            "them by clicking the button below 👇",
        ),
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=_("Start a chat"),
                        web_app=types.WebAppInfo(
                            url=f"{settings.app_url}/users/{match.id}/chat",
                        ),
                    ),
                ],
            ],
        ),
    )

    await message.answer(
        _("Matches"),
        reply_markup=get_matches_keyboard(has_previous, has_next),
    )

    await state.set_state(AppStates.matches)
    await state.update_data(index=index)
