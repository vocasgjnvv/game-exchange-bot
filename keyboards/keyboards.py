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
                KeyboardButton(text="➕ Добавить игру"),
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


def platform_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🎮 PS3"),
                KeyboardButton(text="🎮 PS4")
            ],
            [
                KeyboardButton(text="🎮 PS5"),
                KeyboardButton(text="🟩 Xbox One")
            ],
            [
                KeyboardButton(text="🟩 Xbox Series X/S"),
                KeyboardButton(text="💻 PC")
            ]
        ],
        resize_keyboard=True
    )


def format_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💿 Физический диск")
            ],
            [
                KeyboardButton(text="🔑 Игровой ключ")
            ]
        ],
        resize_keyboard=True
    )
    
def condition_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🟢 Отличное")
            ],
            [
                KeyboardButton(text="🟡 Хорошее")
            ],
            [
                KeyboardButton(text="🟠 Есть следы использования")
            ]
        ],
        resize_keyboard=True
    )