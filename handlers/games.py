from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from database.db import (
    get_user,
    get_or_create_game,
    create_offer,
    get_user_offers,
    search_offers,
    delete_offer,
    save_game_draft,
    delete_game_draft,
)
from keyboards.keyboards import (
    platform_keyboard,
    format_keyboard,
    condition_keyboard,
    game_actions_keyboard,
)

router = Router()

@router.message(F.text == "🎮 Мои игры")
async def my_games(message: Message):
    user = get_user(message.from_user.id)

    if not user:
        await message.answer(
            "❌ Профиль не найден. Выполни /start."
        )
        return

    offers = get_user_offers(user["id"])

    if not offers:
        await message.answer(
            "🎮 <b>Мои игры</b>\n\n"
            "У тебя пока нет добавленных игр.\n\n"
            "Нажми «➕ Добавить игру», чтобы добавить первую."
        )
        return

    for offer in offers:
        text = (
            f"🆔 <b>#{offer['id']}</b>\n"
            f"🎮 <b>{offer['title']}</b>\n"
            f"🕹 Платформа: {offer['platform']}\n"
            f"📦 Формат: "
            f"{'💿 Физический диск' if offer['format'] == 'physical' else '🔑 Игровой ключ'}\n"
            f"📍 Город: {offer['city']}\n"
            f"📝 {offer['description'] or 'Без описания'}"
        )

        await message.answer(
            text,
            reply_markup=game_actions_keyboard(offer["id"])
        )
    
@router.message(F.text.startswith("🗑 Удалить #"))
async def delete_game_handler(message: Message):
    user = get_user(message.from_user.id)

    if not user:
        await message.answer(
            "❌ Профиль не найден. Выполни /start."
        )
        return

    try:
        offer_id = int(message.text.split("#")[1])
    except (ValueError, IndexError):
        await message.answer(
            "❌ Не удалось определить игру."
        )
        return

    deleted = delete_offer(offer_id, user["id"])

    if not deleted:
        await message.answer(
            "❌ Игра не найдена или уже удалена."
        )
        return

    await message.answer(
        f"🗑 <b>Игра #{offer_id} удалена.</b>\n\n"
        "Она больше не будет отображаться "
        "в твоих активных играх."
    )


class AddGameState(StatesGroup):
    waiting_for_title = State()
    waiting_for_platform = State()
    waiting_for_format = State()
    waiting_for_condition = State()
    waiting_for_region = State()
    waiting_for_description = State()


@router.message(F.text == "➕ Добавить игру")
async def add_game_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AddGameState.waiting_for_title)

    await message.answer(
        "🎮 <b>Добавление игры</b>\n\n"
        "Напиши название игры.\n\n"
        "Например: <i>God of War</i>"
    )


@router.message(AddGameState.waiting_for_title)
async def add_game_title(message: Message, state: FSMContext):
    title = (message.text or "").strip()

    if len(title) < 2:
        await message.answer("❌ Название слишком короткое.")
        return

    if len(title) > 100:
        await message.answer("❌ Название слишком длинное.")
        return

    await state.update_data(title=title)

    data = await state.get_data()
    save_game_draft(
        message.from_user.id,
        data,
        "waiting_for_platform"
    )

await state.set_state(AddGameState.waiting_for_platform)
    await message.answer(
        "🎮 На какой платформе игра?",
        reply_markup=platform_keyboard()
    )


@router.message(AddGameState.waiting_for_platform)
async def add_game_platform(message: Message, state: FSMContext):
    platform_map = {
        "🎮 PS3": "PS3",
        "🎮 PS4": "PS4",
        "🎮 PS5": "PS5",
        "🟩 Xbox One": "Xbox One",
        "🟩 Xbox Series X/S": "Xbox Series X/S",
        "💻 PC": "PC",
    }

    platform = platform_map.get(message.text)

    if not platform:
        await message.answer(
            "❌ Выбери платформу кнопкой ниже.",
            reply_markup=platform_keyboard()
        )
        return

    await state.update_data(platform=platform)
    await state.set_state(AddGameState.waiting_for_format)

    await message.answer(
        "📦 В каком формате у тебя игра?",
        reply_markup=format_keyboard()
    )


