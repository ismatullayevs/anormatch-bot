from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from bot.keyboards import (
    LANGUAGES,
    get_languages_keyboard,
    get_menu_keyboard,
    get_settings_keyboard,
    make_keyboard,
)
from bot.middlewares import i18n_middleware
from bot.schemas.user import UserUpdateSchema
from bot.services.report import create_report
from bot.services.user import delete_user, update_user
from bot.states import AppStates

router = Router()


@router.message(F.text == __("⬅️ Menu"))
@router.message(Command("menu"))
async def show_menu(message: types.Message, state: FSMContext) -> None:
    """Show menu."""
    locale = await state.get_value("locale")
    await state.set_data({"locale": locale})

    await message.answer(_("Menu"), reply_markup=get_menu_keyboard())
    await state.set_state(AppStates.menu)


@router.message(AppStates.likes, F.text == __("✍️ Report"))
@router.message(AppStates.search, F.text == __("✍️ Report"))
@router.message(AppStates.matches, F.text == __("✍️ Report"))
async def report(message: types.Message, state: FSMContext) -> None:
    """Show report reason keyboard."""
    await message.answer(
        _("What's the reason for reporting this user?"),
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(AppStates.report_reason)


@router.message(AppStates.report_reason, F.text)
async def report_reason(message: types.Message, state: FSMContext) -> None:
    """Handle report reason input from user."""
    if not message.text or not message.from_user:
        return

    match_id = await state.get_value("match_id")
    if not match_id:
        return

    await create_report(message.from_user.id, match_id, message.text)
    await message.answer(_("User has been reported"))
    await show_menu(message, state)


@router.message(AppStates.menu, F.text == __("⚙️ Settings"))
async def show_settings(message: types.Message, state: FSMContext) -> None:
    """Show settings menu."""
    await message.answer(_("Settings"), reply_markup=get_settings_keyboard())
    await state.set_state(AppStates.settings)


@router.message(AppStates.settings, F.text == __("⛔️ Deactivate"))
async def deactivate_account(message: types.Message, state: FSMContext) -> None:
    """Show deactivate account confirmation dialog."""
    msg = _(
        "Are you sure you want to deactivate your account? "
        "No one will see your account, even the users that you liked",
    )
    await message.answer(msg, reply_markup=make_keyboard([[_("Yes"), _("No")]]))
    await state.set_state(AppStates.deactivate_confirm)


@router.message(AppStates.deactivate_confirm, F.text == __("No"))
async def deactivate_account_reject(message: types.Message, state: FSMContext) -> None:
    """Handle rejection of account deactivation."""
    await show_settings(message, state)


@router.message(AppStates.deactivate_confirm, F.text == __("Yes"))
async def deactivate_account_confirm(
    message: types.Message,
    state: FSMContext,
) -> None:
    """Handle confirmation of account deactivation."""
    if not message.from_user:
        return
    update_data = UserUpdateSchema(is_active=False)
    await update_user(message.from_user.id, update_data)
    await activate_account_start(message, state)


@router.message(
    AppStates.deactivated,
    F.text == __("Activate my account"),
)
async def activate_account(message: types.Message, state: FSMContext) -> None:
    """Activate user's deactivated account."""
    if not message.from_user:
        return
    update_data = UserUpdateSchema(is_active=True)
    await update_user(message.from_user.id, update_data)

    await message.answer(_("Your account has been activated"))
    await show_menu(message, state)


async def activate_account_start(message: types.Message, state: FSMContext) -> None:
    """Show account activation screen after deactivation."""
    await message.answer(
        _("Your account has been deactivated. To activate it, press the button below"),
        reply_markup=make_keyboard([[_("Activate my account")]]),
    )
    await state.set_state(AppStates.deactivated)


@router.message(AppStates.settings, F.text == __("🌐 Language"))
async def change_language_start(message: types.Message, state: FSMContext) -> None:
    """Show language selection menu."""
    await message.answer(
        _("Choose your language"),
        reply_markup=get_languages_keyboard(),
    )
    await state.set_state(AppStates.update_ui_language)


@router.message(AppStates.update_ui_language, F.text.in_(LANGUAGES.keys()))
async def change_language(
    message: types.Message,
    state: FSMContext,
) -> None:
    """Handle language change selection."""
    if not message.text or not message.from_user:
        return
    await i18n_middleware.set_locale(state, LANGUAGES[message.text].name)
    await state.update_data(locale=LANGUAGES[message.text].name)

    update_data = UserUpdateSchema(ui_language=LANGUAGES[message.text])
    await update_user(message.from_user.id, update_data)
    await show_settings(message, state)


@router.message(AppStates.settings, F.text == __("❌ Delete account"))
async def delete_account_start(message: types.Message, state: FSMContext) -> None:
    """Show delete account confirmation dialog."""
    await message.answer(
        _("Are you sure you want to delete your account? All your data will be lost"),
        reply_markup=make_keyboard([[_("Yes"), _("No")]]),
    )
    await state.set_state(AppStates.delete_confirm)


@router.message(AppStates.delete_confirm, F.text == __("No"))
async def delete_account_reject(message: types.Message, state: FSMContext) -> None:
    """Handle rejection of account deletion."""
    await show_settings(message, state)


@router.message(AppStates.delete_confirm, F.text == __("Yes"))
async def delete_account_confirm(message: types.Message, state: FSMContext) -> None:
    """Handle confirmation of account deletion."""
    if not message.from_user:
        return
    await delete_user(message.from_user.id)
    await start_registration_start(message, state)


async def start_registration_start(message: types.Message, state: FSMContext) -> None:
    """Show registration start screen after account deletion."""
    await message.answer(
        _("Your account has been deleted. To start again, press the button below"),
        reply_markup=make_keyboard([[_("Start registration")]]),
    )
    await state.set_state(AppStates.deleted)
