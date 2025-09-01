import logging

import httpx
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from app.config import settings
from app.enums import ReactionType
from app.handlers.likes import show_likes, show_likes_with_keyboard
from app.handlers.matches import show_matches
from app.handlers.menu import show_menu
from app.keyboards import get_empty_search_keyboard, get_search_keyboard
from app.schemas.reaction import ReactionInSchema
from app.services.match import (
    create_or_update_reaction,
    get_best_match,
    get_rewinds,
)
from app.services.media import get_media
from app.services.user import get_current_user
from app.states import AppStates
from app.utils import get_profile_card

logger = logging.getLogger(__name__)

router = Router()


@router.message(AppStates.menu, F.text == __("🔎 Watch profiles"))
async def search_with_keyboard(message: types.Message, state: FSMContext) -> None:
    """Send a keyboard to the user to search for profiles."""
    await message.answer("🔎", reply_markup=get_search_keyboard())
    return await search(message, state)


async def search(
    message: types.Message,
    state: FSMContext,
) -> None:
    """Send a keyboard to the user to search for profiles."""
    if not message.from_user:
        return None

    await state.update_data(match_id=None)
    await state.update_data(rewind_index=0)

    try:
        user = await get_current_user(message.from_user.id)
        match = await get_best_match(message.from_user.id)
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        await message.answer(_("An error occurred while fetching data."))
        return await state.set_state(AppStates.search)
    if not match:
        await message.answer(
            _("No one left to match with right now."),
            reply_markup=get_empty_search_keyboard(),
        )
        return await state.set_state(AppStates.search)
    media = await get_media(match.id)

    card = await get_profile_card(match, media, user)
    await message.answer_media_group(card)
    await state.update_data(match_id=match.id)
    await state.set_state(AppStates.search)
    return None


@router.message(AppStates.search, F.text == __("⏪ Rewind"))
async def rewind_with_keyboard(message: types.Message, state: FSMContext) -> None:
    """Rewind to the previous match with keyboard."""
    await message.answer(_("⏪ Rewinding"), reply_markup=get_search_keyboard())
    await rewind(message, state)


@router.message(AppStates.search, F.text == "⏪")
@router.message(AppStates.likes, F.text == "⏪")
@router.message(AppStates.matches, F.text == "⏪")
async def rewind(
    message: types.Message,
    state: FSMContext,
) -> None:
    """Rewind to the previous match."""
    if not message.from_user:
        return

    user = await get_current_user(message.from_user.id)
    rewind_index = await state.get_value("rewind_index") or 0
    try:
        rewinds = await get_rewinds(
            telegram_id=message.from_user.id,
            limit=1,
            offset=rewind_index,
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            await message.answer(
                _("You can't rewind more than {rewind_limit} times").format(
                    rewind_limit=settings.rewind_limit,
                ),
            )
        raise

    if not rewinds:
        await message.answer(_("No more matches to rewind"))
        await show_menu(message, state)
        return

    rewind = rewinds[0]
    media = await get_media(rewind.id)
    card = await get_profile_card(rewind, media, user)
    await message.answer_media_group(card)
    await state.update_data(match_id=rewind.id)
    await state.update_data(rewind_index=rewind_index + 1)


@router.message(AppStates.search, F.text.in_(["👎", "👍"]))
@router.message(AppStates.likes, F.text.in_(["👎", "👍"]))
@router.message(AppStates.matches, F.text == "👎")
async def react(message: types.Message, state: FSMContext) -> None:
    """Handle reactions to matches."""
    if not message.text or not message.from_user:
        return None

    current_state = await state.get_state()
    reactions = {
        "👍": ReactionType.like,
        "👎": ReactionType.dislike,
    }

    match_id = await state.get_value("match_id")
    if not match_id:
        return None

    try:
        await create_or_update_reaction(
            message.from_user.id,
            ReactionInSchema(
                to_user_id=match_id,
                reaction_type=reactions[message.text],
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to create or update reaction: {e}")
        if e.response.status_code == 404 or (
            e.response.status_code == 403 and "Inactive user" in e.response.text
        ):
            await message.answer(_("User not found"))
        else:
            await message.answer(_("Something went wrong"))

    if current_state == AppStates.likes.state:
        return await show_likes(message, state)
    if current_state == AppStates.matches.state:
        return await show_matches(message, state)
    return await search(message, state)


@router.callback_query(F.data == "delete_message")
async def delete_message(callback: types.CallbackQuery) -> None:
    """Delete message."""
    if callback.message and isinstance(callback.message, types.Message):
        await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "show_matches")
async def show_matches_callback(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Show matches."""
    await callback.answer()
    if not isinstance(callback.message, types.Message):
        return
    await show_matches(callback.message, state, from_user=callback.from_user)


@router.callback_query(F.data == "show_likes")
async def show_likes_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Show likes."""
    await callback.answer()
    if not isinstance(callback.message, types.Message):
        return
    await show_likes_with_keyboard(
        callback.message,
        state,
        from_user=callback.from_user,
    )
