import json
import sqlite3
from contextlib import closing
from labs.lab03.database import get_connection, BASE_DIR

SEED_PATH = BASE_DIR / "data" / "seed.json"

def seed_data():
    try:
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Помилка: Файл seed.json не знайдено.")
        return

    categories = [(c["id"], c["name"]) for c in data.get("categories", [])]
    records = [(r["code"], r["title"], r["category_id"], r["value"], r["status"])
               for r in data.get("records", [])]

    with closing(get_connection()) as connection:
        try:
            # Контекстний менеджер автоматично підтверджує (commit) або скасовує (rollback) транзакцію
            with connection:
                connection.executemany(
                    "INSERT INTO categories (id, name) VALUES (?, ?)",
                    categories
                )
                connection.executemany(
                    "INSERT INTO records (code, title, category_id, value, status) VALUES (?, ?, ?, ?, ?)",
                    records
                )
            print("Базу даних успішно заповнено.")
        except sqlite3.IntegrityError as e:
            # connection.rollback() вже виконано автоматично
            print(f"Зміни скасовано. Помилка унікальності або обмежень: {e}")
        except sqlite3.Error as e:
            print(f"Технічна помилка бази даних: {e}")

if __name__ == "__main__":
    seed_data()