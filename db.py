"""
Gunluk kalori gecmisi icin basit SQLite katmani.
Her hesaplanan ogun (kisi basi degerleriyle) meals tablosuna kaydedilir.
db_path parametre olarak verilebildigi icin testlerde gercek dosyaya
dokunmadan gecici bir veritabani kullanilabilir.
"""

import sqlite3
from datetime import date, datetime

DB_PATH = "kalori_bot.db"


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    conn = get_connection(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            calories REAL NOT NULL,
            protein_g REAL NOT NULL,
            carbs_g REAL NOT NULL,
            fat_g REAL NOT NULL,
            portion_count INTEGER
        )
        """
    )
    conn.commit()
    conn.close()


def log_meal(user_id: int, totals: dict, portion_count: int | None = None, db_path: str = DB_PATH) -> None:
    """Bir ogunu (kisi basi degerleriyle) veritabanina kaydeder."""
    conn = get_connection(db_path)
    conn.execute(
        """
        INSERT INTO meals (user_id, created_at, calories, protein_g, carbs_g, fat_g, portion_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            datetime.now().isoformat(),
            totals["calories"],
            totals["protein_g"],
            totals["carbs_g"],
            totals["fat_g"],
            portion_count,
        ),
    )
    conn.commit()
    conn.close()


def get_today_totals(user_id: int, db_path: str = DB_PATH) -> tuple[dict, int]:
    """Bugun icin kullanicinin toplam kalori/makro degerlerini ve kayit sayisini dondurur."""
    today_prefix = date.today().isoformat()  # "2026-08-09"
    conn = get_connection(db_path)
    rows = conn.execute(
        """
        SELECT calories, protein_g, carbs_g, fat_g FROM meals
        WHERE user_id = ? AND created_at LIKE ?
        """,
        (user_id, f"{today_prefix}%"),
    ).fetchall()
    conn.close()

    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    for row in rows:
        totals["calories"] += row["calories"]
        totals["protein_g"] += row["protein_g"]
        totals["carbs_g"] += row["carbs_g"]
        totals["fat_g"] += row["fat_g"]

    return {key: round(value, 1) for key, value in totals.items()}, len(rows)
