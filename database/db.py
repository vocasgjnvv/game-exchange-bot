import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "game_exchange.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with get_connection() as db:

        # =========================
        # USERS
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT NOT NULL,
                city TEXT,
                rating REAL NOT NULL DEFAULT 5.0,
                reviews_count INTEGER NOT NULL DEFAULT 0,
                completed_deals INTEGER NOT NULL DEFAULT 0,
                rules_accepted INTEGER NOT NULL DEFAULT 0,
                is_blocked INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =========================
        # GAMES
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                normalized_title TEXT NOT NULL UNIQUE
            )
        """)

        # =========================
        # OFFERS / LISTINGS
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                format TEXT NOT NULL,
                condition TEXT,
                key_region TEXT,
                description TEXT,
                city TEXT NOT NULL,
                search_location TEXT NOT NULL DEFAULT 'all_russia',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        """)

        # Добавляем поле search_location в старую БД,
        # если таблица offers уже существовала.
        try:
            db.execute("""
                ALTER TABLE offers
                ADD COLUMN search_location TEXT NOT NULL DEFAULT 'all_russia'
            """)
        except sqlite3.OperationalError:
            pass

        # =========================
        # PHOTOS
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS listing_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offer_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (offer_id)
                    REFERENCES offers(id)
                    ON DELETE CASCADE
            )
        """)

        # =========================
        # LIKES / INTERESTS
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                offer_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                message_text TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(from_user_id, offer_id),

                FOREIGN KEY (from_user_id) REFERENCES users(id),
                FOREIGN KEY (to_user_id) REFERENCES users(id),
                FOREIGN KEY (offer_id) REFERENCES offers(id)
            )
        """)

        # Для уже существующей таблицы likes
        try:
            db.execute("""
                ALTER TABLE likes
                ADD COLUMN message_text TEXT
            """)
        except sqlite3.OperationalError:
            pass

        # =========================
        # INITIAL MESSAGES
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS offer_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                offer_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (from_user_id) REFERENCES users(id),
                FOREIGN KEY (to_user_id) REFERENCES users(id),
                FOREIGN KEY (offer_id) REFERENCES offers(id)
            )
        """)

        # =========================
        # MATCHES
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                offer1_id INTEGER NOT NULL,
                offer2_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user1_id, user2_id, offer1_id, offer2_id),

                FOREIGN KEY (user1_id) REFERENCES users(id),
                FOREIGN KEY (user2_id) REFERENCES users(id),
                FOREIGN KEY (offer1_id) REFERENCES offers(id),
                FOREIGN KEY (offer2_id) REFERENCES offers(id)
            )
        """)

        # =========================
        # NOTIFICATIONS
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                payload TEXT,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # =========================
        # OLD / COMPATIBILITY TABLES
        # Пока оставляем, чтобы старая БД
        # не ломалась.
        # =========================

        db.execute("""
            CREATE TABLE IF NOT EXISTS wanted_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                format TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 1,

                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                public_id TEXT UNIQUE NOT NULL,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                offer1_id INTEGER NOT NULL,
                offer2_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                closed_at TEXT,

                FOREIGN KEY (user1_id) REFERENCES users(id),
                FOREIGN KEY (user2_id) REFERENCES users(id),
                FOREIGN KEY (offer1_id) REFERENCES offers(id),
                FOREIGN KEY (offer2_id) REFERENCES offers(id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS deal_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL,
                sender_user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (deal_id) REFERENCES deals(id),
                FOREIGN KEY (sender_user_id) REFERENCES users(id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                text TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(deal_id, from_user_id),

                FOREIGN KEY (deal_id) REFERENCES deals(id),
                FOREIGN KEY (from_user_id) REFERENCES users(id),
                FOREIGN KEY (to_user_id) REFERENCES users(id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_user_id INTEGER NOT NULL,
                reported_user_id INTEGER NOT NULL,
                deal_id INTEGER,
                reason TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (reporter_user_id) REFERENCES users(id),
                FOREIGN KEY (reported_user_id) REFERENCES users(id),
                FOREIGN KEY (deal_id) REFERENCES deals(id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                offer_id INTEGER NOT NULL,

                PRIMARY KEY (user_id, offer_id),

                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (offer_id) REFERENCES offers(id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS blocks (
                user_id INTEGER NOT NULL,
                blocked_user_id INTEGER NOT NULL,

                PRIMARY KEY (user_id, blocked_user_id),

                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (blocked_user_id) REFERENCES users(id)
            )
        """)

        # =========================
        # GAME DRAFTS
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS game_drafts (
                user_id INTEGER PRIMARY KEY,

                title TEXT,
                platform TEXT,
                format TEXT,
                condition TEXT,
                key_region TEXT,
                description TEXT,

                search_location TEXT,
                photos TEXT,

                current_step TEXT NOT NULL,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Добавляем новые поля в старую таблицу drafts.
        try:
            db.execute("""
                ALTER TABLE game_drafts
                ADD COLUMN search_location TEXT
            """)
        except sqlite3.OperationalError:
            pass

        try:
            db.execute("""
                ALTER TABLE game_drafts
                ADD COLUMN photos TEXT
            """)
        except sqlite3.OperationalError:
            pass

        db.commit()


# ============================================================
# USERS
# ============================================================

def get_user(telegram_id: int):
    with get_connection() as db:
        return db.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        ).fetchone()


