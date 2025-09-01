import asyncio
import logging
import secrets

import httpx
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import settings
from app.enums import FileTypes
from app.handlers.menu import activate_account_start, show_menu
from app.keyboards import (
    GENDER_PREFERENCES,
    GENDERS,
    LANGUAGES,
    get_ask_location_keyboard,
    get_genders_keyboard,
    get_languages_keyboard,
    get_menu_keyboard,
    get_preferred_genders_keyboard,
    make_keyboard,
)
from app.middlewares import i18n_middleware
from app.schemas.media import FileSchema
from app.schemas.user import UserSchema
from app.services.place import (
    get_place_by_coordinates,
    get_place_details,
    search_places,
)
from app.services.user import get_current_user, is_user_banned
from app.states import AppStates
from app.utils import get_profile_card
from app.validators import (
    Params,
    validate_bio,
    validate_birth_date,
    validate_media_size,
    validate_name,
    validate_preference_age_string,
    validate_video_duration,
)

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    """Show help message."""
    await message.answer(
        _(
            "Hi there! I'm a bot to help you find your soulmate.\n\n"
            ""
            "Here's how it works: you'll be shown profiles of other users, "
            "and you can like or dislike them. When you like a profile, we "
            "will notify the user about it. If the user likes you back, you'll "
            "be matched and can start chatting.\n\n"
            ""
            "If you have any questions, contact our "
            "<a href='{support_link}'>support team</a>.",
        ).format(support_link="https://t.me/anormatchsupportbot"),
        parse_mode="HTML",
    )


@router.message(AppStates.deleted, F.text == __("Start registration"))
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    """Handle the /start command and route users appropriately."""
    if not message.from_user:
        return
    await state.set_state(None)
    locale = await state.get_value("locale")
    await state.set_data({"locale": locale})

    try:
        if await is_user_banned(message.from_user.id):
            await message.answer(
                _("Your account is banned. Please contact support."),
                reply_markup=types.ReplyKeyboardRemove(),
            )
            return
    except httpx.HTTPStatusError as e:
        # If user not found, continue to registration
        if e.response.status_code != 404:
            raise

    try:
        user = await get_current_user(message.from_user.id)
        await i18n_middleware.set_locale(state, user.ui_language.name)
        await state.set_data({"locale": user.ui_language.name})

        if user.is_active:
            await show_menu(message, state)
        else:
            await activate_account_start(message, state)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # User not found - start registration
            await set_language_start(message, state)
        else:
            # Other HTTP errors - re-raise
            raise


async def set_language_start(message: types.Message, state: FSMContext) -> None:
    """Start the language selection process for new users."""
    await message.answer(
        _("Hi! Select a language"),
        reply_markup=get_languages_keyboard(),
    )
    await state.set_state(AppStates.set_ui_language)


@router.message(AppStates.set_ui_language, F.text.in_(LANGUAGES.keys()))
async def set_language(message: types.Message, state: FSMContext) -> None:
    """Process the selected language and proceed to name setup."""
    if not message.text:
        return
    language = LANGUAGES[message.text]

    await i18n_middleware.set_locale(state, language.name)
    await state.update_data({"language": language})

    await set_name_start(message, state)


@router.message(AppStates.set_ui_language)
async def set_language_invalid(message: types.Message) -> None:
    """Handle invalid language selection."""
    await message.answer(
        _("Select one of the given languages"),
        reply_markup=get_languages_keyboard(),
    )


