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

        db.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                normalized_title TEXT NOT NULL
            )
        """)

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
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        """)

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
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                offer_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_user_id, offer_id),
                FOREIGN KEY (from_user_id) REFERENCES users(id),
                FOREIGN KEY (to_user_id) REFERENCES users(id),
                FOREIGN KEY (offer_id) REFERENCES offers(id)
            )
        """)

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

        db.execute("""
            CREATE TABLE IF NOT EXISTS game_drafts (
                user_id INTEGER PRIMARY KEY,
                title TEXT,
                platform TEXT,
                format TEXT,
                condition TEXT,
                key_region TEXT,
                description TEXT,
                current_step TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        db.commit()


def get_user(telegram_id: int):
    with get_connection() as db:
        return db.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
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
            (telegram_id, username, first_name)
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


def set_city(telegram_id: int, city: str):
    with get_connection() as db:
        db.execute(
            """
            UPDATE users
            SET city = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
            """,
            (city, telegram_id)
        )
        db.commit()


def get_or_create_game(title: str) -> int:
    normalized_title = title.strip().lower()

    with get_connection() as conn:
        game = conn.execute(
            """
            SELECT id
            FROM games
            WHERE normalized_title = ?
            """,
            (normalized_title,)
        ).fetchone()

        if game:
            return game["id"]

        cursor = conn.execute(
            """
            INSERT INTO games (title, normalized_title)
            VALUES (?, ?)
            """,
            (title.strip(), normalized_title)
        )

        return cursor.lastrowid


def create_offer(
    user_id: int,
    game_id: int,
    platform: str,
    format_type: str,
    condition: str | None = None,
    key_region: str | None = None,
    description: str | None = None,
    city: str | None = None,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO offers (
                user_id,
                game_id,
                platform,
                format,
                condition,
                key_region,
                description,
                city
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                game_id,
                platform,
                format_type,
                condition,
                key_region,
                description,
                city
            )
        )

        return cursor.lastrowid


def get_user_offers(user_id: int):
    with get_connection() as conn:
        return conn.execute(
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
                offers.status
            FROM offers
            JOIN games ON games.id = offers.game_id
            WHERE offers.user_id = ?
              AND offers.status = 'active'
            ORDER BY offers.created_at DESC
            """,
            (user_id,)
        ).fetchall()


def search_offers(
    title: str = "",
    platform: str = "",
    city: str = "",
    user_id: int = 0
):
    with get_connection() as conn:
        query = """
            SELECT
                offers.id,
                games.title,
                offers.platform,
                offers.format,
                offers.condition,
                offers.key_region,
                offers.description,
                offers.city,
                users.telegram_id
            FROM offers
            JOIN games ON games.id = offers.game_id
            JOIN users ON users.id = offers.user_id
            WHERE offers.status = 'active'
              AND offers.user_id != ?
        """

        params = [user_id]

        if title:
            query += " AND games.title LIKE ?"
            params.append(f"%{title}%")

        if platform:
            query += " AND offers.platform = ?"
            params.append(platform)

        if city:
            query += " AND offers.city LIKE ?"
            params.append(f"%{city}%")

        query += """
            ORDER BY offers.created_at DESC
        """

        return conn.execute(query, params).fetchall()


def delete_offer(offer_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE offers
            SET status = 'deleted'
            WHERE id = ?
              AND user_id = ?
              AND status = 'active'
            """,
            (offer_id, user_id)
        )

        return cursor.rowcount > 0


def save_game_draft(
    telegram_id: int,
    data: dict,
    step: str
):
    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT id
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        ).fetchone()

        if not user:
            return

        conn.execute(
            """
            INSERT INTO game_drafts (
                user_id,
                title,
                platform,
                format,
                condition,
                key_region,
                description,
                current_step,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)

            ON CONFLICT(user_id)
            DO UPDATE SET
                title = excluded.title,
                platform = excluded.platform,
                format = excluded.format,
                condition = excluded.condition,
                key_region = excluded.key_region,
                description = excluded.description,
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
                step
            )
        )

        conn.commit()


def get_game_draft(telegram_id: int):
    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT id
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        ).fetchone()

        if not user:
            return None

        return conn.execute(
            """
            SELECT *
            FROM game_drafts
            WHERE user_id = ?
            """,
            (user["id"],)
        ).fetchone()


def delete_game_draft(telegram_id: int):
    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT id
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        ).fetchone()

        if not user:
            return

        conn.execute(
            """
            DELETE FROM game_drafts
            WHERE user_id = ?
            """,
            (user["id"],)
        )

        conn.commit()


def save_like(
    from_user_id: int,
    offer_id: int,
    action: str
):
    with get_connection() as conn:
        offer = conn.execute(
            """
            SELECT
                id,
                user_id,
                game_id
            FROM offers
            WHERE id = ?
              AND status = 'active'
            """,
            (offer_id,)
        ).fetchone()

        if not offer:
            return None

        to_user_id = offer["user_id"]

        if from_user_id == to_user_id:
            return None

        conn.execute(
            """
            INSERT INTO likes (
                from_user_id,
                to_user_id,
                offer_id,
                action
            )
            VALUES (?, ?, ?, ?)

            ON CONFLICT(from_user_id, offer_id)
            DO UPDATE SET
                action = excluded.action,
                created_at = CURRENT_TIMESTAMP
            """,
            (
                from_user_id,
                to_user_id,
                offer_id,
                action
            )
        )

        conn.commit()

        if action != "like":
            return None

        mutual = conn.execute(
            """
            SELECT
                offers.id AS my_offer_id
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

        if not mutual:
            return None

        return {
            "user_id": to_user_id,
            "liked_offer_id": offer_id,
            "my_offer_id": mutual["my_offer_id"]
        }


def get_next_search_offers(
    user_id: int,
    title: str = "",
    platform: str = "",
    city: str = ""
):
    with get_connection() as conn:
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
                users.username,
                users.first_name,
                users.rating
            FROM offers
            JOIN games
                ON games.id = offers.game_id
            JOIN users
                ON users.id = offers.user_id
            WHERE offers.status = 'active'
              AND offers.user_id != ?
              AND users.is_blocked = 0
              AND NOT EXISTS (
                  SELECT 1
                  FROM likes
                  WHERE likes.from_user_id = ?
                    AND likes.offer_id = offers.id
              )
        """

        params = [
            user_id,
            user_id
        ]

        if title:
            query += """
                AND games.title LIKE ?
            """
            params.append(f"%{title}%")

        if platform:
            query += """
                AND offers.platform = ?
            """
            params.append(platform)

        if city:
            query += """
                AND offers.city LIKE ?
            """
            params.append(f"%{city}%")

        query += """
            ORDER BY offers.created_at DESC
            LIMIT 20
        """

        return conn.execute(
            query,
            params
        ).fetchall()


def get_offer(offer_id: int):
    with get_connection() as conn:
        return conn.execute(
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
                users.telegram_id,
                users.username,
                users.first_name,
                users.rating,
                users.reviews_count
            FROM offers
            JOIN games
                ON games.id = offers.game_id
            JOIN users
                ON users.id = offers.user_id
            WHERE offers.id = ?
              AND offers.status = 'active'
              AND users.is_blocked = 0
            """,
            (offer_id,)
        ).fetchone()


def get_user_active_offers(user_id: int):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                offers.id,
                games.title,
                offers.platform,
                offers.format,
                offers.condition,
                offers.key_region,
                offers.description,
                offers.city
            FROM offers
            JOIN games
                ON games.id = offers.game_id
            WHERE offers.user_id = ?
              AND offers.status = 'active'
            ORDER BY offers.created_at DESC
            """,
            (user_id,)
        ).fetchall()