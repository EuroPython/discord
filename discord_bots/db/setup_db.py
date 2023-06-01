import sqlite3

DB_PATH = "db/registration_bot.db"


def setup_db():
    con = sqlite3.connect(DB_PATH)

    cur = con.cursor()

    # create registration table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS registration (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        ticket_id TEXT NOT NULL,
        name TEXT,
        valid INTEGER,
        is_speaker INTEGER,
        comment TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )


if __name__ == "__main__":
    setup_db()
