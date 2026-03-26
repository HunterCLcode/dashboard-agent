import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "dashboard-agent-etl" / "data" / "olist.db"


def query(sql: str, params: tuple = ()) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
