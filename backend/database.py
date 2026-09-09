import sqlite3
from pathlib import Path

DATABASE_NAME = Path(__file__).parent / "genecare.db"



def get_db_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection

def create_tables():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            disease TEXT NOT NULL,
            prediction INTEGER NOT NULL,
            result TEXT NOT NULL,
            probability REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()

def migrate_predictions_table():
    connection = get_db_connection()

    try:
        columns = connection.execute(
            "PRAGMA table_info(predictions)"
        ).fetchall()

        existing_columns = {
            column["name"]
            for column in columns
        }

        new_columns = {
            "input_data": "TEXT",
            "explanation": "TEXT",
            "model_name": "TEXT",
            "model_version": "TEXT"
        }

        for column_name, column_type in new_columns.items():

            if column_name not in existing_columns:

                connection.execute(
                    f"""
                    ALTER TABLE predictions
                    ADD COLUMN {column_name} {column_type}
                    """
                )

        connection.commit()

    finally:
        connection.close()

create_tables()
migrate_predictions_table()