@router.message(AddGameState.waiting_for_format)
async def add_game_format(message: Message, state: FSMContext):
    if message.text == "💿 Физический диск":
        await state.update_data(
            format="physical",
            key_region=None
        )

        await state.set_state(AddGameState.waiting_for_condition)

        await message.answer(
            "💿 В каком состоянии диск?",
            reply_markup=condition_keyboard()
        )
        return

    if message.text == "🔑 Игровой ключ":
        await state.update_data(
            format="key",
            condition=None
        )

        await state.set_state(AddGameState.waiting_for_region)

        await message.answer(
            "🌍 Укажи регион активации ключа.\n\n"
            "Например:\n"
            "🇷🇺 RU\n"
            "🇪🇺 EU\n"
            "🌎 Global\n\n"
            "⚠️ Сам ключ отправлять не нужно."
        )
        return

    await message.answer(
        "❌ Выбери формат кнопкой ниже.",
        reply_markup=format_keyboard()
    )


@router.message(AddGameState.waiting_for_condition)
async def add_game_condition(message: Message, state: FSMContext):
    condition_map = {
        "🟢 Отличное": "Отличное",
        "🟡 Хорошее": "Хорошее",
        "🟠 Есть следы использования": "Есть следы использования",
    }

    condition = condition_map.get(message.text)

    if not condition:
        await message.answer(
            "❌ Выбери состояние кнопкой ниже.",
            reply_markup=condition_keyboard()
        )
        return

    await state.update_data(condition=condition)
    await state.set_state(AddGameState.waiting_for_description)

    await message.answer(
        "📝 Теперь напиши краткое описание игры.\n\n"
        "Например:\n"
        "<i>Диск в хорошем состоянии, всё работает.</i>"
    )


@router.message(AddGameState.waiting_for_region)
async def add_game_region(message: Message, state: FSMContext):
    region = (message.text or "").strip()

    if len(region) < 2:
        await message.answer(
            "❌ Укажи корректный регион активации."
        )
        return

    if len(region) > 50:
        await message.answer(
            "❌ Название региона слишком длинное."
        )
        return

    await state.update_data(key_region=region)
    await state.set_state(AddGameState.waiting_for_description)

    await message.answer(
        "📝 Теперь напиши краткое описание игры.\n\n"
        "Например:\n"
        "<i>Ключ новый, регион EU.</i>\n\n"
        "⚠️ Сам ключ отправлять не нужно."
    )


@router.message(AddGameState.waiting_for_description)
async def add_game_description(message: Message, state: FSMContext):
    description = (message.text or "").strip()

    if len(description) < 3:
        await message.answer(
            "❌ Описание слишком короткое."
        )
        return

    if len(description) > 1000:
        await message.answer(
            "❌ Описание слишком длинное."
        )
        return

    data = await state.get_data()

    user = get_user(message.from_user.id)

    if not user:
        await state.clear()
        await message.answer(
            "❌ Профиль не найден. Выполни /start."
        )
        return

    city = user["city"]

    if not city:
        await state.clear()
        await message.answer(
            "❌ Сначала укажи город в профиле."
        )
        return

    try:
        game_id = get_or_create_game(
            title=data["title"]
        )

        offer_id = create_offer(
            user_id=user["id"],
            game_id=game_id,
            platform=data["platform"],
            format_type=data["format"],
            condition=data.get("condition"),
            key_region=data.get("key_region"),
            description=description,
            city=city
        )

    except Exception as e:
        print(f"Ошибка сохранения игры: {e}")

        await state.clear()

        await message.answer(
            "❌ Не удалось сохранить игру.\n\n"
            "Попробуй добавить её ещё раз."
        )
        return

    await state.clear()

    await message.answer(
        "✅ <b>Игра успешно добавлена!</b>\n\n"
        f"🎮 Игра: <b>{data['title']}</b>\n"
        f"🕹 Платформа: <b>{data['platform']}</b>\n"
        f"📦 Формат: <b>"
        f"{'Физический диск' if data['format'] == 'physical' else 'Игровой ключ'}"
        f"</b>\n"
        f"🌍 Регион: <b>{data.get('key_region') or '—'}</b>\n"
        f"💿 Состояние: <b>{data.get('condition') or '—'}</b>\n"
        f"📍 Город: <b>{city}</b>\n"
        f"📝 Описание: <b>{description}</b>\n\n"
        f"🆔 Объявление №{offer_id}\n\n"
        "🎉 Теперь эта игра сохранена и может участвовать в поиске обмена."
    )