from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def rules_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➡️ Продолжить")]
        ],
        resize_keyboard=True
    )


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Найти игру")]
        ],
        resize_keyboard=True
    )


def search_location_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Вся Россия")],
            [KeyboardButton(text="🏙️ Выбрать город")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )


def platform_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 PlayStation 5")],
            [KeyboardButton(text="🎮 PlayStation 4")],
            [KeyboardButton(text="🎮 PlayStation 3")],
            [KeyboardButton(text="🎮 PlayStation 2")],
            [KeyboardButton(text="🎮 PlayStation 1")],
            [KeyboardButton(text="🎮 Xbox Series X/S")],
            [KeyboardButton(text="🎮 Xbox One")],
            [KeyboardButton(text="🎮 Xbox 360")],
            [KeyboardButton(text="🎮 Xbox")],
            [KeyboardButton(text="💻 PC / Windows")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )


def format_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💿 Диск")],
            [KeyboardButton(text="🔑 Ключ")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )


def condition_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔴 Плохое")],
            [KeyboardButton(text="🟠 Среднее")],
            [KeyboardButton(text="🟢 Хорошее")],
            [KeyboardButton(text="⭐ Отличное")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )


def description_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )


def photos_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➡️ Пропустить")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )


def preview_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Опубликовать")],
            [KeyboardButton(text="✏️ Изменить")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )


def exchange_actions_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="❤️"),
                KeyboardButton(text="👎"),
                KeyboardButton(text="✉️")
            ],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )


def review_actions_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="❤️"),
                KeyboardButton(text="👎")
            ],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )


def back_to_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )


def game_actions_keyboard(offer_id: int):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"🗑 Удалить #{offer_id}")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )