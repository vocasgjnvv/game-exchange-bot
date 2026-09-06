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
async def show_next_offer(
    message: Message,
    state: FSMContext,
    user_id: int,
):
    data = await state.get_data()

    platform = data.get("platform")
    city = data.get("city")

    if not platform:
        await state.clear()
        await message.answer(
            "❌ Не удалось определить платформу.",
            reply_markup=main_menu_keyboard(),
        )
        return

    offer = get_next_search_offers(
        user_id=user_id,
        platform=platform,
        city=city,
    )

    if not offer:
        await state.clear()
        await message.answer(
            "🔎 <b>Больше объявлений пока нет.</b>\n\n"
            "Новые объявления появятся здесь автоматически.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.set_state(
        ExchangeStates.browsing
    )

    await show_offer(
        message,
        state,
        offer,
    )


@router.message(F.text == "🔍 Найти игру")
async def start_search(
    message: Message,
    state: FSMContext,
):
    user = get_user(message.from_user.id)

    if not user:
        await message.answer(
            "❌ Пользователь не найден.\n\n"
            "Выполни /start."
        )
        return

    own_offer = get_active_user_offer(
        user["id"]
    )

    if not own_offer:
        await message.answer(
            "🎮 <b>Создай своё объявление</b>\n\n"
            "Чтобы искать игры для обмена, "
            "сначала размести свою игру.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.clear()

    await state.update_data(
        platform=own_offer["platform"],
        city=own_offer["search_location"],
    )

    await show_next_offer(
        message,
        state,
        user["id"],
    )


@router.message(
    ExchangeStates.browsing,
    F.text == "❤️",
)
async def like_offer(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    user = get_user(message.from_user.id)

    if not user:
        return

    data = await state.get_data()
    offer_id = data.get("current_offer_id")

    if not offer_id:
        return

    result = save_like(
        from_user_id=user["id"],
        offer_id=offer_id,
        action="like",
    )

    if not result:
        await show_next_offer(
            message,
            state,
            user["id"],
        )
        return

    if result["type"] == "mutual":
        partner_id = result["user_id"]

        await message.answer(
            "🎉 <b>Взаимный лайк!</b>\n\n"
            "Вы понравились друг другу.\n\n"
            f"{contact_text(partner_id)}",
            reply_markup=main_menu_keyboard(),
        )

        partner = get_user_contact(partner_id)

        if partner:
            try:
                await bot.send_message(
                    partner["telegram_id"],
                    "🎉 <b>Взаимный лайк!</b>\n\n"
                    "Вы понравились друг другу.\n\n"
                    f"{contact_text(user['id'])}",
                    reply_markup=main_menu_keyboard(),
                )
            except Exception:
                pass

        await state.clear()
        return

    owner_id = result["user_id"]

    owner_offer = get_offer(offer_id)
    liker_offer = get_active_user_offer(
        user["id"]
    )

    if not owner_offer or not liker_offer:
        await show_next_offer(
            message,
            state,
            user["id"],
        )
        return

    create_notification(
        user_id=owner_id,
        notification_type="like",
        payload=(
            f"{user['id']}:{liker_offer['id']}:{offer_id}"
        ),
    )

    owner = get_user_contact(owner_id)

    if owner:
        try:
            await bot.send_message(
                owner["telegram_id"],
                "❤️ <b>Вашей игрой заинтересовались!</b>\n\n"
                "Посмотрите объявление пользователя.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Посмотреть",
                                callback_data=(
                                    f"interest:"
                                    f"{user['id']}:"
                                    f"{liker_offer['id']}:"
                                    f"{offer_id}"
                                ),
                            )
                        ]
                    ]
                ),
            )
        except Exception:
            pass

    await show_next_offer(
        message,
        state,
        user["id"],
    )