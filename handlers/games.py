from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from database.db import get_user
from keyboards.keyboards import (
    main_menu_keyboard,
    platform_keyboard,
    format_keyboard,
)


router = Router()


class AddGameState(StatesGroup):
    waiting_for_title = State()
    waiting_for_platform = State()
    waiting_for_format = State()


@router.message(F.text == "➕ Добавить игру")
async def add_game_start(message: Message, state: FSMContext):
    user = message.from_user

    if user is None:
        return

    db_user = get_user(user.id)

    if not db_user:
        await message.answer(
            "❌ Профиль не найден.\n\n"
            "Нажмите /start."
        )
        return

    await state.set_state(AddGameState.waiting_for_title)

    await message.answer(
        "➕ <b>Добавление игры</b>\n\n"
        "Напишите название игры.\n"
        "Например: <b>Red Dead Redemption 2</b>"
    )


@router.message(AddGameState.waiting_for_title)
async def add_game_title(message: Message, state: FSMContext):
    title = (message.text or "").strip()

    if not title:
        await message.answer("❌ Напишите название игры текстом.")
        return

    if len(title) < 2:
        await message.answer("❌ Название слишком короткое.")
        return

    if len(title) > 100:
        await message.answer(
            "❌ Название слишком длинное. Максимум 100 символов."
        )
        return

    await state.update_data(title=title)

    await state.set_state(AddGameState.waiting_for_platform)

    await message.answer(
        f"🎮 Игра: <b>{title}</b>\n\n"
        "Выберите платформу:",
        reply_markup=platform_keyboard(),
    )


@router.message(AddGameState.waiting_for_platform)
async def add_game_platform(message: Message, state: FSMContext):
    platform = (message.text or "").strip()

    allowed_platforms = {
        "🎮 PS3",
        "🎮 PS4",
        "🎮 PS5",
        "🟩 Xbox One",
        "🟩 Xbox Series X/S",
        "💻 PC",
    }

    if platform not in allowed_platforms:
        await message.answer(
            "❌ Выберите платформу кнопкой ниже.",
            reply_markup=platform_keyboard(),
        )
        return

    data = await state.get_data()
    title = data.get("title")

    await state.update_data(platform=platform)

    await state.set_state(AddGameState.waiting_for_format)

    await message.answer(
        f"🎮 Игра: <b>{title}</b>\n"
        f"🕹 Платформа: <b>{platform}</b>\n\n"
        "Выберите формат игры:",
        reply_markup=format_keyboard(),
    )


@router.message(AddGameState.waiting_for_format)
async def add_game_format(message: Message, state: FSMContext):
    format_type = (message.text or "").strip()

    allowed_formats = {
        "💿 Физический диск",
        "🔑 Игровой ключ",
    }

    if format_type not in allowed_formats:
        await message.answer(
            "❌ Выберите формат кнопкой ниже.",
            reply_markup=format_keyboard(),
        )
        return

    data = await state.get_data()
    title = data.get("title")
    platform = data.get("platform")

    await state.update_data(format=format_type)

    await message.answer(
        f"🎮 Игра: <b>{title}</b>\n"
        f"🕹 Платформа: <b>{platform}</b>\n"
        f"📦 Формат: <b>{format_type}</b>\n\n"
        "Следующим шагом добавим данные для объявления."
    )


@router.message(F.text == "🎮 Мои игры")
async def my_games_handler(message: Message):
    user = message.from_user

    if user is None:
        return

    db_user = get_user(user.id)

    if not db_user:
        await message.answer(
            "❌ Профиль не найден.\n\n"
            "Нажмите /start."
        )
        return

    await message.answer(
        "🎮 <b>Мои игры</b>\n\n"
        "Здесь будут отображаться ваши игры.",
        reply_markup=main_menu_keyboard(),
    )