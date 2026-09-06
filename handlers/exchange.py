from html import escape

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
Message,
InlineKeyboardMarkup,
InlineKeyboardButton,
)

from database.db import (
get_connection,
get_user,
get_user_offers,
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

============================================================

STATES

============================================================

class ExchangeStates(StatesGroup):
browsing = State()
waiting_for_message = State()

============================================================

DATABASE HELPERS

============================================================

def get_offer(offer_id: int):
with get_connection() as db:
return db.execute(
“””
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
JOIN games
ON games.id = offers.game_id
JOIN users
ON users.id = offers.user_id
WHERE offers.id = ?
AND offers.status = ‘active’
“””,
(offer_id,),
).fetchone()

def get_user_contact(user_id: int):
with get_connection() as db:
return db.execute(
“””
SELECT
telegram_id,
username,
first_name
FROM users
WHERE id = ?
“””,
(user_id,),
).fetchone()

def get_current_user_offer(user_id: int):
with get_connection() as db:
return db.execute(
“””
SELECT
offers.id,
offers.platform,
offers.city,
offers.search_location
FROM offers
WHERE offers.user_id = ?
AND offers.status = ‘active’
ORDER BY offers.created_at DESC
LIMIT 1
“””,
(user_id,),
).fetchone()

============================================================

CONTACT

============================================================

def contact_text(user_id: int) -> str:
user = get_user_contact(user_id)

if not user:
    return "📱 Telegram: контакт недоступен"
username = user["username"]
if username:
    return f"📱 Telegram: @{escape(username)}"
telegram_id = user["telegram_id"]
first_name = escape(user["first_name"] or "Пользователь")
return (
    f'📱 Telegram: '
    f'<a href="tg://user?id={telegram_id}">{first_name}</a>'
)

============================================================

NOTIFICATION BUTTON

============================================================

def view_interest_keyboard(offer_id: int):
return InlineKeyboardMarkup(
inline_keyboard=[
[
InlineKeyboardButton(
text=“Посмотреть”,
callback_data=f”interest:{offer_id}”,
)
]
]
)

============================================================

OFFER TEXT

============================================================

def build_offer_text(offer) -> str:
text = (
f”🎮 {escape(str(offer[‘title’]))}\n\n”
f”🕹 Платформа: {escape(str(offer[‘platform’]))}\n”
f”💿 Формат: {escape(str(offer[‘format’]))}\n”
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
        f"\n📝 <b>Описание:</b>\n"
        f"{escape(str(offer['description']))}\n"
    )
return text

============================================================

SHOW OFFER

============================================================

async def show_offer(
message: Message,
state: FSMContext,
offer,
):
await state.update_data(
current_offer_id=offer[“id”]
)

photos = get_listing_photos(offer["id"])
for photo in photos:
    try:
        await message.answer_photo(
            photo["file_id"]
        )
    except Exception:
        pass
await message.answer(
    build_offer_text(offer),
    reply_markup=exchange_actions_keyboard(),
)

============================================================

SHOW NEXT OFFER

============================================================

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
        "❌ Не удалось определить платформу.\n\n"
        "Создай объявление заново.",
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
        "Как только появятся новые игры "
        "на этой платформе, они будут показаны здесь.",
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

============================================================

START SEARCH

============================================================

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
own_offer = get_current_user_offer(
    user["id"]
)
if not own_offer:
    await message.answer(
        "🎮 <b>Сначала создай своё объявление.</b>\n\n"
        "Чтобы искать игры для обмена, "
        "нужно сначала разместить свою игру.",
        reply_markup=main_menu_keyboard(),
    )
    return
await state.update_data(
    platform=own_offer["platform"],
    city=own_offer["city"],
)
await show_next_offer(
    message,
    state,
    user["id"],
)

============================================================

LIKE

============================================================

@router.message(
ExchangeStates.browsing,
F.text == “❤️”
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
    await message.answer(
        "❌ Объявление больше недоступно."
    )
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
# --------------------------------------------------------
# MUTUAL LIKE
# --------------------------------------------------------
if result["type"] == "mutual":
    partner_id = result["user_id"]
    text = (
        "🎉 <b>Взаимный лайк!</b>\n\n"
        "Вы понравились друг другу.\n\n"
        f"{contact_text(partner_id)}"
    )
    await message.answer(
        text,
        reply_markup=main_menu_keyboard(),
    )
    partner_telegram_id = get_user_contact(
        partner_id
    )
    if partner_telegram_id:
        try:
            await bot.send_message(
                partner_telegram_id["telegram_id"],
                (
                    "🎉 <b>Взаимный лайк!</b>\n\n"
                    "Вы понравились друг другу.\n\n"
                    f"{contact_text(user['id'])}"
                ),
            )
        except Exception:
            pass
    await state.clear()
    return
# --------------------------------------------------------
# FIRST LIKE
# --------------------------------------------------------
owner_id = result["user_id"]
create_notification(
    user_id=owner_id,
    notification_type="like",
    payload=str(offer_id),
)
owner_contact = get_user_contact(owner_id)
if owner_contact:
    try:
        notification_text = (
            "❤️ <b>Вашей игрой заинтересовались!</b>\n\n"
        )
        if result.get("liked_offer_id"):
            notification_text += (
                "Пользователь хочет обменяться "
                "своей игрой с вами.\n\n"
            )
        await bot.send_message(
            owner_contact["telegram_id"],
            notification_text,
            reply_markup=view_interest_keyboard(
                offer_id
            ),
        )
    except Exception:
        pass
await show_next_offer(
    message,
    state,
    user["id"],
)

============================================================

DISLIKE

============================================================

@router.message(
ExchangeStates.browsing,
F.text == “👎”
)
async def dislike_offer(
message: Message,
state: FSMContext,
):
user = get_user(message.from_user.id)

if not user:
    return
data = await state.get_data()
offer_id = data.get("current_offer_id")
if not offer_id:
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

============================================================

MESSAGE

============================================================

@router.message(
ExchangeStates.browsing,
F.text == “✉️”
)
async def start_message(
message: Message,
state: FSMContext,
):
data = await state.get_data()
offer_id = data.get(“current_offer_id”)

if not offer_id:
    await message.answer(
        "❌ Объявление больше недоступно."
    )
    return
await state.set_state(
    ExchangeStates.waiting_for_message
)
await message.answer(
    "💬 <b>Напиши сообщение владельцу объявления:</b>\n\n"
    "Например:\n"
    "<i>Привет! Готов обменяться, игра в отличном "
    "состоянии.</i>\n\n"
    "Отправка сообщения автоматически означает ❤️."
)

============================================================

SEND MESSAGE = LIKE

============================================================

@router.message(
ExchangeStates.waiting_for_message
)
async def send_initial_message(
message: Message,
state: FSMContext,
bot: Bot,
):
if not message.text:
await message.answer(
“✍️ Напиши сообщение текстом.”
)
return

user = get_user(message.from_user.id)
if not user:
    await state.clear()
    return
data = await state.get_data()
offer_id = data.get("current_offer_id")
if not offer_id:
    await state.clear()
    await message.answer(
        "❌ Объявление больше недоступно.",
        reply_markup=main_menu_keyboard(),
    )
    return
result = save_like(
    from_user_id=user["id"],
    offer_id=offer_id,
    action="like",
    message_text=message.text,
)
if not result:
    await state.clear()
    await message.answer(
        "❌ Не удалось отправить сообщение.",
        reply_markup=main_menu_keyboard(),
    )
    return
# --------------------------------------------------------
# MUTUAL LIKE
# --------------------------------------------------------
if result["type"] == "mutual":
    partner_id = result["user_id"]
    await message.answer(
        "🎉 <b>Взаимный лайк!</b>\n\n"
        "Вы понравились друг другу.\n\n"
        f"{contact_text(partner_id)}",
        reply_markup=main_menu_keyboard(),
    )
    partner_contact = get_user_contact(
        partner_id
    )
    if partner_contact:
        try:
            await bot.send_message(
                partner_contact["telegram_id"],
                (
                    "🎉 <b>Взаимный лайк!</b>\n\n"
                    "Вы понравились друг другу.\n\n"
                    f"{contact_text(user['id'])}"
                ),
            )
        except Exception:
            pass
    await state.clear()
    return
# --------------------------------------------------------
# FIRST LIKE + MESSAGE
# --------------------------------------------------------
owner_id = result["user_id"]
create_notification(
    user_id=owner_id,
    notification_type="like_message",
    payload=str(offer_id),
)
owner_contact = get_user_contact(owner_id)
if owner_contact:
    try:
        await bot.send_message(
            owner_contact["telegram_id"],
            (
                "❤️ <b>Вашей игрой заинтересовались!</b>\n\n"
                f"💬 «{escape(message.text)}»"
            ),
            reply_markup=view_interest_keyboard(
                offer_id
            ),
        )
    except Exception:
        pass
await state.clear()
await message.answer(
    "✅ <b>Сообщение отправлено.</b>\n\n"
    "Если владелец объявления поставит ❤️ в ответ — "
    "контакт автоматически откроется вам обоим.",
    reply_markup=main_menu_keyboard(),
)

============================================================

VIEW INTEREST

============================================================

@router.callback_query(F.data.startswith(“interest:”))
async def view_interest(
callback,
bot: Bot,
):
owner = get_user(callback.from_user.id)

if not owner:
    await callback.answer(
        "Пользователь не найден.",
        show_alert=True,
    )
    return
try:
    offer_id = int(
        callback.data.split(":", 1)[1]
    )
except (ValueError, IndexError):
    await callback.answer(
        "Некорректное объявление.",
        show_alert=True,
    )
    return
offer = get_offer(offer_id)
if not offer:
    await callback.answer(
        "Объявление больше недоступно.",
        show_alert=True,
    )
    return
# Получаем того, кто проявил интерес.
with get_connection() as db:
    liker = db.execute(
        """
        SELECT
            likes.from_user_id,
            likes.message_text
        FROM likes
        WHERE likes.offer_id = ?
          AND likes.to_user_id = ?
          AND likes.action = 'like'
        ORDER BY likes.created_at DESC
        LIMIT 1
        """,
        (
            offer_id,
            owner["id"],
        ),
    ).fetchone()
if not liker:
    await callback.answer(
        "Интерес больше недоступен.",
        show_alert=True,
    )
    return
liker_offer = get_user_offers(
    liker["from_user_id"]
)
if not liker_offer:
    await callback.answer(
        "У пользователя нет активного объявления.",
        show_alert=True,
    )
    return
liker_offer_data = liker_offer[0]
await callback.answer()
photos = get_listing_photos(
    liker_offer_data["id"]
)
for photo in photos:
    try:
        await bot.send_photo(
            callback.from_user.id,
            photo["file_id"],
        )
    except Exception:
        pass
text = (
    "❤️ <b>Пользователь заинтересовался "
    "вашей игрой!</b>\n\n"
    "Его объявление:\n\n"
    f"🎮 <b>{escape(str(liker_offer_data['title']))}</b>\n"
    f"🕹 Платформа: "
    f"<b>{escape(str(liker_offer_data['platform']))}</b>\n"
    f"💿 Формат: "
    f"<b>{escape(str(liker_offer_data['format']))}</b>\n"
)
if liker_offer_data["condition"]:
    text += (
        f"📦 Состояние: "
        f"<b>{escape(str(liker_offer_data['condition']))}</b>\n"
    )
if liker_offer_data["city"]:
    text += (
        f"📍 Город: "
        f"<b>{escape(str(liker_offer_data['city']))}</b>\n"
    )
if liker_offer_data["description"]:
    text += (
        "\n📝 <b>Описание:</b>\n"
        f"{escape(str(liker_offer_data['description']))}\n"
    )
if liker["message_text"]:
    text += (
        "\n💬 <b>Сообщение:</b>\n"
        f"«{escape(str(liker['message_text']))}»\n"
    )
text += (
    "\n\n❤️ — тоже заинтересован\n"
    "👎 — не подходит"
)
await bot.send_message(
    callback.from_user.id,
    text,
    reply_markup=exchange_actions_keyboard(),
)
# Сохраняем объявление пользователя,
# который проявил интерес.
await callback.message.answer(
    "Выбери ❤️ или 👎."
)
# Для обработки ответа владельца
# current_offer_id должен быть его объявлением.
await callback.message.answer(
    "❤️",
)
await callback.message.delete()

============================================================

FALLBACK HOME

============================================================

@router.message(F.text == “🏠 Главное меню”)
async def home_from_exchange(
message: Message,
state: FSMContext,
):
await state.clear()

await message.answer(
    "🎮 <b>Главное меню</b>",
    reply_markup=main_menu_keyboard(),
)