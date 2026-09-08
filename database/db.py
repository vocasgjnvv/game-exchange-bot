import sqlite3
from contextlib import contextmanager
from pathlib import Path


DB_PATH = Path("game_exchange.db")


@contextmanager
def get_connection():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    try:
        yield db
    finally:
        db.close()


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
                first_name TEXT,
                city TEXT,

                rating REAL DEFAULT 0,
                reviews_count INTEGER DEFAULT 0,
                deals_count INTEGER DEFAULT 0,

                rules_accepted INTEGER DEFAULT 0,
                is_blocked INTEGER DEFAULT 0,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                blocked_at TEXT
            )
        """)

        # =========================
        # GAME DRAFTS
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS game_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,

                game_title TEXT,
                platform TEXT,
                format TEXT,
                condition TEXT,
                description TEXT,

                search_location TEXT,
                step TEXT,

                photos TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)

        # =========================
        # GAMES
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =========================
        # OFFERS
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,
                game_id INTEGER NOT NULL,

                platform TEXT NOT NULL,
                format TEXT NOT NULL,
                condition TEXT NOT NULL,

                key_region TEXT,
                description TEXT,

                city TEXT NOT NULL,
                search_location TEXT NOT NULL DEFAULT 'all_russia',

                status TEXT NOT NULL DEFAULT 'active',

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (game_id)
                    REFERENCES games(id)
            )
        """)

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

                FOREIGN KEY (from_user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (to_user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

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
                from_offer_id INTEGER,

                action TEXT NOT NULL,
                message_text TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(from_user_id, offer_id),

                FOREIGN KEY (from_user_id)
                    REFERENCES users(id),

                FOREIGN KEY (to_user_id)
                    REFERENCES users(id),

                FOREIGN KEY (offer_id)
                    REFERENCES offers(id)
            )
        """)

        # =========================
        # MIGRATION: message_text
        # =========================
        try:
            db.execute("""
                ALTER TABLE likes
                ADD COLUMN message_text TEXT
            """)
        except sqlite3.OperationalError:
            pass

        # =========================
        # MIGRATION: from_offer_id
        # =========================
        try:
            db.execute("""
                ALTER TABLE likes
                ADD COLUMN from_offer_id INTEGER
            """)
        except sqlite3.OperationalError:
            pass

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

                UNIQUE(
                    user1_id,
                    user2_id,
                    offer1_id,
                    offer2_id
                ),

                FOREIGN KEY (user1_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (user2_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (offer1_id)
                    REFERENCES offers(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (offer2_id)
                    REFERENCES offers(id)
                    ON DELETE CASCADE
            )
        """)

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
    username: str | None = None,
    first_name: str | None = None
):
    with get_connection() as db:
        db.execute(
            """
            INSERT OR IGNORE INTO users
            (
                telegram_id,
                username,
                first_name
            )
            VALUES (?, ?, ?)
            """,
            (
                telegram_id,
                username,
                first_name
            )
        )

        db.execute(
            """
            UPDATE users
            SET
                username = ?,
                first_name = ?
            WHERE telegram_id = ?
            """,
            (
                username,
                first_name,
                telegram_id
            )
        )

        db.commit()

        return db.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        ).fetchone()


# ============================================================
# GAMES
# ============================================================

def get_or_create_game(title: str):
    with get_connection() as db:

        game = db.execute(
            """
            SELECT *
            FROM games
            WHERE title = ?
            """,
            (title,)
        ).fetchone()

        if game:
            return game

        cursor = db.execute(
            """
            INSERT INTO games (title)
            VALUES (?)
            """,
            (title,)
        )

        db.commit()

        return db.execute(
            """
            SELECT *
            FROM games
            WHERE id = ?
            """,
            (cursor.lastrowid,)
        ).fetchone()


# ============================================================
# OFFERS
# ============================================================

