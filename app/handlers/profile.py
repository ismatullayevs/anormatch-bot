import asyncio

import httpx
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.enums import FileTypes
from bot.handlers.menu import show_settings
from bot.handlers.registration import GENDER_PREFERENCES, GENDERS
from bot.keyboards import (
    CLEAR_TXT,
    get_ask_location_keyboard,
    get_genders_keyboard,
    get_preferences_update_keyboard,
    get_preferred_genders_keyboard,
    get_profile_update_keyboard,
    make_keyboard,
)
from bot.schemas.preferences import PreferencesUpdateSchema
from bot.schemas.user import UserUpdateSchema
from bot.services import preferences as preferences_service
from bot.services.media import get_user_media, replace_all_media
from bot.services.place import (
    get_place_by_coordinates,
    get_place_details,
    search_places,
)
from bot.services.user import get_current_user, update_user
from bot.states import AppStates
from bot.utils import clear_state, get_profile_card
from bot.validators import (
    Params,
    validate_bio,
    validate_birth_date,
    validate_media_size,
    validate_name,
    validate_preference_age_string,
    validate_video_duration,
)

router = Router()

user_locks: dict[int, asyncio.Lock] = {}


def get_user_lock(user_id: int) -> asyncio.Lock:
    """Get user lock in order to prevent race conditions when uploading media."""
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    return user_locks[user_id]


@router.message(AppStates.settings, F.text == __("👤 My profile"))
async def show_profile(
    message: types.Message,
    state: FSMContext,
    from_user: types.User | None = None,
) -> None:
    """Show user profile."""
    from_user = from_user or message.from_user
    if not from_user:
        return

    try:
        user = await get_current_user(from_user.id)
        media = await get_user_media(from_user.id)
        profile = await get_profile_card(user, media)
        await message.answer_media_group(profile)

        await message.answer(
            _("Press the buttons below to update your profile"),
            reply_markup=get_profile_update_keyboard(),
        )
        await state.set_state(AppStates.profile)
        await clear_state(state, except_locale=True)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await message.answer(_("User profile not found. Please try again."))
        else:
            await message.answer(_("Unable to load profile. Please try again later."))


@router.message(AppStates.settings, F.text == __("🔎 Search settings"))
async def update_preferences(
    message: types.Message,
    state: FSMContext,
    *,
    with_keyboard: bool = True,
) -> None:
    """Update user preferences."""
    if with_keyboard:
        await message.answer(
            _("Search settings"),
            reply_markup=get_preferences_update_keyboard(),
        )
    await state.set_state(AppStates.preferences)
    await clear_state(state, except_locale=True)


@router.message(AppStates.profile, F.text == __("⬅️ Back"))
@router.message(AppStates.preferences, F.text == __("⬅️ Back"))
async def back_to_settings(message: types.Message, state: FSMContext) -> None:
    """Return to settings menu."""
    await show_settings(message, state)


@router.message(AppStates.profile, F.text == __("✏️ Name"))
async def update_name_start(message: types.Message, state: FSMContext) -> None:
    """Start updating user's name."""
    await message.answer(_("Enter your name"), reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AppStates.update_name)


@router.message(AppStates.update_name, F.text)
async def update_name(message: types.Message, state: FSMContext) -> None:
    """Update user's name."""
    if not message.text or not message.from_user:
        return

    try:
        name = validate_name(message.text)
    except ValueError as e:
        await message.answer(str(e))
        return

    # TODO: add error handling to all update operations
    await update_user(message.from_user.id, UserUpdateSchema(name=name))
    await message.answer(_("Your profile has been updated"))
    await show_profile(message, state)


@router.message(AppStates.profile, F.text == __("🔢 Birth date"))
async def update_birth_date_start(message: types.Message, state: FSMContext) -> None:
    """Send message to update user's birth date."""
    msg = _(
        "What's your birth date? Use one these formats:"
        "\n"
        "\n👉 <b>YYYY-MM-DD</b> (For example, 2000-12-31)"
        "\n👉 <b>DD.MM.YYYY</b> (For example, 31.12.2000)"
        "\n👉 <b>MM/DD/YYYY</b> (For example, 12/31/2000)",
    )
    await message.answer(
        msg,
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode="HTML",
    )
    await state.set_state(AppStates.update_age)


@router.message(AppStates.update_age, F.text)
async def update_birth_date(message: types.Message, state: FSMContext) -> None:
    """Send message to update user's birth date."""
    if not message.text or not message.from_user:
        return

    try:
        birth_date = validate_birth_date(message.text)
    except ValueError as e:
        await message.answer(str(e))
        return

    await update_user(message.from_user.id, UserUpdateSchema(birth_date=birth_date))
    await message.answer(_("Your profile has been updated"))
    await show_profile(message, state)


@router.message(AppStates.profile, F.text == __("👫 Gender"))
async def update_gender_start(message: types.Message, state: FSMContext) -> None:
    """Send message to update user's gender."""
    await message.answer(_("Select your gender"), reply_markup=get_genders_keyboard())
    await state.set_state(AppStates.update_gender)


