from ..database import get_db_connection


def save_prediction(
    user_id: int,
    disease: str,
    prediction: int,
    result: str,
    probability: float,
    input_data: str,
    explanation: str,
    model_name: str,
    model_version: str,
):
    connection = get_db_connection()

    try:
        connection.execute(
            """
            INSERT INTO predictions
            (
                user_id,
                disease,
                prediction,
                result,
                probability,
                input_data,
                explanation,
                model_name,
                model_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                disease,
                prediction,
                result,
                probability,
                input_data,
                explanation,
                model_name,
                model_version,
            )
        )

        connection.commit()

    finally:
        connection.close()


def get_user_history(user_id: int):
    connection = get_db_connection()

    try:
        return connection.execute(
            """
            SELECT
                id,
                disease,
                prediction,
                result,
                probability,
                created_at
            FROM predictions
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()

    finally:
        connection.close()


def get_prediction_by_id(prediction_id: int, user_id: int):
    connection = get_db_connection()

    try:
        return connection.execute(
            """
            SELECT
                id,
                disease,
                prediction,
                result,
                probability,
                input_data,
                explanation,
                model_name,
                model_version,
                created_at
            FROM predictions
            WHERE id = ? AND user_id = ?
            """,
            (prediction_id, user_id)
        ).fetchone()

    finally:
        connection.close()