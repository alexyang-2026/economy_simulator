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