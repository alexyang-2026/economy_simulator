import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "playerdata.db"
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"

def initialize_database():
    """
    Initialize the SQLite database and create the required tables if they do not exist already.
    """

    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        schema = file.read()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(schema)
    conn.commit()
    conn.close()


def connect_db():
    """
    Open a SQLite connection with foreign-key enforcement enabled.
    Returns a sqlite3.Connection (an active database connection).
    """

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def save_market_state(conn, item_id, current_price, current_state):
    conn.execute(
        """
        INSERT INTO market_state (item_id, current_price, current_state)
        VALUES (?, ?, ?)
        ON CONFLICT (item_id)
        DO UPDATE SET
            current_price = excluded.current_price,
            current_state = excluded.current_state
        """,
        (item_id, current_price, current_state)
    )


def get_market_state(conn):
    cursor = conn.execute(
        "SELECT item_id, current_price, current_state FROM market_state"
    )

    return {
        item_id: {
            "price": price,
            "state": state
        }
        for item_id, price, state in cursor.fetchall()
    }


def advance_game_day(conn):
    conn.execute("""
        UPDATE simulation_state
        SET current_day = current_day + 1
        WHERE id = 1
    """)

def get_current_day(conn):
    return conn.execute(
        "SELECT current_day FROM simulation_state WHERE id = 1"
    ).fetchone()[0]