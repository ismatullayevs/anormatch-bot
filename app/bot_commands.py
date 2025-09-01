from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats


async def set_bot_profile(bot: Bot):
    await bot.set_my_name("Anor - match and meet new friends ✨")
    await bot.set_my_name("Anor - знакомства и новые друзья ✨", language_code="ru")
    await bot.set_my_name(
        "Anor - tanishing va do'stlar orttiring ✨", language_code="uz",
    )
    await bot.set_my_commands(
        [
            BotCommand(
                command="/menu",
                description="Menu",
            ),
            BotCommand(
                command="/help",
                description="Help",
            ),
        ],
        scope=BotCommandScopeAllPrivateChats(),
        language_code="en",
    )

    await bot.set_my_commands(
        [
            BotCommand(
                command="/menu",
                description="Menyu",
            ),
            BotCommand(
                command="/help",
                description="Yordam",
            ),
        ],
        scope=BotCommandScopeAllPrivateChats(),
        language_code="uz",
    )

    await bot.set_my_commands(
        [
            BotCommand(
                command="/menu",
                description="Меню",
            ),
            BotCommand(
                command="/help",
                description="Помощь",
            ),
        ],
        scope=BotCommandScopeAllPrivateChats(),
        language_code="ru",
    )

    await bot.set_my_description(
        "Hi there! I'm a bot to help you find your soulmate.\n\n"
        ""
        "Here's how it works: you'll be shown profiles of other users, and you can like or dislike them. "
        "When you like a profile, we will notify the user about it. If the user likes you back, you'll be matched "
        "and can start chatting.\n\n"
        ""
        "To get started, click /start and fill out your profile.",
    )

    await bot.set_my_description(
        "Привет! Я бот, который поможет вам найти свою вторую половинку.\n"
        "\n"
        "Вот как это работает: вам будут показаны профили других пользователей, и "
        "вы сможете залайкать или дизлайкнуть их. Когда вы лайкнете профиль, мы "
        "уведомим пользователя об этом. Если пользователь вас тоже лайкнет, вы "
        "будете совпадать и сможете начать общение.\n"
        "\n"
        "Для начала, нажмите /start и заполните свой профиль.",
        language_code="ru",
    )

    await bot.set_my_description(
        "Salom! Men sizga juftingizni topishga yordam beraman.\n"
        "\n"
        "Bot qanday ishlaydi: biz sizga boshqa foydalanuvchilar profilini "
        "ko'rsatamiz. Siz ularga layk yoki dislayk bosishingiz mumkin. Siz "
        "kimningdir profiliga layk bossangiz, biz foydalanuvchini bu haqida "
        "ogohlantiramiz. Agar foydalanuvchi ham sizga layk bossa, siz ular bilan "
        "suhbatlashishingiz mumkin bo'ladi.\n"
        "\n"
        "Boshlash uchun /start tugmasini bosing va profilingizni to'ldiring.",
        language_code="uz",
    )
