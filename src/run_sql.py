"""Load the synthetic CSV into SQLite and execute the portfolio SQL files."""

from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def run() -> None:
    df = pd.read_csv(ROOT / "data" / "experiment_users.csv")
    with sqlite3.connect(":memory:") as connection:
        df.to_sql("experiment_users", connection, index=False)
        for path in sorted((ROOT / "sql").glob("*.sql")):
            print(f"\n{path.name}")
            script = "\n".join(line for line in path.read_text().splitlines()
                               if not line.lstrip().startswith("--"))
            for statement in script.split(";"):
                if statement.strip():
                    result = pd.read_sql_query(statement, connection)
                    print(result.to_string(index=False, max_rows=5))


if __name__ == "__main__":
    run()
