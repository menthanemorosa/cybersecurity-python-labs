import sqlite3
from contextlib import closing
from typing import List, Optional
from labs.lab03.database import get_connection


# --- Операції з категоріями ---

def get_categories() -> List[dict]:
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT id, name FROM categories ORDER BY id").fetchall()
        return [dict(row) for row in rows]


def create_category(name: str) -> Optional[dict]:
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO categories (name) VALUES (?) RETURNING id, name",
                    (name,)
                )
                return dict(cursor.fetchone())
        except sqlite3.IntegrityError:
            return None


def delete_category(category_id: int) -> bool:
    with closing(get_connection()) as conn:
        try:
            with conn:
                cursor = conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
                return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            raise ValueError("Категорія містить записи")  # Перехоплюється в API як 409


# --- Операції із записами ---

def get_record(record_id: int) -> Optional[dict]:
    query = """
        SELECT r.*, c.name as category_name 
        FROM records r 
        JOIN categories c ON r.category_id = c.id 
        WHERE r.id = ?
    """
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(query, (record_id,)).fetchone()
        return dict(row) if row else None


def get_records(
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        min_value: Optional[float] = None,
        q: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
) -> List[dict]:
    query = """
        SELECT r.*, c.name as category_name 
        FROM records r 
        JOIN categories c ON r.category_id = c.id 
        WHERE 1=1
    """
    params = []

    if category_id is not None:
        query += " AND r.category_id = ?"
        params.append(category_id)
    if status is not None:
        query += " AND r.status = ?"
        params.append(status)
    if min_value is not None:
        query += " AND r.value >= ?"
        params.append(min_value)
    if q is not None:
        query += " AND instr(r.title, ?) > 0"
        params.append(q)

    query += " ORDER BY r.id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def create_record(data: dict) -> Optional[dict]:
    query = """
        INSERT INTO records (code, title, category_id, value, status) 
        VALUES (?, ?, ?, ?, ?) RETURNING id
    """
    with closing(get_connection()) as conn:
        try:
            with conn:
                cursor = conn.execute(query, (
                    data["code"], data["title"], data["category_id"],
                    data["value"], data["status"]
                ))
                record_id = cursor.fetchone()[0]
        except sqlite3.IntegrityError:
            return None
    return get_record(record_id)


def update_record(record_id: int, data: dict) -> Optional[dict]:
    query = """
        UPDATE records 
        SET code = ?, title = ?, category_id = ?, value = ?, status = ? 
        WHERE id = ?
    """
    with closing(get_connection()) as conn:
        try:
            with conn:
                cursor = conn.execute(query, (
                    data["code"], data["title"], data["category_id"],
                    data["value"], data["status"], record_id
                ))
                if cursor.rowcount == 0:
                    return None
        except sqlite3.IntegrityError:
            raise ValueError("Порушення унікальності або неіснуюча категорія")
    return get_record(record_id)


def delete_record(record_id: int) -> bool:
    with closing(get_connection()) as conn:
        with conn:
            cursor = conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
            return cursor.rowcount > 0


def bulk_create_records(records: List[dict]) -> Optional[List[dict]]:
    query = """
        INSERT INTO records (code, title, category_id, value, status) 
        VALUES (?, ?, ?, ?, ?)
    """
    values = [(r["code"], r["title"], r["category_id"], r["value"], r["status"]) for r in records]

    with closing(get_connection()) as conn:
        try:
            with conn:
                # Всі записи зберігаються в одній транзакції
                cursor = conn.executemany(query, values)
                # Отримання останніх доданих ID для повернення клієнту
                last_id = cursor.lastrowid
                first_id = last_id - len(records) + 1

            # Читаємо створені записи для відповіді
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT r.*, c.name as category_name FROM records r JOIN categories c ON r.category_id = c.id WHERE r.id BETWEEN ? AND ?",
                (first_id, last_id)
            ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.IntegrityError:
            # Транзакція скасовується автоматично
            return None