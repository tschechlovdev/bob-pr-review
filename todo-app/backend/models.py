import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "todos.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT    NOT NULL,
                completed  INTEGER NOT NULL DEFAULT 0,
                status     TEXT    NOT NULL DEFAULT 'todo',
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        
        # Migration: check if 'status' column exists in 'todos' table
        cursor = conn.execute("PRAGMA table_info(todos)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "status" not in columns:
            conn.execute("ALTER TABLE todos ADD COLUMN status TEXT NOT NULL DEFAULT 'todo'")
            conn.execute("UPDATE todos SET status = 'done' WHERE completed = 1")
            conn.execute("UPDATE todos SET status = 'todo' WHERE completed = 0")
        
        conn.commit()
