import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tasks.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done  INTEGER NOT NULL DEFAULT 0
            );
            """
        )

        row = conn.execute("SELECT COUNT(*) AS n FROM tasks;").fetchone()
        if row["n"] == 0:
            conn.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?);",
                [
                    ("Buy milk", 0),
                    ("Write README", 0),
                    ("Ship the API", 0),
                ],
            )
        conn.commit()
    finally:
        conn.close()
