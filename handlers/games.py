from html import escape

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from database.db import (
    get_user,
    get_or_create_game,
    create_offer,
    add_listing_photo,
    save_game_draft,
    get_game_draft,
    delete_game_draft,
)

from keyboards.keyboards import (
    main_menu_keyboard,
    search_location_keyboard,
    platform_keyboard,
    format_keyboard,
    condition_keyboard,
    description_keyboard,
    photos_keyboard,
    preview_keyboard,
)

router = Router()


# ============================================================
# CONSTANTS
# ============================================================

PLATFORMS = {
    "🎮 PlayStation 5": "PlayStation 5",
    "🎮 PlayStation 4": "PlayStation 4",
    "🎮 PlayStation 3": "PlayStation 3",
    "🎮 PlayStation 2": "PlayStation 2",
    "🎮 PlayStation 1": "PlayStation 1",
    "🎮 Xbox Series X/S": "Xbox Series X/S",
    "🎮 Xbox One": "Xbox One",
    "🎮 Xbox 360": "Xbox 360",
    "🎮 Xbox": "Xbox",
    "💻 PC / Windows": "PC / Windows",
}

FORMATS = {
    "💿 Диск": "disc",
    "🔑 Ключ": "key",
}

CONDITIONS = {
    "🔴 Плохое": "Плохое",
    "🟠 Среднее": "Среднее",
    "🟢 Хорошее": "Хорошее",
    "⭐ Отличное": "Отличное",
}


# ============================================================
# FSM
# ============================================================

class AddGameState(StatesGroup):
    waiting_for_search_location = State()
    waiting_for_city = State()
    waiting_for_platform = State()
    waiting_for_title = State()
    waiting_for_format = State()
    waiting_for_condition = State()
    waiting_for_description = State()
    waiting_for_photos = State()
    waiting_for_preview = State()


# ============================================================
# HELPERS
# ============================================================

async def save_draft(message: Message, state: FSMContext, step: str):
    data = await state.get_data()

    save_game_draft(
        telegram_id=message.from_user.id,
        data=data,
        step=step,
    )


def format_name(value: str) -> str:
    if value == "disc":
        return "💿 Диск"

    if value == "key":
        return "🔑 Ключ"

    return value


def build_preview(data: dict) -> str:
    title = escape(data.get("title", "—"))
    platform = escape(data.get("platform", "—"))
    format_type = format_name(data.get("format", "—"))
    condition = escape(data.get("condition", "—"))
    search_location = escape(data.get("search_location", "—"))
    description = escape(data.get("description", "—"))

    return (
        "📋 <b>Проверь объявление</b>\n\n"
        f"🎮 <b>{title}</b>\n"
        f"🕹 Платформа: <b>{platform}</b>\n"
        f"📦 Формат: <b>{format_type}</b>\n"
        f"📦 Состояние: <b>{condition}</b>\n"
        f"📍 Поиск: <b>{search_location}</b>\n"
        f"📝 {description}\n\n"
        "Если всё правильно — нажми «✅ Опубликовать»."
    )


# ============================================================
# START LISTING CREATION
# ============================================================

@router.message(F.text == "🔍 Найти игру")
async def find_game_start(
    message: Message,
    state: FSMContext,
):
    user = get_user(
        message.from_user.id
    )

    if not user:
        await message.answer(
            "❌ Пользователь не найден.\n\n"
            "Выполни /start."
        )
        return

    with __import__("database.db", fromlist=["get_connection"]).get_connection() as db:
        active_offer = db.execute(
            """
            SELECT id
            FROM offers
            WHERE user_id = ?
              AND status = 'active'
            LIMIT 1
            """,
            (user["id"],),
        ).fetchone()

    if active_offer:
        await message.answer(
            "🔎 У тебя уже есть активное объявление.\n\n"
            "Продолжи поиск игр для обмена."
        )

        # Передаём управление в поиск объявлений.
        # Сам поиск находится в handlers/exchange.py.
        from handlers.exchange import start_search

        await start_search(
            message,
            state,
        )
        return

    await state.clear()

    await state.set_state(
        AddGameState.waiting_for_search_location
    )

    await message.answer(
        "🔍 <b>Поиск игр для обмена</b>\n\n"
        "Сначала выбери, где искать игры:",
        reply_markup=search_location_keyboard(),
    )

# ============================================================
# SEARCH LOCATION
# ============================================================

@router.message(
    AddGameState.waiting_for_search_location,
    F.text == "🇷🇺 Вся Россия",
)
async def search_all_russia(message: Message, state: FSMContext):
    await state.update_data(
        search_location="Россия",
        city="Россия",
    )

    await save_draft(
        message,
        state,
        "waiting_for_platform",
    )

    await state.set_state(
        AddGameState.waiting_for_platform
    )

    await message.answer(
        "🎮 <b>Выбери платформу</b>",
        reply_markup=platform_keyboard(),
    )


