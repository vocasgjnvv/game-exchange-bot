from aiogram import Router, F
from aiogram.types import Message

from database.db import get_user
from keyboards.keyboards import main_menu_keyboard


router = Router()


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
        "Здесь будут отображаться ваши игры.\n\n"
        "Следующим шагом добавим возможность создать "
        "объявление об обмене.",
        reply_markup=main_menu_keyboard(),
    )