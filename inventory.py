import csv
import io
import re
import sqlite3
from contextlib import closing
from pathlib import Path


MAX_UPLOAD = 64 * 1024
MAX_ROWS = 200
HEADERS = ["sku", "name", "quantity"]


def review_csv(source: str) -> tuple[list[tuple], list[str]]:
    if len(source.encode("utf-8")) > MAX_UPLOAD:
        raise ValueError("The CSV must be 64 KiB or smaller.")

    reader = csv.reader(io.StringIO(source, newline=""), strict=True)
    items = []
    errors = []
    seen = set()
    try:
        header = next(reader, [])
        if header != HEADERS:
            raise ValueError("Use the header sku,name,quantity.")
        for number, row in enumerate(reader, start=2):
            if number > MAX_ROWS + 1:
                raise ValueError("Use at most 200 data rows.")
            if len(row) != 3:
                errors.append(f"Row {number}: expected three columns.")
                continue
            sku, name, quantity = (value.strip() for value in row)
            sku = sku.upper()
            if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{0,39}", sku):
                errors.append(f"Row {number}: invalid SKU.")
            elif not name or len(name) > 100:
                errors.append(f"Row {number}: name must contain 1–100 characters.")
            elif not re.fullmatch(r"[0-9]{1,6}", quantity):
                errors.append(f"Row {number}: quantity must be an integer from 0 to 999999.")
            elif sku in seen:
                errors.append(f"Row {number}: duplicate SKU in this file.")
            else:
                items.append((sku, name, int(quantity)))
                seen.add(sku)
    except csv.Error as error:
        raise ValueError("Invalid CSV formatting.") from error
    return items, errors


def initialize(database: Path) -> None:
    with closing(sqlite3.connect(database)) as db, db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                sku TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity BETWEEN 0 AND 999999)
            )
        """)


def save_items(database: Path, items: list[tuple]) -> int:
    with closing(sqlite3.connect(database)) as db, db:
        return db.executemany(
            "INSERT INTO inventory VALUES (?, ?, ?) ON CONFLICT(sku) DO NOTHING", items
        ).rowcount


def list_items(database: Path) -> list[tuple]:
    with closing(sqlite3.connect(database)) as db:
        return db.execute("SELECT sku, name, quantity FROM inventory ORDER BY sku").fetchall()
