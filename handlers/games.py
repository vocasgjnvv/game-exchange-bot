from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from database.db import get_user
from keyboards.keyboards import main_menu_keyboard, platform_keyboard


router = Router()


class AddGameState(StatesGroup):
    waiting_for_title = State()
    waiting_for_platform = State()


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
        await message.answer("❌ Название слишком длинное. Максимум 100 символов.")
        return

     await state.update_data(title=title)

     await state.set_state(AddGameState.waiting_for_platform)

     await message.answer(
         f"🎮 Игра: <b>{title}</b>\n\n"
         "Выберите платформу:",
         reply_markup=platform_keyboard(),
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