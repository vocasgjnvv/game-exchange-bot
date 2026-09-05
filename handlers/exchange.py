from html import escape

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from database.db import (
    get_user,
    get_next_search_offers,
    save_like,
)
from database.exchange import (
    create_or_get_deal,
    get_latest_active_deal,
    get_liked_offers,
    get_active_deals,
    get_user_telegram_id,
    add_deal_message,
)
from keyboards.keyboards import (
    exchange_actions_keyboard,
    main_menu_keyboard,
)


router = Router()


class ExchangeStates(StatesGroup):
    waiting_for_game = State()
    browsing = State()
    chat = State()


async def show_offer(message: Message, state: FSMContext, offer: dict):
    await state.update_data(current_offer_id=offer["id"])

    text = (
        f"🎮 <b>{escape(str(offer['title']))}</b>\n\n"
        f"🕹 Платформа: <b>{escape(str(offer['platform']))}</b>\n"
        f"💿 Формат: <b>{escape(str(offer['format']))}</b>\n"
    )

    if offer.get("condition"):
        text += f"📦 Состояние: <b>{escape(str(offer['condition']))}</b>\n"

    if offer.get("key_region"):
        text += f"🌍 Регион: <b>{escape(str(offer['key_region']))}</b>\n"

    if offer.get("city"):
        text += f"📍 Город: <b>{escape(str(offer['city']))}</b>\n"

    if offer.get("description"):
        text += (
            f"\n📝 <b>Описание:</b>\n"
            f"{escape(str(offer['description']))}\n"
        )

    if offer.get("first_name"):
        text += (
            f"\n👤 Пользователь: "
            f"<b>{escape(str(offer['first_name']))}</b>\n"
        )

    if offer.get("rating") is not None:
        text += f"⭐ Рейтинг: <b>{offer['rating']:.1f}</b>\n"

    text += "\n❤️ Нравится — нажми ❤️\n👎 Не подходит — нажми 👎"

    await message.answer(
        text,
        reply_markup=exchange_actions_keyboard(),
    )


