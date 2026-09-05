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
    back_to_main_keyboard,
)


router = Router()


class RegistrationState(StatesGroup):
    waiting_for_city = State()


RULES_TEXT = """
<b>🎮 GAME EXCHANGE</b>

Добро пожаловать в сервис обмена играми.

Здесь пользователи могут находить друг друга
и самостоятельно договариваться об обмене своими играми.

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
• Нельзя пытаться обмануть другого пользователя.
• Сервис не является стороной сделки.
• Сервис не гарантирует получение товара.
• Сервис не гарантирует подлинность ключа.
• Сервис не гарантирует соответствие товара описанию.
• Условия обмена пользователи согласовывают самостоятельно.
• За нарушения пользователь может получить ограничение или блокировку.

Нажимая <b>«✅ Продолжить»</b>, вы принимаете правила.
"""


# =========================================================
# /start
# =========================================================

@router.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext,
):
    user = message.from_user

    if user is None:
        return

    # При /start всегда убираем старое состояние
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
            "Попробуйте выполнить /start ещё раз."
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

    if not existing_user["city"]:
        await state.set_state(
            RegistrationState.waiting_for_city
        )

        await message.answer(
            "📍 <b>Укажите ваш город.</b>\n\n"
            "Например: Калининград",
            reply_markup=back_to_main_keyboard(),
        )
        return

    await message.answer(
        "🎮 <b>GAME EXCHANGE</b>\n\n"
        "С возвращением!\n\n"
        "Выберите действие:",
        reply_markup=main_menu_keyboard(),
    )


# =========================================================
# Принятие правил
# =========================================================

@router.message(F.text == "✅ Продолжить")
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
            "Попробуйте выполнить /start."
        )
        return

    if existing_user["is_blocked"]:
        await message.answer(
            "🚫 <b>Ваш аккаунт заблокирован.</b>"
        )
        return

    accept_rules(user.id)

    await state.set_state(
        RegistrationState.waiting_for_city
    )

    await message.answer(
        "✅ <b>Правила приняты.</b>\n\n"
        "Теперь укажите ваш город.\n\n"
        "Например: Калининград",
        reply_markup=back_to_main_keyboard(),
    )


# =========================================================
# Главное меню
# ВАЖНО: этот обработчик находится выше FSM-обработчика города
# =========================================================

@router.message(F.text == "🏠 Главное меню")
async def main_menu_handler(
    message: Message,
    state: FSMContext,
):
    user = message.from_user

    if user is None:
        return

    # Самое главное — полностью сбрасываем текущее действие
    await state.clear()

    existing_user = get_user(user.id)

    if not existing_user:
        await message.answer(
            "❌ Профиль не найден.\n\n"
            "Выполните /start."
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

    if not existing_user["city"]:
        await state.set_state(
            RegistrationState.waiting_for_city
        )

        await message.answer(
            "📍 Сначала укажите ваш город.",
            reply_markup=back_to_main_keyboard(),
        )
        return

    await message.answer(
        "🎮 <b>Главное меню</b>\n\n"
        "Выберите нужное действие:",
        reply_markup=main_menu_keyboard(),
    )


# =========================================================
# Регистрация города
# =========================================================

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
            "❌ Слишком короткое название города.\n\n"
            "Попробуйте ещё раз.",
            reply_markup=back_to_main_keyboard(),
        )
        return

    if len(city) > 100:
        await message.answer(
            "❌ Название города слишком длинное.\n\n"
            "Попробуйте ещё раз.",
            reply_markup=back_to_main_keyboard(),
        )
        return

    set_city(user.id, city)

    await state.clear()

    await message.answer(
        f"📍 Город сохранён: <b>{escape(city)}</b>\n\n"
        "🎮 <b>Регистрация завершена!</b>\n\n"
        "Теперь можно добавлять игры и искать обмены.",
        reply_markup=main_menu_keyboard(),
    )


# =========================================================
# ⭐ МОЙ ПРОФИЛЬ
# =========================================================

@router.message(F.text == "⭐ Мой профиль")
async def profile_handler(message: Message):
    user = message.from_user

    if user is None:
        return

    profile = get_user(user.id)

    if not profile:
        await message.answer(
            "❌ Профиль не найден.\n\n"
            "Выполните /start."
        )
        return

    if profile["is_blocked"]:
        await message.answer(
            "🚫 <b>Ваш аккаунт заблокирован.</b>"
        )
        return

    first_name = escape(
        profile["first_name"] or "Пользователь"
    )

    city = escape(
        profile["city"] or "Не указан"
    )

    if profile["username"]:
        username = "@" + escape(profile["username"])
    else:
        username = "Не указан"

    rating = profile["rating"] or 5.0
    reviews_count = profile["reviews_count"] or 0
    completed_deals = profile["completed_deals"] or 0

    await message.answer(
        "⭐ <b>МОЙ ПРОФИЛЬ</b>\n\n"
        f"👤 Имя: <b>{first_name}</b>\n"
        f"🔗 Username: <b>{username}</b>\n"
        f"📍 Город: <b>{city}</b>\n\n"
        f"⭐ Рейтинг: <b>{rating:.1f}/5.0</b>\n"
        f"💬 Отзывов: <b>{reviews_count}</b>\n"
        f"🤝 Завершённых обменов: <b>{completed_deals}</b>\n\n"
        "💡 Хорошая репутация помогает другим "
        "пользователям доверять вам при обмене.",
        reply_markup=back_to_main_keyboard(),
    )


# =========================================================
# 🔔 УВЕДОМЛЕНИЯ
# =========================================================

@router.message(F.text == "🔔 Уведомления")
async def notifications_handler(message: Message):
    user = message.from_user

    if user is None:
        return

    profile = get_user(user.id)

    if not profile:
        await message.answer(
            "❌ Профиль не найден.\n\n"
            "Выполните /start."
        )
        return

    if profile["is_blocked"]:
        await message.answer(
            "🚫 <b>Ваш аккаунт заблокирован.</b>"
        )
        return

    # Пока таблица уведомлений уже существует в БД,
    # полноценный вывод подключим следующим большим блоком.
    await message.answer(
        "🔔 <b>Уведомления</b>\n\n"
        "Пока новых уведомлений нет.\n\n"
        "Здесь в будущем будут появляться:\n"
        "❤️ новые лайки\n"
        "🎯 новые совпадения\n"
        "💌 предложения обмена\n"
        "🤝 изменения сделок\n"
        "⭐ отзывы",
        reply_markup=back_to_main_keyboard(),
    )


# =========================================================
# ⚙️ НАСТРОЙКИ
# =========================================================

@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: Message):
    user = message.from_user

    if user is None:
        return

    profile = get_user(user.id)

    if not profile:
        await message.answer(
            "❌ Профиль не найден.\n\n"
            "Выполните /start."
        )
        return

    if profile["is_blocked"]:
        await message.answer(
            "🚫 <b>Ваш аккаунт заблокирован.</b>"
        )
        return

    await message.answer(
        "⚙️ <b>НАСТРОЙКИ</b>\n\n"
        "🔔 Уведомления — скоро\n"
        "📍 Изменение города — скоро\n"
        "👤 Профиль — скоро\n"
        "🚫 Чёрный список — скоро\n\n"
        "Основные настройки подключим следующим "
        "большим блоком.",
        reply_markup=back_to_main_keyboard(),
    )