@router.message(AppStates.update_gender, F.text.in_([x[0] for x in GENDERS]))
async def update_gender(message: types.Message, state: FSMContext) -> None:
    """Update user's gender."""
    if not message.text or not message.from_user:
        return

    gender = None
    for k, v in GENDERS:
        if k == message.text:
            gender = v
            break

    await update_user(message.from_user.id, UserUpdateSchema(gender=gender))

    await message.answer(_("Your profile has been updated"))
    await show_profile(message, state)


@router.message(AppStates.profile, F.text == __("📝 Bio"))
async def update_bio_start(message: types.Message, state: FSMContext) -> None:
    """Start updating user's bio."""
    await message.answer(
        _("Tell us more about yourself. What are your hobbies, interests, etc.?"),
        reply_markup=make_keyboard([[CLEAR_TXT]]),
    )
    await state.set_state(AppStates.update_bio)


@router.message(AppStates.update_bio, F.text)
async def update_bio(message: types.Message, state: FSMContext) -> None:
    """Update user's bio."""
    if not message.text or not message.from_user:
        return

    bio = message.text
    if bio == CLEAR_TXT:
        bio = None
    try:
        bio = validate_bio(bio)
    except ValueError as e:
        await message.answer(str(e))
        return

    await update_user(message.from_user.id, UserUpdateSchema(bio=bio))

    await message.answer(_("Your profile has been updated"))
    await show_profile(message, state)


@router.message(AppStates.preferences, F.text == __("👩‍❤️‍👨 Gender preferences"))
async def update_gender_preferences_start(
    message: types.Message,
    state: FSMContext,
) -> None:
    """Start updating gender preferences."""
    await message.answer(
        _("Who are you interested in?"),
        reply_markup=get_preferred_genders_keyboard(),
    )
    await state.set_state(AppStates.update_gender_preferences)


@router.message(
    AppStates.update_gender_preferences,
    F.text.in_([x[0] for x in GENDER_PREFERENCES]),
)
async def update_gender_preferences(message: types.Message, state: FSMContext) -> None:
    """Update gender preferences."""
    if not message.text or not message.from_user:
        return

    preferred_gender = None
    for k, v in GENDER_PREFERENCES:
        if k == message.text:
            preferred_gender = v
            break

    await preferences_service.update_preferences(
        message.from_user.id,
        PreferencesUpdateSchema(preferred_gender=preferred_gender),
    )
    await message.answer(
        _("Search settings have been updated"),
        reply_markup=get_preferences_update_keyboard(),
    )
    await update_preferences(message, state, with_keyboard=False)


@router.message(AppStates.preferences, F.text == __("🔢 Age preferences"))
async def update_age_preferences_start(
    message: types.Message,
    state: FSMContext,
) -> None:
    """Start updating age preferences."""
    await message.answer(
        _("What is your preferred age range? (e.g. 18-25)"),
        reply_markup=make_keyboard([[CLEAR_TXT]]),
    )
    await state.set_state(AppStates.update_age_preferences)


@router.message(AppStates.update_age_preferences, F.text)
async def update_age_preferences(message: types.Message, state: FSMContext) -> None:
    """Update age preferences."""
    if not message.text or not message.from_user:
        return
    if message.text == CLEAR_TXT:
        min_age, max_age = None, None
    else:
        try:
            min_age, max_age = validate_preference_age_string(message.text)
        except ValueError as e:
            await message.answer(str(e))
            return

    # TODO: show preferences info when updating preferences
    await preferences_service.update_preferences(
        message.from_user.id,
        PreferencesUpdateSchema(min_age=min_age, max_age=max_age),
    )

    await message.answer(
        _("Search settings have been updated"),
        reply_markup=get_preferences_update_keyboard(),
    )
    await update_preferences(message, state, with_keyboard=False)


@router.message(AppStates.profile, F.text == __("📍 Location"))
async def update_location_start(message: types.Message, state: FSMContext) -> None:
    """Start updating user's location."""
    await message.answer(
        _("Share your location or type the name of your city"),
        reply_markup=get_ask_location_keyboard(),
    )
    await state.set_state(AppStates.update_location)


@router.message(AppStates.update_location, F.text)
async def update_location_by_name(message: types.Message, state: FSMContext) -> None:
    """Update location by city name."""
    if not message.text or not message.from_user:
        return

    language = await state.get_value("locale") or "en"
    try:
        places = await search_places(message.text, language)
        if not places:
            await message.answer(_("City not found"))
            return
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await message.answer(_("No cities found for your search."))
        else:
            await message.answer(_("Error searching for cities. Please try again."))
        return

    msg = _("Select your city")
    builder = InlineKeyboardBuilder()
    for place in places:
        builder.row(
            types.InlineKeyboardButton(
                text=place.name,
                callback_data=f"place_id:{place.place_id}",
            ),
        )

    await message.answer(msg, reply_markup=builder.as_markup())


