from html import escape

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database.db import (
    get_connection,
    get_user,
    get_next_search_offers,
    get_listing_photos,
    save_like,
    create_notification,
)

from keyboards.keyboards import (
    exchange_actions_keyboard,
    main_menu_keyboard,
)

router = Router()


class ExchangeStates(StatesGroup):
    browsing = State()
    waiting_for_message = State()


def get_offer(offer_id: int):
    with get_connection() as db:
        return db.execute(
            """
            SELECT
                offers.id,
                offers.user_id,
                games.title,
                offers.platform,
                offers.format,
                offers.condition,
                offers.key_region,
                offers.description,
                offers.city,
                offers.search_location,
                users.telegram_id,
                users.username,
                users.first_name
            FROM offers
            JOIN games ON games.id = offers.game_id
            JOIN users ON users.id = offers.user_id
            WHERE offers.id = ?
              AND offers.status = 'active'
            """,
            (offer_id,),
        ).fetchone()


def get_user_contact(user_id: int):
    with get_connection() as db:
        return db.execute(
            """
            SELECT
                id,
                telegram_id,
                username,
                first_name
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()


def get_active_user_offer(user_id: int):
    with get_connection() as db:
        return db.execute(
            """
            SELECT
                offers.id,
                offers.user_id,
                games.title,
                offers.platform,
                offers.format,
                offers.condition,
                offers.key_region,
                offers.description,
                offers.city,
                offers.search_location
            FROM offers
            JOIN games ON games.id = offers.game_id
            WHERE offers.user_id = ?
              AND offers.status = 'active'
            ORDER BY offers.created_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()


def contact_text(user_id: int) -> str:
    user = get_user_contact(user_id)

    if not user:
        return "📱 Telegram: контакт недоступен"

    if user["username"]:
        return f"📱 Telegram: @{escape(user['username'])}"

    first_name = escape(
        user["first_name"] or "Пользователь"
    )

    return (
        f'📱 Telegram: '
        f'<a href="tg://user?id={user["telegram_id"]}">'
        f'{first_name}</a>'
    )


def build_offer_text(offer) -> str:
    text = (
        f"🎮 <b>{escape(str(offer['title']))}</b>\n\n"
        f"🕹 Платформа: "
        f"<b>{escape(str(offer['platform']))}</b>\n"
        f"💿 Формат: "
        f"<b>{escape(str(offer['format']))}</b>\n"
    )

    if offer["condition"]:
        text += (
            f"📦 Состояние: "
            f"<b>{escape(str(offer['condition']))}</b>\n"
        )

    if offer["key_region"]:
        text += (
            f"🌍 Регион: "
            f"<b>{escape(str(offer['key_region']))}</b>\n"
        )

    if offer["city"]:
        text += (
            f"📍 Город: "
            f"<b>{escape(str(offer['city']))}</b>\n"
        )

    if offer["description"]:
        text += (
            "\n📝 <b>Описание:</b>\n"
            f"{escape(str(offer['description']))}\n"
        )

    return text


async def send_offer_photos(
    bot: Bot,
    chat_id: int,
    offer_id: int,
):
    photos = get_listing_photos(offer_id)

    for photo in photos:
        try:
            await bot.send_photo(
                chat_id,
                photo["file_id"],
            )
        except Exception:
            continue


async def show_offer(
    message: Message,
    state: FSMContext,
    offer,
):
    await state.update_data(
        current_offer_id=offer["id"]
    )

    await send_offer_photos(
        bot=message.bot,
        chat_id=message.chat.id,
        offer_id=offer["id"],
    )

    await message.answer(
        build_offer_text(offer),
        reply_markup=exchange_actions_keyboard(),
    )