async def set_name_start(message: types.Message, state: FSMContext) -> None:
    """Start the name input process."""
    await message.answer(
        _("What is your name?"),
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(AppStates.set_name)


@router.message(AppStates.set_name, F.text)
async def set_name(message: types.Message, state: FSMContext) -> None:
    """Process the user's name input and validate it."""
    if not message.text:
        return

    try:
        validate_name(message.text)
    except ValueError as e:
        await message.answer(str(e))
        return

    await state.update_data(name=message.text)
    await set_birth_date_start(message, state)


async def set_birth_date_start(message: types.Message, state: FSMContext) -> None:
    """Start the birth date input process."""
    msg = _(
        "What's your birth date? Use one these formats:"
        "\n"
        "\n👉 <b>YYYY-MM-DD</b> (For example, 2000-12-31)"
        "\n👉 <b>DD.MM.YYYY</b> (For example, 31.12.2000)"
        "\n👉 <b>MM/DD/YYYY</b> (For example, 12/31/2000)",
    )
    await message.answer(msg, parse_mode="HTML")
    await state.set_state(AppStates.set_birth_date)


@router.message(AppStates.set_birth_date, F.text)
async def set_birth_date(message: types.Message, state: FSMContext) -> None:
    """Process the user's birth date input and validate it."""
    if not message.text:
        return

    try:
        validate_birth_date(message.text)
    except ValueError as e:
        await message.answer(str(e))
        return

    await state.update_data(birth_date=message.text)
    await set_gender_start(message, state)


async def set_gender_start(message: types.Message, state: FSMContext) -> None:
    """Start the gender selection process."""
    await message.answer(_("What is your gender?"), reply_markup=get_genders_keyboard())
    await state.set_state(AppStates.set_gender)


@router.message(AppStates.set_gender, F.text.in_([x[0] for x in GENDERS]))
async def set_gender(message: types.Message, state: FSMContext) -> None:
    """Process the selected gender and proceed to bio setup."""
    if not message.text or not message.from_user:
        return

    gender = None
    for k, v in GENDERS:
        if k == message.text:
            gender = v
            break

    await state.update_data(gender=gender)
    await set_bio_start(message, state)


@router.message(AppStates.set_gender)
async def set_gender_invalid(message: types.Message) -> None:
    """Handle invalid gender selection."""
    await message.answer(_("Select one of the given options"))


async def set_bio_start(message: types.Message, state: FSMContext) -> None:
    """Start the bio input process."""
    msg = _("Tell me more about yourself. What are your hobbies, interests, etc.?")
    await message.answer(msg, reply_markup=make_keyboard([[_("Skip")]]))
    await state.set_state(AppStates.set_bio)


@router.message(AppStates.set_bio, F.text == __("Skip"))
async def skip_bio(message: types.Message, state: FSMContext) -> None:
    """Skip bio input and proceed to preferred gender setup."""
    await state.update_data(bio=None)
    await set_preferred_gender_start(message, state)


@router.message(AppStates.set_bio, F.text)
async def set_bio(message: types.Message, state: FSMContext) -> None:
    """Process the user's bio input and validate it."""
    try:
        validate_bio(message.text)
    except ValueError as e:
        await message.answer(str(e))
        return

    await state.update_data(bio=message.text)
    await set_preferred_gender_start(message, state)


async def set_preferred_gender_start(message: types.Message, state: FSMContext) -> None:
    """Start the preferred gender selection process."""
    await message.answer(
        _("Who are you interested in?"),
        reply_markup=get_preferred_genders_keyboard(),
    )
    await state.set_state(AppStates.set_gender_preferences)


@router.message(
    AppStates.set_gender_preferences,
    F.text.in_([x[0] for x in GENDER_PREFERENCES]),
)
async def set_preferred_gender(message: types.Message, state: FSMContext) -> None:
    """Process the selected preferred gender and proceed to age preferences."""
    preferred_gender = None
    for k, v in GENDER_PREFERENCES:
        if k == message.text:
            preferred_gender = v
            break

    if preferred_gender is None:
        return
    await state.update_data(preferred_gender=preferred_gender)
    await set_age_preferences_start(message, state)


@router.message(AppStates.set_gender_preferences, F.text)
async def set_gender_preferences_invalid(message: types.Message) -> None:
    """Handle invalid gender preference selection."""
    await message.answer(
        _("Select one of the given options"),
        reply_markup=get_preferred_genders_keyboard(),
    )


async def set_age_preferences_start(message: types.Message, state: FSMContext) -> None:
    """Start the age preferences input process."""
    await message.answer(
        _("What is your preferred age range? (e.g. 18-25)"),
        reply_markup=make_keyboard([[_("Skip")]]),
    )
    await state.set_state(AppStates.set_age_preferences)


@router.message(AppStates.set_age_preferences, F.text == __("Skip"))
async def skip_age_preferences(message: types.Message, state: FSMContext) -> None:
    """Skip age preferences and proceed to location setup."""
    await state.update_data(preferred_min_age=None)
    await state.update_data(preferred_max_age=None)
    await set_location_start(message, state)


@router.message(AppStates.set_age_preferences, F.text)
async def set_age_preferences(message: types.Message, state: FSMContext) -> None:
    """Process the user's age preferences input and validate it."""
    if not message.text or not message.from_user:
        return

    try:
        min_age, max_age = validate_preference_age_string(message.text)
    except ValueError as e:
        await message.answer(str(e))
        return

    await state.update_data(preferred_min_age=min_age)
    await state.update_data(preferred_max_age=max_age)
    await set_location_start(message, state)


async def set_location_start(message: types.Message, state: FSMContext) -> None:
    """Start the location input process."""
    await message.answer(
        _("Share your location or type the name of your city"),
        reply_markup=get_ask_location_keyboard(),
    )
    await state.set_state(AppStates.set_location)


@router.message(AppStates.set_location, F.text)
async def set_location_by_name(message: types.Message, state: FSMContext) -> None:
    """Process location input by name and show matching places."""
    if not message.text or not message.from_user:
        return

    language = await state.get_value("language")
    if not language:
        return

    try:
        places = await search_places(message.text, language)
        if not places:
            await message.answer(_("City not found"))
            return
    except httpx.HTTPError:
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


@router.callback_query(AppStates.set_location, F.data.startswith("place_id:"))
async def set_location_by_name_selected(
    query: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle place selection from inline keyboard."""
    if not query.data or not isinstance(query.message, types.Message):
        return
    place_id = query.data.split(":")[1]

    try:
        language = await state.get_value("language")
        if not language:
            language = "en"
        place_details = await get_place_details(place_id, language)

        await state.update_data(place_id=place_id)
        await state.update_data(latitude=place_details.latitude)
        await state.update_data(longitude=place_details.longitude)
        await state.update_data(is_location_precise=False)
    except httpx.HTTPError:
        await query.message.answer(
            _("Error getting place information. Please try again."),
        )
        return

    await query.message.delete()
    await set_media_start(query.message, state)


@router.message(AppStates.set_location, F.location)
async def set_location(message: types.Message, state: FSMContext) -> None:
    """Process location input from coordinates."""
    if not message.location or not message.from_user:
        return

    lat, lng = message.location.latitude, message.location.longitude
    await state.update_data(latitude=lat)
    await state.update_data(longitude=lng)
    await state.update_data(is_location_precise=True)

    try:
        language = await state.get_value("language")
        if not language:
            language = "en"
        place_details = await get_place_by_coordinates(lat, lng, language)
        await state.update_data(place_id=place_details.place_id)
    except httpx.HTTPError:
        # If place not found, continue without place_id
        pass

    await set_media_start(message, state)


@router.message(AppStates.set_location)
async def set_location_invalid(message: types.Message) -> None:
    """Handle invalid location input."""
    await message.answer(
        _("Share your location by clicking the button below"),
        reply_markup=get_ask_location_keyboard(),
    )


async def set_media_start(message: types.Message, state: FSMContext) -> None:
    """Start the media upload process."""
    await message.answer(
        _(
            "Upload photos or videos of yourself ({min_media_count}-{max_media_count})",
        ).format(
            min_media_count=Params.media_min_count,
            max_media_count=Params.media_max_count,
        ),
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(AppStates.set_media)


@router.message(AppStates.set_media, F.text == __("Continue"))
async def continue_registration(message: types.Message, state: FSMContext) -> None:
    """Continue with registration after media upload."""
    media = await state.get_value("media")
    try:
        validate_media_size(media or [])
    except ValueError as e:
        await message.answer(str(e))
        return
    await finish_registration(message, state)


user_locks: dict[int, asyncio.Lock] = {}


def get_user_lock(user_id: int) -> asyncio.Lock:
    """Get or create an asyncio lock for a specific user ID."""
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    return user_locks[user_id]


@router.message(AppStates.set_media, F.photo | F.video)
async def set_media(message: types.Message, state: FSMContext) -> None:
    """Process uploaded media and add it to the user's profile."""
    if not message.from_user:
        return
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
            return

    if file is None:
        return

    lock = get_user_lock(message.from_user.id)
    async with lock:
        media = (await state.get_value("media")) or []
        media.append(file)
        await state.update_data(media=media)

    try:
        validate_media_size(media)
    except ValueError as e:
        await message.answer(str(e))
        await finish_registration(message, state)
        return

    if len(media) >= Params.media_max_count:
        await message.answer(_("File has been uploaded"))
        await finish_registration(message, state)
        return

    msg = _(
        "File has been uploaded. Upload more media files "
        'if you want or press "Continue"',
    )
    await message.answer(msg, reply_markup=make_keyboard([[_("Continue")]]))


async def finish_registration(message: types.Message, state: FSMContext) -> None:
    """Complete the registration process and create the user account."""
    if not message.from_user:
        return
    data = await state.get_data()
    telegram_id = message.from_user.id
    if data.get("testing"):
        telegram_id = secrets.randbelow(8999999999) + 1000000000

    media = [
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
    # TODO: allow user to exist without preferences and media

    preferences_data = {
        "min_age": data["preferred_min_age"],
        "max_age": data["preferred_max_age"],
        "preferred_gender": data["preferred_gender"],
    }

    birth_date = validate_birth_date(data["birth_date"])
    if not birth_date:
        await message.answer(_("Invalid birth date"))
        return
    user_data = {
        "telegram_id": telegram_id,
        "name": data["name"],
        "birth_date": birth_date.isoformat(),
        "bio": data.get("bio"),
        "gender": data["gender"],
        "ui_language": data["language"],
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "is_location_precise": data["is_location_precise"],
        "place_id": data.get("place_id"),
    }

    # Place handling is now done by the API during registration

    headers = {
        "X-Internal-Token": settings.internal_token,
        "X-Telegram-User-Id": str(telegram_id),
    }
    async with httpx.AsyncClient() as session:
        try:
            response = await session.post(
                f"{settings.api_url}/v1/auth/register",
                json=user_data,
                headers=headers,
            )
            response.raise_for_status()
            user = UserSchema.model_validate(response.json())
            response = await session.post(
                f"{settings.api_url}/v1/media/batch-add",
                json=media,
                headers=headers,
            )
            response.raise_for_status()
            media = [FileSchema.model_validate(m) for m in response.json()]
            response = await session.post(
                f"{settings.api_url}/v1/preferences",
                json=preferences_data,
                headers=headers,
                params={"user_id": str(user.id)},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"Error registering user: {e}")
            await message.answer(
                _(
                    "An error occurred while registering your account. "
                    "Please try again later or contact support.",
                ),
            )
            raise

    await message.answer(
        _("Registration has been completed!"),
        reply_markup=get_menu_keyboard(),
    )

    profile = await get_profile_card(user, media)
    await message.answer_media_group(profile)
    await show_menu(message, state)