@router.message(
    AddGameState.waiting_for_search_location,
    F.text == "🏙️ Выбрать город",
)
async def choose_city_start(message: Message, state: FSMContext):
    await state.set_state(
        AddGameState.waiting_for_city
    )

    await message.answer(
        "🏙️ Напиши город, в котором хочешь искать игры.\n\n"
        "Например: <b>Калининград</b>",
    )


@router.message(AddGameState.waiting_for_city)
async def choose_city(message: Message, state: FSMContext):
    city = (message.text or "").strip()

    if len(city) < 2:
        await message.answer(
            "❌ Название города слишком короткое.\n"
            "Напиши город ещё раз."
        )
        return

    if len(city) > 100:
        await message.answer(
            "❌ Название города слишком длинное."
        )
        return

    await state.update_data(
        search_location=city,
        city=city,
    )

    await save_draft(
        message,
        state,
        "waiting_for_platform",
    )

    await state.set_state(
        AddGameState.waiting_for_platform
    )

    await message.answer(
        "🎮 <b>Выбери платформу</b>",
        reply_markup=platform_keyboard(),
    )


# ============================================================
# PLATFORM
# ============================================================

@router.message(AddGameState.waiting_for_platform)
async def choose_platform(message: Message, state: FSMContext):
    platform = PLATFORMS.get(message.text)

    if not platform:
        await message.answer(
            "❌ Выбери платформу кнопкой ниже.",
            reply_markup=platform_keyboard(),
        )
        return

    await state.update_data(
        platform=platform
    )

    await save_draft(
        message,
        state,
        "waiting_for_title",
    )

    await state.set_state(
        AddGameState.waiting_for_title
    )

    await message.answer(
        "🎮 <b>Какую игру ты предлагаешь для обмена?</b>\n\n"
        "Напиши название игры.\n"
        "Например: <i>Red Dead Redemption 2</i>"
    )


# ============================================================
# TITLE
# ============================================================

@router.message(AddGameState.waiting_for_title)
async def choose_title(message: Message, state: FSMContext):
    title = (message.text or "").strip()

    if len(title) < 2:
        await message.answer(
            "❌ Название слишком короткое."
        )
        return

    if len(title) > 100:
        await message.answer(
            "❌ Название слишком длинное."
        )
        return

    await state.update_data(
        title=title
    )

    await save_draft(
        message,
        state,
        "waiting_for_format",
    )

    await state.set_state(
        AddGameState.waiting_for_format
    )

    await message.answer(
        "📦 <b>В каком формате игра?</b>",
        reply_markup=format_keyboard(),
    )


# ============================================================
# FORMAT
# ============================================================

@router.message(AddGameState.waiting_for_format)
async def choose_format(message: Message, state: FSMContext):
    format_type = FORMATS.get(message.text)

    if not format_type:
        await message.answer(
            "❌ Выбери формат кнопкой ниже.",
            reply_markup=format_keyboard(),
        )
        return

    await state.update_data(
        format=format_type
    )

    await save_draft(
        message,
        state,
        "waiting_for_condition",
    )

    await state.set_state(
        AddGameState.waiting_for_condition
    )

    await message.answer(
        "📦 <b>В каком состоянии игра?</b>",
        reply_markup=condition_keyboard(),
    )


# ============================================================
# CONDITION
# ============================================================

@router.message(AddGameState.waiting_for_condition)
async def choose_condition(message: Message, state: FSMContext):
    condition = CONDITIONS.get(message.text)

    if not condition:
        await message.answer(
            "❌ Выбери состояние кнопкой ниже.",
            reply_markup=condition_keyboard(),
        )
        return

    await state.update_data(
        condition=condition
    )

    await save_draft(
        message,
        state,
        "waiting_for_description",
    )

    await state.set_state(
        AddGameState.waiting_for_description
    )

    await message.answer(
        "📝 <b>Добавь описание</b>\n\n"
        "Напиши всё, что важно знать об игре.\n\n"
        "Например:\n"
        "<i>Диск полностью рабочий, есть небольшие царапины.</i>",
        reply_markup=description_keyboard(),
    )


# ============================================================
# DESCRIPTION
# ============================================================

@router.message(AddGameState.waiting_for_description)
async def choose_description(
    message: Message,
    state: FSMContext,
):
    description = (message.text or "").strip()

    if len(description) < 3:
        await message.answer(
            "❌ Описание слишком короткое."
        )
        return

    if len(description) > 1000:
        await message.answer(
            "❌ Описание слишком длинное. "
            "Максимум 1000 символов."
        )
        return

    await state.update_data(
        description=description,
        photos=[],
    )

    await save_draft(
        message,
        state,
        "waiting_for_photos",
    )

    await state.set_state(
        AddGameState.waiting_for_photos
    )

    await message.answer(
        "📸 <b>Добавь фотографии игры</b>\n\n"
        "Можешь отправить несколько фотографий.\n"
        "Когда закончишь — нажми «➡️ Пропустить».\n\n"
        "Если фотографии не нужны, сразу нажми кнопку.",
        reply_markup=photos_keyboard(),
    )


