import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "phimed.db")
SQL_PATH = os.path.join(BASE_DIR, "seed.sql")

def initialize_database(force=False):
    if os.path.exists(DB_PATH) and not force:
        print(f"Database already exists at {DB_PATH}")
        return

    if force and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    print(f"Initializing SQLite database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    with open(SQL_PATH, "r", encoding="utf-8") as f:
        sql_script = f.read()

    conn.executescript(sql_script)
    conn.commit()
    conn.close()
    print("Database successfully initialized!")

if __name__ == "__main__":
    initialize_database(force=True)
