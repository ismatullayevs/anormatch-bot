import contextlib
import math
from math import atan2, cos, radians, sin, sqrt

import httpx
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TEST
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from aiogram.utils.media_group import MediaGroupBuilder

from app.config import EnvironmentTypes, settings
from app.enums import FileTypes
from app.schemas.media import FileSchema
from app.schemas.user import UserSchema
from app.services.place import get_place_name


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Haversine distance between two points on the Earth."""
    r = 6371

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


async def get_profile_card(
    user: UserSchema,
    media: list[FileSchema],
    from_user: UserSchema | None = None,
):
    assert user.is_active
    caption = f"{user.name}, {user.age}"

    language = from_user.ui_language.name if from_user else user.ui_language.name
    city = None
    if user.place_id:
        with contextlib.suppress(httpx.HTTPStatusError):
            city = await get_place_name(user.place_id, language)
    location_str = f"📍 {city}" if city else ""
    if from_user and from_user.is_location_precise and user.is_location_precise:
        dist = haversine_distance(
            user.latitude,
            user.longitude,
            from_user.latitude,
            from_user.longitude,
        )
        if dist <= 20 and dist != 0:
            location_str = _("📍 {dist} km").format(dist=int(math.ceil(dist)))

    caption += f", {location_str}" if location_str else ""
    caption += f"\n\n{user.bio}" if user.bio else ""

    album_builder = MediaGroupBuilder(caption=caption)
    for file in media:
        if file.file_type == FileTypes.image:
            album_builder.add_photo(file.telegram_id or file.path or "")
        elif file.file_type == FileTypes.video:
            album_builder.add_video(file.telegram_id or file.path or "")

    return album_builder.build()


async def clear_state(state: FSMContext, except_locale=False):
    data = {}
    if except_locale:
        locale = await state.get_value("locale")
        data["locale"] = locale
    await state.set_data(data)


async def send_message(*args, **kwargs):
    bot = Bot(token=settings.bot_token)
    if EnvironmentTypes.testing == settings.environment:
        session = AiohttpSession(api=TEST)
        bot = Bot(token=settings.bot_token, session=session)
    try:
        await bot.send_message(*args, **kwargs)
    finally:
        await bot.session.close()
