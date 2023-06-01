import sqlite3

DB_PATH = "db/registration_bot.db"


def reset_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # drop registration table
    cur.execute(
        """
        DROP TABLE IF EXISTS registration;
        """
    )


if __name__ == "__main__":
    reset_db()