# ============================================================
# PHOTOS
# ============================================================

@router.message(
    AddGameState.waiting_for_photos,
    F.photo,
)
async def add_photo(message: Message, state: FSMContext):
    data = await state.get_data()

    photos = data.get("photos", [])

    if len(photos) >= 10:
        await message.answer(
            "❌ Можно добавить максимум 10 фотографий.\n\n"
            "Нажми «➡️ Пропустить», чтобы продолжить.",
            reply_markup=photos_keyboard(),
        )
        return

    photos.append(message.photo[-1].file_id)

    await state.update_data(
        photos=photos
    )

    await save_draft(
        message,
        state,
        "waiting_for_photos",
    )

    await message.answer(
        f"📸 Фото добавлено: {len(photos)}/10\n\n"
        "Можешь отправить ещё или нажать "
        "«➡️ Пропустить».",
        reply_markup=photos_keyboard(),
    )


@router.message(
    AddGameState.waiting_for_photos,
    F.text == "➡️ Пропустить",
)
async def finish_photos(
    message: Message,
    state: FSMContext,
):
    await save_draft(
        message,
        state,
        "waiting_for_preview",
    )

    await state.set_state(
        AddGameState.waiting_for_preview
    )

    data = await state.get_data()

    preview = build_preview(data)

    photos = data.get("photos", [])

    if photos:
        await message.answer_photo(
            photos[0],
            caption=preview,
            reply_markup=preview_keyboard(),
        )

        for photo_id in photos[1:]:
            await message.answer_photo(photo_id)

    else:
        await message.answer(
            preview,
            reply_markup=preview_keyboard(),
        )


@router.message(AddGameState.waiting_for_photos)
async def invalid_photo_input(
    message: Message,
    state: FSMContext,
):
    await message.answer(
        "📸 Отправь фотографию или нажми "
        "«➡️ Пропустить».",
        reply_markup=photos_keyboard(),
    )


# ============================================================
# PREVIEW / PUBLISH
# ============================================================

@router.message(
    AddGameState.waiting_for_preview,
    F.text == "✏️ Изменить",
)
async def edit_listing(
    message: Message,
    state: FSMContext,
):
    await state.set_state(
        AddGameState.waiting_for_title
    )

    await message.answer(
        "✏️ <b>Изменение объявления</b>\n\n"
        "Напиши название игры заново:"
    )


@router.message(
    AddGameState.waiting_for_preview,
    F.text == "✅ Опубликовать",
)
async def publish_listing(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()

    user = get_user(message.from_user.id)

    if not user:
        await state.clear()

        await message.answer(
            "❌ Профиль не найден.\n"
            "Выполни /start."
        )
        return

    title = data.get("title")
    platform = data.get("platform")
    format_type = data.get("format")
    condition = data.get("condition")
    description = data.get("description")
    search_location = data.get(
        "search_location",
        "Россия",
    )

    if not all([
        title,
        platform,
        format_type,
        condition,
        description,
    ]):
        await message.answer(
            "❌ Данные объявления заполнены не полностью.\n"
            "Начни создание объявления заново."
        )

        await state.clear()
        return

    try:
        game_id = get_or_create_game(title)

        offer_id = create_offer(
            user_id=user["id"],
            game_id=game_id,
            platform=platform,
            format_type=format_type,
            condition=condition,
            key_region=None,
            description=description,
            city=search_location,
            search_location=search_location,
        )

        photos = data.get("photos", [])

        for photo_id in photos:
            add_listing_photo(
                offer_id=offer_id,
                file_id=photo_id,
            )

        delete_game_draft(
            message.from_user.id
        )

        await state.clear()

        await message.answer(
            "✅ <b>Объявление опубликовано!</b>\n\n"
            f"🎮 <b>{escape(title)}</b>\n"
            f"🕹 {escape(platform)}\n"
            f"📦 {format_name(format_type)}\n"
            f"📦 {escape(condition)}\n"
            f"📍 {escape(search_location)}\n\n"
            "Теперь твоя игра участвует в поиске обмена.",
            reply_markup=main_menu_keyboard(),
        )

    except Exception as e:
        print(
            f"Ошибка публикации объявления: {e}"
        )

        await message.answer(
            "❌ Не удалось опубликовать объявление.\n\n"
            "Попробуй ещё раз."
        )


@router.message(AddGameState.waiting_for_preview)
async def invalid_preview_action(
    message: Message,
    state: FSMContext,
):
    await message.answer(
        "Выбери действие:",
        reply_markup=preview_keyboard(),
    )