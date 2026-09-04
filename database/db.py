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

        db.commit()


def get_user(telegram_id: int):
    with get_connection() as db:
        return db.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        ).fetchone()


def create_user(telegram_id: int, username: str | None, first_name: str):
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
            "SELECT id FROM games WHERE normalized_title = ?",
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
                city,
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
            ORDER BY offers.created_at DESC
            """,
            (user_id,)
        ).fetchall()
        
def delete_offer(offer_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE offers
            SET status = 'deleted'
            WHERE id = ? AND user_id = ? AND status = 'active'
            """,
            (offer_id, user_id)
        )

        return cursor.rowcount > 0