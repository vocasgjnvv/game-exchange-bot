from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def rules_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✅ Продолжить")
            ]
        ],
        resize_keyboard=True
    )


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🎮 Мои игры"),
                KeyboardButton(text="🔎 Найти игру")
            ],
            [
                KeyboardButton(text="🔄 Создать обмен"),
                KeyboardButton(text="🎯 Мои совпадения")
            ],
            [
                KeyboardButton(text="❤️ Мои лайки"),
                KeyboardButton(text="🤝 Мои сделки")
            ],
            [
                KeyboardButton(text="⭐ Мой профиль"),
                KeyboardButton(text="🔔 Уведомления")
            ],
            [
                KeyboardButton(text="⚙️ Настройки")
            ]
        ],
        resize_keyboard=True
    )