def create_user(
    telegram_id: int,
    username: str | None,
    first_name: str
):
    with get_connection() as db:
        db.execute(
            """
            INSERT OR IGNORE INTO users
            (telegram_id, username, first_name)
            VALUES (?, ?, ?)
            """,
            (
                telegram_id,
                username,
                first_name
            )
        )
        db.commit()


def accept_rules(telegram_id: int):
    with get_connection() as db:
        db.execute(
            """
            UPDATE users
            SET rules_accepted = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )
        db.commit()


# ============================================================
# GAMES
# ============================================================

def get_or_create_game(title: str) -> int:
    title = title.strip()
    normalized_title = title.lower()

    with get_connection() as db:

        game = db.execute(
            """
            SELECT id
            FROM games
            WHERE normalized_title = ?
            """,
            (normalized_title,)
        ).fetchone()

        if game:
            return game["id"]

        cursor = db.execute(
            """
            INSERT INTO games
            (
                title,
                normalized_title
            )
            VALUES (?, ?)
            """,
            (
                title,
                normalized_title
            )
        )

        db.commit()

        return cursor.lastrowid


# ============================================================
# OFFERS
# ============================================================

def create_offer(
    user_id: int,
    game_id: int,
    platform: str,
    format_type: str,
    condition: str | None = None,
    key_region: str | None = None,
    description: str | None = None,
    city: str | None = None,
    search_location: str = "all_russia",
) -> int:

    with get_connection() as db:

        cursor = db.execute(
            """
            INSERT INTO offers (
                user_id,
                game_id,
                platform,
                format,
                condition,
                key_region,
                description,
                city,
                search_location,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (
                user_id,
                game_id,
                platform,
                format_type,
                condition,
                key_region,
                description,
                city or "Не указан",
                search_location
            )
        )

        db.commit()

        return cursor.lastrowid


def get_user_offers(user_id: int):
    with get_connection() as db:
        return db.execute(
            """
            SELECT
                offers.id,
                games.title,
                offers.platform,
                offers.format,
                offers.condition,
                offers.key_region,
                offers.description,
                offers.city,
                offers.search_location,
                offers.status
            FROM offers
            JOIN games
                ON games.id = offers.game_id
            WHERE offers.user_id = ?
              AND offers.status = 'active'
            ORDER BY offers.created_at DESC
            """,
            (user_id,)
        ).fetchall()


def delete_offer(
    offer_id: int,
    user_id: int
) -> bool:

    with get_connection() as db:

        cursor = db.execute(
            """
            UPDATE offers
            SET status = 'deleted'
            WHERE id = ?
              AND user_id = ?
              AND status = 'active'
            """,
            (
                offer_id,
                user_id
            )
        )

        db.commit()

        return cursor.rowcount > 0


# ============================================================
# PHOTOS
# ============================================================

def add_listing_photo(
    offer_id: int,
    file_id: str
):
    with get_connection() as db:

        db.execute(
            """
            INSERT INTO listing_photos
            (
                offer_id,
                file_id
            )
            VALUES (?, ?)
            """,
            (
                offer_id,
                file_id
            )
        )

        db.commit()


def get_listing_photos(offer_id: int):
    with get_connection() as db:

        return db.execute(
            """
            SELECT
                id,
                file_id
            FROM listing_photos
            WHERE offer_id = ?
            ORDER BY id ASC
            """,
            (offer_id,)
        ).fetchall()


# ============================================================
# FEED
# ============================================================

def get_next_search_offers(
    user_id: int,
    platform: str,
    city: str | None = None
):

    with get_connection() as db:

        query = """
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
                users.first_name,
                users.username
            FROM offers
            JOIN games
                ON games.id = offers.game_id
            JOIN users
                ON users.id = offers.user_id
            WHERE offers.status = 'active'
              AND offers.user_id != ?
              AND offers.platform = ?

              AND NOT EXISTS (
                  SELECT 1
                  FROM likes
                  WHERE likes.from_user_id = ?
                    AND likes.offer_id = offers.id
              )
        """

        params = [
            user_id,
            platform,
            user_id
        ]

        if city:
            query += """
                ORDER BY
                    CASE
                        WHEN offers.city = ? THEN 0
                        ELSE 1
                    END,
                    RANDOM()
            """

            params.append(city)

        else:
            query += """
                ORDER BY RANDOM()
            """

        query += """
            LIMIT 1
        """

        return db.execute(
            query,
            params
        ).fetchone()


# ============================================================
# LIKES / INTERESTS
# ============================================================

def save_like(
    from_user_id: int,
    offer_id: int,
    action: str,
    message_text: str | None = None
):

    with get_connection() as db:

        offer = db.execute(
            """
            SELECT
                id,
                user_id
            FROM offers
            WHERE id = ?
              AND status = 'active'
            """,
            (offer_id,)
        ).fetchone()

        if not offer:
            return None

        to_user_id = offer["user_id"]

        # Нельзя лайкнуть самого себя.
        if from_user_id == to_user_id:
            return None

        # Проверяем существующее взаимодействие.
        existing = db.execute(
            """
            SELECT *
            FROM likes
            WHERE from_user_id = ?
              AND offer_id = ?
            """,
            (
                from_user_id,
                offer_id
            )
        ).fetchone()

        if existing:
            return None

        db.execute(
            """
            INSERT INTO likes
            (
                from_user_id,
                to_user_id,
                offer_id,
                action,
                message_text
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                from_user_id,
                to_user_id,
                offer_id,
                action,
                message_text
            )
        )

        db.commit()

        # Дизлайк — просто сохраняем.
        if action == "dislike":
            return {
                "type": "dislike",
                "user_id": to_user_id,
                "offer_id": offer_id
            }

        # Ищем взаимный лайк:
        # владелец объявления ранее лайкнул
        # объявление текущего пользователя.
        mutual = db.execute(
            """
            SELECT
                likes.id,
                likes.offer_id AS my_offer_id
            FROM likes
            JOIN offers
                ON offers.id = likes.offer_id
            WHERE likes.from_user_id = ?
              AND likes.to_user_id = ?
              AND likes.action = 'like'
              AND offers.status = 'active'
            ORDER BY likes.created_at DESC
            LIMIT 1
            """,
            (
                to_user_id,
                from_user_id
            )
        ).fetchone()

        if mutual:

            existing_match = db.execute(
                """
                SELECT *
                FROM matches
                WHERE
                    (
                        user1_id = ?
                        AND user2_id = ?
                        AND offer1_id = ?
                        AND offer2_id = ?
                    )
                    OR
                    (
                        user1_id = ?
                        AND user2_id = ?
                        AND offer1_id = ?
                        AND offer2_id = ?
                    )
                LIMIT 1
                """,
                (
                    from_user_id,
                    to_user_id,
                    offer_id,
                    mutual["my_offer_id"],

                    to_user_id,
                    from_user_id,
                    mutual["my_offer_id"],
                    offer_id
                )
            ).fetchone()

            if not existing_match:

                cursor = db.execute(
                    """
                    INSERT INTO matches
                    (
                        user1_id,
                        user2_id,
                        offer1_id,
                        offer2_id
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        from_user_id,
                        to_user_id,
                        offer_id,
                        mutual["my_offer_id"]
                    )
                )

                match_id = cursor.lastrowid

                db.commit()

            else:
                match_id = existing_match["id"]

            return {
                "type": "mutual",
                "match_id": match_id,
                "user_id": to_user_id,
                "liked_offer_id": offer_id,
                "my_offer_id": mutual["my_offer_id"]
            }

        return {
            "type": "like",
            "user_id": to_user_id,
            "liked_offer_id": offer_id
        }


# ============================================================
# NOTIFICATIONS
# ============================================================

def create_notification(
    user_id: int,
    notification_type: str,
    payload: str | None = None
):

    with get_connection() as db:

        cursor = db.execute(
            """
            INSERT INTO notifications
            (
                user_id,
                type,
                payload
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                notification_type,
                payload
            )
        )

        db.commit()

        return cursor.lastrowid


# ============================================================
# DRAFTS
# ============================================================

def save_game_draft(
    telegram_id: int,
    data: dict,
    step: str
):

    with get_connection() as db:

        user = db.execute(
            """
            SELECT id
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        ).fetchone()

        if not user:
            return

        photos = data.get("photos")

        if isinstance(photos, list):
            photos = "|".join(photos)

        db.execute(
            """
            INSERT INTO game_drafts
            (
                user_id,
                title,
                platform,
                format,
                condition,
                key_region,
                description,
                search_location,
                photos,
                current_step,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)

            ON CONFLICT(user_id)
            DO UPDATE SET
                title = excluded.title,
                platform = excluded.platform,
                format = excluded.format,
                condition = excluded.condition,
                key_region = excluded.key_region,
                description = excluded.description,
                search_location = excluded.search_location,
                photos = excluded.photos,
                current_step = excluded.current_step,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user["id"],
                data.get("title"),
                data.get("platform"),
                data.get("format"),
                data.get("condition"),
                data.get("key_region"),
                data.get("description"),
                data.get("search_location"),
                photos,
                step
            )
        )

        db.commit()


def get_game_draft(telegram_id: int):

    with get_connection() as db:

        user = db.execute(
            """
            SELECT id
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        ).fetchone()

        if not user:
            return None

        row = db.execute(
            """
            SELECT *
            FROM game_drafts
            WHERE user_id = ?
            """,
            (user["id"],)
        ).fetchone()

        return row


def delete_game_draft(telegram_id: int):

    with get_connection() as db:

        user = db.execute(
            """
            SELECT id
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        ).fetchone()

        if not user:
            return

        db.execute(
            """
            DELETE FROM game_drafts
            WHERE user_id = ?
            """,
            (user["id"],)
        )

        db.commit()

# ============================================================
# COMPATIBILITY
# ============================================================

def set_city(telegram_id: int, city: str):
    with get_connection() as db:
        db.execute(
            """
            UPDATE users
            SET city = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
            """,
            (city.strip(), telegram_id)
        )
        db.commit()


def search_offers(
    user_id: int,
    title: str | None = None,
    platform: str | None = None
):
    with get_connection() as db:
        query = """
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
            JOIN games
                ON games.id = offers.game_id
            WHERE offers.status = 'active'
              AND offers.user_id != ?
        """

        params = [user_id]

        if title:
            query += """
                AND games.normalized_title LIKE ?
            """
            params.append(f"%{title.strip().lower()}%")

        if platform:
            query += """
                AND offers.platform = ?
            """
            params.append(platform)

        query += """
            ORDER BY offers.created_at DESC
        """

        return db.execute(query, params).fetchall()