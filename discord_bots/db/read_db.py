import sys

import pandas as pd
import sqlite3

DB_PATH = "db/registration_bot.db"


def print_db(csv=False):
    con = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query("SELECT * FROM registration", con)
    print(df)
    if csv:
        df.to_csv("db/registration.csv")


if __name__ == "__main__":
    csv = False
    if len(sys.argv) > 1:
        option = sys.argv[1]
        print(option)
        if option == "csv":
            csv = True

    print_db(csv)
