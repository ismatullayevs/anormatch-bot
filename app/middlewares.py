from aiogram.utils.i18n import FSMI18nMiddleware, I18n

from app.config import settings

# Bot-specific i18n configuration

i18n = I18n(
    path=settings.base_dir / "locales",
    default_locale="en",
    domain="messages",
)
i18n_middleware = FSMI18nMiddleware(i18n)