def create_offer(
    user_id: int,
    game_id: int,
    platform: str,
    format_type: str,
    condition: str,
    key_region: str | None = None,
    description: str | None = None,
    city: str | None = None,
    search_location: str = "all_russia"
):
    with get_connection() as db:

        cursor = db.execute(
            """
            INSERT INTO offers
            (
                user_id,
                game_id,
                platform,
                format,
                condition,
                key_region,
                description,
                city,
                search_location
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                game_id,
                platform,
                format_type,
                condition,
                key_region,
                description,
                city,
                search_location
            )
        )

        db.commit()

        return cursor.lastrowid


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
            photos = ",".join(photos)

        db.execute(
            """
            INSERT INTO game_drafts
            (
                user_id,
                game_title,
                platform,
                format,
                condition,
                description,
                search_location,
                step,
                photos,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)

            ON CONFLICT(user_id)
            DO UPDATE SET
                game_title = excluded.game_title,
                platform = excluded.platform,
                format = excluded.format,
                condition = excluded.condition,
                description = excluded.description,
                search_location = excluded.search_location,
                step = excluded.step,
                photos = excluded.photos,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user["id"],
                data.get("game_title"),
                data.get("platform"),
                data.get("format"),
                data.get("condition"),
                data.get("description"),
                data.get("search_location"),
                step,
                photos
            )
        )

        db.commit()


def get_game_draft(telegram_id: int):
    with get_connection() as db:

        return db.execute(
            """
            SELECT
                game_drafts.*
            FROM game_drafts
            JOIN users
                ON users.id = game_drafts.user_id
            WHERE users.telegram_id = ?
            """,
            (telegram_id,)
        ).fetchone()


def delete_game_draft(telegram_id: int):
    with get_connection() as db:

        db.execute(
            """
            DELETE FROM game_drafts
            WHERE user_id = (
                SELECT id
                FROM users
                WHERE telegram_id = ?
            )
            """,
            (telegram_id,)
        )

        db.commit()


# ============================================================
# LIKES
# ============================================================

def save_like(
    from_user_id: int,
    offer_id: int,
    action: str,
    message_text: str | None = None,
    from_offer_id: int | None = None
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

        # Нельзя поставить реакцию на собственное объявление
        if from_user_id == to_user_id:
            return None

        # Нельзя создать одинаковый интерес дважды
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

        # Для лайка проверяем объявление самого пользователя
        if action == "like":

            if from_offer_id is None:
                return None

            source_offer = db.execute(
                """
                SELECT id
                FROM offers
                WHERE id = ?
                  AND user_id = ?
                  AND status = 'active'
                """,
                (
                    from_offer_id,
                    from_user_id
                )
            ).fetchone()

            if not source_offer:
                return None

        db.execute(
            """
            INSERT INTO likes
            (
                from_user_id,
                to_user_id,
                offer_id,
                from_offer_id,
                action,
                message_text
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                from_user_id,
                to_user_id,
                offer_id,
                from_offer_id,
                action,
                message_text
            )
        )

        db.commit()

        # =========================
        # DISLIKE
        # =========================
        if action == "dislike":

            return {
                "type": "dislike",
                "user_id": to_user_id,
                "offer_id": offer_id
            }

        # =========================
        # CHECK MUTUAL LIKE
        # =========================
        mutual = db.execute(
            """
            SELECT
                likes.id,
                likes.from_offer_id AS my_offer_id
            FROM likes
            WHERE likes.from_user_id = ?
              AND likes.to_user_id = ?
              AND likes.offer_id = ?
              AND likes.action = 'like'
              AND likes.from_offer_id IS NOT NULL
              AND EXISTS (
                  SELECT 1
                  FROM offers
                  WHERE offers.id = likes.from_offer_id
                    AND offers.user_id = ?
                    AND offers.status = 'active'
              )
            ORDER BY likes.created_at DESC
            LIMIT 1
            """,
            (
                to_user_id,
                from_user_id,
                from_offer_id,
                from_user_id
            )
        ).fetchone()

        # =========================
        # MUTUAL LIKE
        # =========================
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
                    from_offer_id,
                    offer_id,

                    to_user_id,
                    from_user_id,
                    offer_id,
                    from_offer_id
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
                        from_offer_id,
                        offer_id
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
                "my_offer_id": from_offer_id
            }

        # =========================
        # NORMAL LIKE
        # =========================
        return {
            "type": "like",
            "user_id": to_user_id,
            "liked_offer_id": offer_id
        }