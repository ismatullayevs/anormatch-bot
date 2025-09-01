from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from bot.handlers.menu import show_menu
from bot.keyboards import get_search_keyboard
from bot.services.match import get_likes
from bot.services.media import get_media
from bot.services.user import get_current_user
from bot.states import AppStates
from bot.utils import get_profile_card

router = Router()


@router.message(AppStates.menu, F.text == __("👍 Likes"))
async def show_likes_with_keyboard(
    message: types.Message,
    state: FSMContext,
    from_user: types.User | None = None,
) -> None:
    """Show likes with keyboard."""
    await message.answer(_("Likes"), reply_markup=get_search_keyboard())
    await show_likes(message, state, from_user)


async def show_likes(
    message: types.Message,
    state: FSMContext,
    from_user: types.User | None = None,
) -> None:
    """Show likes."""
    from_user = from_user or message.from_user
    if not from_user:
        return None

    await state.update_data(match_id=None)
    await state.update_data(rewind_index=0)

    user = await get_current_user(from_user.id)

    likes = await get_likes(from_user.id, limit=1)
    if not likes:
        await message.answer(_("No likes found"))
        return await show_menu(message, state)

    match = likes[0]
    media = await get_media(match.id)
    profile = await get_profile_card(match, media, user)
    await state.update_data(match_id=match.id)
    await message.answer_media_group(profile)
    await state.set_state(AppStates.likes)
    return None
