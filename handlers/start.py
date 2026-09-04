from html import escape

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from database.db import (
    get_user,
    create_user,
    accept_rules,
    set_city,
)

from keyboards.keyboards import (
    rules_keyboard,
    main_menu_keyboard,
)


router = Router()


class RegistrationState(StatesGroup):
    waiting_for_city = State()


RULES_TEXT = """
<b>🎮 GAME EXCHANGE</b>

Добро пожаловать в сервис обмена играми.

Здесь пользователи могут находить друг друга
и договариваться об обмене своими играми.

<b>Поддерживаются:</b>

🎮 PlayStation 3
🎮 PlayStation 4
🎮 PlayStation 5
🎮 Xbox One
🎮 Xbox Series X/S
💻 PC

<b>Форматы:</b>

💿 Физический диск
🔑 Игровой ключ

<b>Важно:</b>

• Ключ игры нельзя публиковать в объявлении.
• Для ключа указывается только регион активации.
• Запрещены мошенничество и нерабочие ключи.
• Нельзя передавать пароли и коды подтверждения.
• Нельзя спамить, оскорблять или угрожать.
• Запрещено пытаться вывести сделку за пределы сервиса.
• Нельзя приглашать третьих лиц в сделку.
• Сервис помогает найти пользователя, но не гарантирует обмен.
• Условия обмена пользователи согласовывают самостоятельно.
• За нарушения пользователь может получить ограничение или блокировку.

Нажимая <b>«✅ Продолжить»</b>, вы принимаете эти правила.
"""


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
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
            "❌ Не удалось создать профиль. Попробуйте ещё раз."
        )
        return

    if existing_user["is_blocked"]:
        await message.answer(
            "🚫 Ваш аккаунт заблокирован."
        )
        return

    if not existing_user["rules_accepted"]:
        await message.answer(
            RULES_TEXT,
            reply_markup=rules_keyboard(),
        )
        return

    if not existing_user["city"]:
        await state.set_state(
            RegistrationState.waiting_for_city
        )

        await message.answer(
            "📍 Укажите ваш город.\n\n"
            "Например: Калининград"
        )
        return

    await message.answer(
        "🎮 <b>GAME EXCHANGE</b>\n\n"
        "С возвращением! Выберите действие:",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "✅ Продолжить")
async def accept_rules_handler(
    message: Message,
    state: FSMContext,
):
    user = message.from_user

    if user is None:
        return

    accept_rules(user.id)

    await state.set_state(
        RegistrationState.waiting_for_city
    )

    await message.answer(
        "✅ Правила приняты.\n\n"
        "Теперь укажите ваш город.\n\n"
        "Например: Калининград"
    )


@router.message(RegistrationState.waiting_for_city)
async def city_handler(
    message: Message,
    state: FSMContext,
):
    user = message.from_user

    if user is None:
        return

    city = (message.text or "").strip()

    if len(city) < 2:
        await message.answer(
            "❌ Слишком короткое название города.\n"
            "Попробуйте ещё раз."
        )
        return

    if len(city) > 100:
        await message.answer(
            "❌ Слишком длинное название города.\n"
            "Попробуйте ещё раз."
        )
        return

    set_city(user.id, city)

    await state.clear()

    await message.answer(
        f"📍 Город сохранён: <b>{escape(city)}</b>\n\n"
        "🎮 Регистрация завершена!\n\n"
        "Теперь можно добавлять игры и искать обмены.",
        reply_markup=main_menu_keyboard(),
    )