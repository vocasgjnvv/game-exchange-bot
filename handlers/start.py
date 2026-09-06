from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.db import (
    get_user,
    create_user,
    accept_rules,
)

from keyboards.keyboards import (
    rules_keyboard,
    main_menu_keyboard,
)

router = Router()


# ============================================================
# RULES
# ============================================================

RULES_TEXT = """
<b>🎮 GAME EXCHANGE</b>

Сервис помогает находить пользователей для обмена играми.

Ты создаёшь объявление со своей игрой,
просматриваешь объявления других пользователей
и можешь поставить ❤️ или 👎.

Если вы оба поставите ❤️ —
контакт Telegram будет сразу открыт обоим пользователям.

<b>Важно:</b>

• Сервис только помогает найти друг друга.
• Сервис не является стороной сделки.
• Сервис не гарантирует получение товара.
• Сервис не гарантирует подлинность игры или ключа.
• Сервис не гарантирует соответствие товара описанию.
• Сервис не гарантирует выполнение договорённостей.
• Условия обмена пользователи согласовывают самостоятельно.
• Соблюдай правила платформ и будь внимателен при обмене.

Нажимая <b>«➡️ Продолжить»</b>, ты принимаешь правила.
"""


# ============================================================
# /start
# ============================================================

@router.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext,
):
    user = message.from_user

    if user is None:
        return

    await state.clear()

    existing_user = get_user(user.id)

    if not existing_user:
        create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name or "Пользователь",
        )

        existing_user = get_user(user.id)

    if not existing_user:
        await message.answer(
            "❌ Не удалось создать профиль.\n\n"
            "Попробуй выполнить /start ещё раз."
        )
        return

    if existing_user["is_blocked"]:
        await message.answer(
            "🚫 <b>Ваш аккаунт заблокирован.</b>\n\n"
            "Использование сервиса недоступно."
        )
        return

    if not existing_user["rules_accepted"]:
        await message.answer(
            RULES_TEXT,
            reply_markup=rules_keyboard(),
        )
        return

    await message.answer(
        "🎮 <b>GAME EXCHANGE</b>\n\n"
        "Добро пожаловать обратно!",
        reply_markup=main_menu_keyboard(),
    )


# ============================================================
# ACCEPT RULES
# ============================================================

@router.message(F.text == "➡️ Продолжить")
async def accept_rules_handler(
    message: Message,
    state: FSMContext,
):
    user = message.from_user

    if user is None:
        return

    existing_user = get_user(user.id)

    if not existing_user:
        create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name or "Пользователь",
        )

        existing_user = get_user(user.id)

    if not existing_user:
        await message.answer(
            "❌ Не удалось создать профиль.\n\n"
            "Попробуй выполнить /start ещё раз."
        )
        return

    if existing_user["is_blocked"]:
        await message.answer(
            "🚫 <b>Ваш аккаунт заблокирован.</b>"
        )
        return

    accept_rules(user.id)

    await state.clear()

    await message.answer(
        "✅ <b>Правила приняты!</b>\n\n"
        "Теперь можешь создать объявление и "
        "искать игры для обмена.",
        reply_markup=main_menu_keyboard(),
    )


# ============================================================
# MAIN MENU
# ============================================================

@router.message(F.text == "🏠 Главное меню")
async def main_menu_handler(
    message: Message,
    state: FSMContext,
):
    user = message.from_user

    if user is None:
        return

    await state.clear()

    existing_user = get_user(user.id)

    if not existing_user:
        await message.answer(
            "❌ Профиль не найден.\n\n"
            "Выполни /start."
        )
        return

    if existing_user["is_blocked"]:
        await message.answer(
            "🚫 <b>Ваш аккаунт заблокирован.</b>\n\n"
            "Доступ к сервису ограничен."
        )
        return

    if not existing_user["rules_accepted"]:
        await message.answer(
            RULES_TEXT,
            reply_markup=rules_keyboard(),
        )
        return

    await message.answer(
        "🎮 <b>Главное меню</b>\n\n"
        "Выбери действие:",
        reply_markup=main_menu_keyboard(),
    )