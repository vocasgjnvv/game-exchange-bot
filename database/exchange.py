import uuid
from database.db import get_connection


def create_or_get_deal(
    user1_id: int,
    user2_id: int,
    offer1_id: int,
    offer2_id: int
):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM deals
        WHERE status = 'active'
        AND (
            (user1_id = ? AND user2_id = ? AND offer1_id = ? AND offer2_id = ?)
            OR
            (user1_id = ? AND user2_id = ? AND offer1_id = ? AND offer2_id = ?)
        )
        LIMIT 1
        """,
        (
            user1_id, user2_id, offer1_id, offer2_id,
            user2_id, user1_id, offer2_id, offer1_id
        )
    ).fetchone()

    if row:
        conn.close()
        return dict(row)

    public_id = "GE-" + uuid.uuid4().hex[:8].upper()

    cursor = conn.execute(
        """
        INSERT INTO deals (
            public_id,
            user1_id,
            user2_id,
            offer1_id,
            offer2_id,
            status
        )
        VALUES (?, ?, ?, ?, ?, 'active')
        """,
        (
            public_id,
            user1_id,
            user2_id,
            offer1_id,
            offer2_id
        )
    )

    conn.commit()

    row = conn.execute(
        "SELECT * FROM deals WHERE id = ?",
        (cursor.lastrowid,)
    ).fetchone()

    conn.close()

    return dict(row)


def get_active_deals(user_id: int):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            d.*,
            CASE
                WHEN d.user1_id = ? THEN d.user2_id
                ELSE d.user1_id
            END AS partner_id,

            CASE
                WHEN d.user1_id = ? THEN u2.first_name
                ELSE u1.first_name
            END AS partner_name,

            CASE
                WHEN d.user1_id = ? THEN u2.username
                ELSE u1.username
            END AS partner_username,

            CASE
                WHEN d.user1_id = ? THEN g2.title
                ELSE g1.title
            END AS partner_game

        FROM deals d

        JOIN users u1 ON u1.id = d.user1_id
        JOIN users u2 ON u2.id = d.user2_id

        JOIN offers o1 ON o1.id = d.offer1_id
        JOIN offers o2 ON o2.id = d.offer2_id

        JOIN games g1 ON g1.id = o1.game_id
        JOIN games g2 ON g2.id = o2.game_id

        WHERE d.status = 'active'
        AND (d.user1_id = ? OR d.user2_id = ?)

        ORDER BY d.created_at DESC
        """,
        (
            user_id,
            user_id,
            user_id,
            user_id,
            user_id,
            user_id
        )
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_latest_active_deal(user_id: int):
    deals = get_active_deals(user_id)

    if not deals:
        return None

    return deals[0]


def get_user_telegram_id(user_id: int):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT telegram_id
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    if not row:
        return None

    return row["telegram_id"]


def get_liked_offers(user_id: int):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            o.id AS offer_id,
            g.title,
            o.platform,
            o.format,
            o.condition,
            o.key_region,
            o.city,
            u.first_name,
            u.username,
            l.created_at
        FROM likes l
        JOIN offers o ON o.id = l.offer_id
        JOIN games g ON g.id = o.game_id
        JOIN users u ON u.id = o.user_id
        WHERE l.from_user_id = ?
        AND l.action = 'like'
        AND o.status = 'active'
        ORDER BY l.created_at DESC
        """,
        (user_id,)
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def add_deal_message(deal_id: int, sender_user_id: int, text: str):
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO deal_messages (
            deal_id,
            sender_user_id,
            text
        )
        VALUES (?, ?, ?)
        """,
        (
            deal_id,
            sender_user_id,
            text
        )
    )

    conn.commit()
    conn.close()


def get_deal_for_user(deal_id: int, user_id: int):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM deals
        WHERE id = ?
        AND status = 'active'
        AND (user1_id = ? OR user2_id = ?)
        LIMIT 1
        """,
        (
            deal_id,
            user_id,
            user_id
        )
    ).fetchone()

    conn.close()

    if not row:
        return None

    return dict(row)