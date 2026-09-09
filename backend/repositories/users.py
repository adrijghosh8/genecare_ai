from ..database import get_db_connection


def get_user_by_email(email: str):
    connection = get_db_connection()

    try:
        return connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()
    finally:
        connection.close()


def get_user_by_id(user_id: int):
    connection = get_db_connection()

    try:
        return connection.execute(
            """
            SELECT id, name, email, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()
    finally:
        connection.close()


def create_user(name: str, email: str, password_hash: str):
    connection = get_db_connection()

    try:
        connection.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (name, email, password_hash)
        )

        connection.commit()
    finally:
        connection.close()


def email_exists_for_other_user(email: str, user_id: int):
    connection = get_db_connection()

    try:
        return connection.execute(
            """
            SELECT id
            FROM users
            WHERE email = ? AND id != ?
            """,
            (email, user_id)
        ).fetchone()
    finally:
        connection.close()


def update_user(user_id: int, name: str, email: str):
    connection = get_db_connection()

    try:
        connection.execute(
            """
            UPDATE users
            SET name = ?, email = ?
            WHERE id = ?
            """,
            (name, email, user_id)
        )

        connection.commit()

        return connection.execute(
            """
            SELECT id, name, email, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

    finally:
        connection.close()


def update_password(user_id: int, password_hash: str):
    connection = get_db_connection()

    try:
        connection.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (password_hash, user_id)
        )

        connection.commit()

    finally:
        connection.close()

def get_user_by_id_with_password(user_id: int):
    connection = get_db_connection()

    try:
        return connection.execute(
            """
            SELECT password_hash
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

    finally:
        connection.close()