"""Step 4 - Load the clean data into a SQLite database.

SQLite stores the whole database in one file (data/ttc_delays.db) and ships with
Python, so there is no server to install.
"""
import sqlite3

from . import config

SCHEMA_FILE = config.SQL_DIR / "schema.sql"


def load_to_sqlite(clean_df, codes, db_path=config.DB_PATH):
    """Recreate the tables and insert all rows. Returns the number of delay rows loaded."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        load_into_connection(conn, clean_df, codes)
        return conn.execute("SELECT COUNT(*) FROM delays").fetchone()[0]


def load_into_connection(conn, clean_df, codes):
    """Create the schema and insert rows using an open connection (also used by the tests)."""
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    # Insert into the tables defined in schema.sql, so the CHECK constraints are enforced.
    clean_df.to_sql("delays", conn, if_exists="append", index=False)
    conn.executemany("INSERT INTO delay_codes (code, description) VALUES (?, ?)", sorted(codes.items()))
    conn.commit()