async def show_next_offer(
    message: Message,
    state: FSMContext,
    user_id: int,
):
    data = await state.get_data()

    title = data.get("search_title", "")

    offers = get_next_search_offers(
        user_id=user_id,
        title=title,
    )

    if not offers:
        await state.clear()

        await message.answer(
            "🔎 Больше подходящих объявлений нет.\n\n"
            "Попробуй поискать другую игру.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.set_state(ExchangeStates.browsing)
    await show_offer(message, state, offers[0])


@router.message(F.text.in_(["🔎 Найти игру", "🔄 Создать обмен"]))
async def start_exchange(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)

    if not user:
        await message.answer(
            "Сначала зарегистрируйся через /start."
        )
        return

    await state.set_state(ExchangeStates.waiting_for_game)

    await message.answer(
        "🔎 <b>Поиск игры</b>\n\n"
        "Напиши название игры, которую хочешь найти.\n\n"
        "Например: <i>God of War</i>",
    )


@router.message(ExchangeStates.waiting_for_game)
async def process_game_search(
    message: Message,
    state: FSMContext,
):
    game_title = (message.text or "").strip()

    if not game_title:
        await message.answer("Напиши название игры.")
        return

    user = get_user(message.from_user.id)

    if not user:
        await state.clear()
        await message.answer(
            "Пользователь не найден. Нажми /start."
        )
        return

    await state.update_data(search_title=game_title)

    await show_next_offer(
        message,
        state,
        user["id"],
    )


@router.message(ExchangeStates.browsing, F.text == "❤️")
async def like_offer(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    data = await state.get_data()
    offer_id = data.get("current_offer_id")

    if not offer_id:
        await message.answer("Сейчас нет активного объявления.")
        return

    user = get_user(message.from_user.id)

    if not user:
        return

    result = save_like(
        from_user_id=user["id"],
        offer_id=offer_id,
        action="like",
    )

    if result:
        deal = create_or_get_deal(
            user1_id=user["id"],
            user2_id=result["user_id"],
            offer1_id=offer_id,
            offer2_id=result["my_offer_id"],
        )

        partner_telegram_id = get_user_telegram_id(
            result["user_id"]
        )

        if partner_telegram_id:
            try:
                await bot.send_message(
                    partner_telegram_id,
                    "🎉 <b>У вас взаимный лайк!</b>\n\n"
                    "❤️ Вы понравились друг другу.\n"
                    "Теперь можно перейти в чат и договориться "
                    "об обмене.\n\n"
                    "✉️ Нажми кнопку ✉️, чтобы открыть чат.",
                )
            except Exception:
                pass

        await message.answer(
            "🎉 <b>Взаимный лайк!</b>\n\n"
            "Вы нашли совпадение.\n"
            "Теперь можете договориться об обмене.\n\n"
            f"🤝 Сделка: <b>{escape(deal['public_id'])}</b>\n\n"
            "✉️ Нажми ✉️, чтобы открыть чат.",
            reply_markup=exchange_actions_keyboard(),
        )

    await show_next_offer(
        message,
        state,
        user["id"],
    )


@router.message(ExchangeStates.browsing, F.text == "👎")
async def dislike_offer(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()
    offer_id = data.get("current_offer_id")

    user = get_user(message.from_user.id)

    if not user or not offer_id:
        return

    save_like(
        from_user_id=user["id"],
        offer_id=offer_id,
        action="dislike",
    )

    await show_next_offer(
        message,
        state,
        user["id"],
    )


@router.message(F.text == "✉️")
async def open_chat(
    message: Message,
    state: FSMContext,
):
    user = get_user(message.from_user.id)

    if not user:
        return

    deal = get_latest_active_deal(user["id"])

    if not deal:
        await message.answer(
            "✉️ У тебя пока нет активных совпадений.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.set_state(ExchangeStates.chat)
    await state.update_data(deal_id=deal["id"])

    partner_name = deal.get("partner_name") or "пользователь"

    await message.answer(
        "✉️ <b>Чат обмена</b>\n\n"
        f"Ты общаешься с: <b>{escape(str(partner_name))}</b>\n\n"
        "Напиши сообщение — я передам его пользователю.\n"
        "🏠 — выйти из чата.",
        reply_markup=exchange_actions_keyboard(),
    )


@router.message(ExchangeStates.chat, F.text == "🏠")
async def exit_chat(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    await message.answer(
        "🏠 Ты вернулся в главное меню.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(ExchangeStates.chat)
async def send_chat_message(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    if not message.text:
        return

    data = await state.get_data()
    deal_id = data.get("deal_id")

    user = get_user(message.from_user.id)

    if not user or not deal_id:
        await state.clear()
        return

    deals = get_active_deals(user["id"])

    deal = next(
        (item for item in deals if item["id"] == deal_id),
        None,
    )

    if not deal:
        await message.answer(
            "Эта сделка больше недоступна."
        )
        await state.clear()
        return

    partner_id = deal["partner_id"]

    add_deal_message(
        deal_id=deal_id,
        sender_user_id=user["id"],
        text=message.text,
    )

    partner_telegram_id = get_user_telegram_id(partner_id)

    if not partner_telegram_id:
        await message.answer(
            "Не удалось найти пользователя."
        )
        return

    try:
        await bot.send_message(
            partner_telegram_id,
            "✉️ <b>Новое сообщение по обмену:</b>\n\n"
            f"{escape(message.text)}",
        )

        await message.answer("✅ Сообщение отправлено.")

    except Exception:
        await message.answer(
            "❌ Не удалось отправить сообщение пользователю."
        )


@router.message(F.text == "🎯 Мои совпадения")
async def my_matches(
    message: Message,
):
    user = get_user(message.from_user.id)

    if not user:
        return

    deals = get_active_deals(user["id"])

    if not deals:
        await message.answer(
            "🎯 <b>Совпадений пока нет.</b>\n\n"
            "Поставь ❤️ на интересные объявления — "
            "если пользователь тоже поставит ❤️, "
            "появится совпадение."
        )
        return

    text = "🎯 <b>Мои совпадения</b>\n\n"

    for deal in deals:
        partner_name = deal.get("partner_name") or "Пользователь"
        partner_game = deal.get("partner_game") or "Игра"

        text += (
            f"🤝 <b>{escape(str(deal['public_id']))}</b>\n"
            f"👤 {escape(str(partner_name))}\n"
            f"🎮 {escape(str(partner_game))}\n\n"
        )

    text += "✉️ Нажми ✉️, чтобы открыть чат."

    await message.answer(
        text,
        reply_markup=exchange_actions_keyboard(),
    )


@router.message(F.text == "❤️ Мои лайки")
async def my_likes(message: Message):
    user = get_user(message.from_user.id)

    if not user:
        return

    likes = get_liked_offers(user["id"])

    if not likes:
        await message.answer(
            "❤️ Ты пока ничего не лайкал."
        )
        return

    text = "❤️ <b>Мои лайки</b>\n\n"

    for item in likes:
        title = item.get("title") or "Игра"
        platform = item.get("platform") or "—"
        city = item.get("city") or "—"

        text += (
            f"🎮 <b>{escape(str(title))}</b>\n"
            f"🕹 {escape(str(platform))}\n"
            f"📍 {escape(str(city))}\n\n"
        )

    await message.answer(text)


@router.message(F.text == "🤝 Мои сделки")
async def my_deals(message: Message):
    user = get_user(message.from_user.id)

    if not user:
        return

    deals = get_active_deals(user["id"])

    if not deals:
        await message.answer(
            "🤝 Активных сделок пока нет."
        )
        return

    text = "🤝 <b>Мои сделки</b>\n\n"

    for deal in deals:
        partner_name = deal.get("partner_name") or "Пользователь"
        partner_game = deal.get("partner_game") or "Игра"

        text += (
            f"🆔 <b>{escape(str(deal['public_id']))}</b>\n"
            f"👤 {escape(str(partner_name))}\n"
            f"🎮 {escape(str(partner_game))}\n"
            f"📌 Статус: активна\n\n"
        )

    await message.answer(
        text,
        reply_markup=exchange_actions_keyboard(),
    )


@router.message(F.text == "🏠")
async def home_from_exchange(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    await message.answer(
        "🏠 Главное меню.",
        reply_markup=main_menu_keyboard(),
    )