@router.callback_query(AppStates.update_location, F.data.startswith("place_id:"))
async def set_location_by_name_selected(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle place selection from inline keyboard."""
    if not callback.data or not isinstance(callback.message, types.Message):
        return

    place_id = callback.data.split(":")[1]

    try:
        language = await state.get_value("locale") or "en"
        place_details = await get_place_details(place_id, language)

        # Update user location via API
        await update_user(
            callback.from_user.id,
            UserUpdateSchema(
                latitude=place_details.latitude,
                longitude=place_details.longitude,
                place_id=place_id,
                is_location_precise=False,
            ),
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await callback.message.answer(_("Location not found. Please try again."))
        else:
            await callback.message.answer(
                _("Error updating location. Please try again."),
            )
        return

    await callback.message.answer(_("Your profile has been updated"))
    await show_profile(callback.message, state, callback.from_user)

    await callback.message.delete()


@router.message(AppStates.update_location, F.location)
async def update_location(message: types.Message, state: FSMContext) -> None:
    """Update location from coordinates."""
    if not message.location or not message.from_user:
        return

    latitude = message.location.latitude
    longitude = message.location.longitude

    try:
        language = await state.get_value("locale") or "en"
        place_details = await get_place_by_coordinates(latitude, longitude, language)
        place_id = place_details.place_id
    except httpx.HTTPStatusError:
        # If place not found, continue without place_id
        place_id = None

    # Update user location via API
    await update_user(
        message.from_user.id,
        UserUpdateSchema(
            latitude=latitude,
            longitude=longitude,
            place_id=place_id,
            is_location_precise=True,
        ),
    )

    await message.answer(_("Your profile has been updated"))
    await show_profile(message, state)


@router.message(AppStates.profile, F.text == __("📷 Media"))
async def update_media_start(message: types.Message, state: FSMContext) -> None:
    """Start media update process."""
    await message.answer(
        _(
            "Upload photos or videos of yourself ({min_media_count}-{max_media_count})",
        ).format(
            min_media_count=Params.media_min_count,
            max_media_count=Params.media_max_count,
        ),
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(AppStates.update_media)


@router.message(AppStates.update_media, F.text == __("Continue"))
async def continue_media(message: types.Message, state: FSMContext) -> None:
    """Continue with current media selection."""
    media = await state.get_value("media")
    if not media:
        await message.answer(_("Please upload at least one photo"))
        return

    await update_media_finish(message, state)


@router.message(AppStates.update_media, F.photo | F.video)
async def update_media(message: types.Message, state: FSMContext) -> None:
    """Handle media file uploads."""
    if not message.from_user:
        return None

    file = None
    if message.photo:
        p = message.photo[-1]
        file = {
            "telegram_id": p.file_id,
            "telegram_unique_id": p.file_unique_id,
            "file_type": FileTypes.image,
            "path": None,
            "duration": None,
            "file_size": p.file_size,
            "mime_type": None,
        }

    elif message.video:
        try:
            thumbnail = None
            if message.video.thumbnail:
                p = message.video.thumbnail
                thumbnail = {
                    "telegram_id": p.file_id,
                    "telegram_unique_id": p.file_unique_id,
                    "file_type": FileTypes.image,
                    "path": None,
                    "duration": None,
                    "file_size": p.file_size,
                    "mime_type": None,
                }
            file = {
                "telegram_id": message.video.file_id,
                "telegram_unique_id": message.video.file_unique_id,
                "file_type": FileTypes.video,
                "path": None,
                "duration": validate_video_duration(message.video.duration),
                "file_size": message.video.file_size,
                "mime_type": message.video.mime_type,
                "thumbnail": thumbnail,
            }
        except ValueError as e:
            await message.answer(str(e))
            return None

    if file is None:
        return None

    lock = get_user_lock(message.from_user.id)
    async with lock:
        media = (await state.get_value("media")) or []
        media.append(file)
        await state.update_data(media=media)

    try:
        validate_media_size(media)
    except ValueError as e:
        await message.answer(str(e))
        return await update_media_finish(message, state)

    if len(media) >= Params.media_max_count:
        await message.answer(_("File has been uploaded"))
        return await update_media_finish(message, state)

    msg = _(
        "File has been uploaded. Upload more media files or press Continue",
    )
    await message.answer(msg, reply_markup=make_keyboard([[_("Continue")]]))
    return None


async def update_media_finish(message: types.Message, state: FSMContext) -> None:
    """Finish media update process."""
    if not message.from_user:
        return

    data = await state.get_data()

    # Prepare media data for API
    media_data = [
        {
            "telegram_id": m["telegram_id"],
            "telegram_unique_id": m.get("telegram_unique_id"),
            "file_type": m["file_type"],
            "file_size": m["file_size"],
            "mime_type": m.get("mime_type"),
            "thumbnail": m.get("thumbnail"),
            "duration": m.get("duration"),
        }
        for m in data["media"]
    ]

    try:
        # Replace all user media via API
        await replace_all_media(message.from_user.id, media_data)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            await message.answer(_("Invalid media files. Please check your uploads."))
        elif e.response.status_code == 413:
            await message.answer(_("Media files too large. Please use smaller files."))
        else:
            await message.answer(_("Error updating media. Please try again."))
        return

    await message.answer(_("Your profile has been updated"))
    await show_profile(message, state)
