from aiogram.fsm.state import State, StatesGroup


class AppStates(StatesGroup):
    registration = State()
    set_ui_language = State()
    set_name = State()
    set_birth_date = State()
    set_gender = State()
    set_bio = State()
    set_gender_preferences = State()
    set_age_preferences = State()
    set_location = State()
    set_media = State()

    menu = State()
    search = State()
    likes = State()
    settings = State()
    matches = State()
    report_reason = State()

    deactivate_confirm = State()
    deactivated = State()
    delete_confirm = State()
    deleted = State()

    profile = State()
    update_ui_language = State()
    update_name = State()
    update_age = State()
    update_gender = State()
    update_bio = State()
    update_location = State()
    update_media = State()

    preferences = State()
    update_gender_preferences = State()
    update_age_preferences = State()
