import csv
import hashlib
import json
import os
import sys
from datetime import datetime
from functools import wraps

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from shared.student import VARIANT_NUMBER


class ValidationError(Exception):
    pass
minpass = 13
def generate_hash(password: str, salt: str) -> str:
    if not password or not salt:
        raise ValueError("Password or salt cannot be empty")
    if len(password) < minpass:
        raise ValidationError("Password too short")
    return hashlib.sha224((password + salt).encode()).hexdigest()

salt = str(VARIANT_NUMBER).zfill(5)

users_to_register = [
    ("alice", "SecurePass123!"),
    ("bob", "AnotherStrongPass456@"),
    ("charlie", "MyPassword789#"),
    ("david", "UltraSafePass0001$"),
    ("eva", "ComplexPass2026%"),
    ("frank", "CryptoPass9999&"),
    ("grace", "HashingPass7777*"),
    ("henry", "LongPassword8888("),
    ("irene", "StrongestPass5555)"),
    ("jack", "MegaSecurePass4444^")
]

def create_user(username, password):
    return (username, generate_hash(password, salt))

def create_users(users_list):
    os.makedirs("data", exist_ok=True)
    errors = []
    try:
        with open("data/users.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for u, p in users_list:
                try:
                    writer.writerow(create_user(u, p))
                except (ValidationError, ValueError) as e:
                    errors.append(f"{u}: {e}")
    except PermissionError as e:
        errors.append(f"PermissionError while creating file: {e}")
    except OSError as e:
        errors.append(f"IOError while writing file: {e}")

    # друга перевірка
    try:
        if not os.path.exists("data/users.csv"):
            raise FileNotFoundError("users.csv not created")
    except FileNotFoundError as e:
        errors.append(f"FileNotFoundError after creation: {e}")
    except PermissionError as e:
        errors.append(f"PermissionError after creation: {e}")
    except OSError as e:
        errors.append(f"IOError after creation: {e}")

    if errors:
        print("\n❌ Registration errors:")
        for err in errors:
            print(f" - {err}")

def read_users():
    users_db = []
    errors = []
    try:
        with open("data/users.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                users_db.append((row[0], row[1]))
    except FileNotFoundError as e:
        errors.append(f"FileNotFoundError while reading: {e}")
    except PermissionError as e:
        errors.append(f"PermissionError while reading: {e}")
    except OSError as e:
        errors.append(f"IOError while reading: {e}")

    # друга перевірка
    try:
        if not users_db:
            raise FileNotFoundError("users.csv is empty or unreadable")
    except FileNotFoundError as e:
        errors.append(f"FileNotFoundError after read: {e}")
    except PermissionError as e:
        errors.append(f"PermissionError after read: {e}")
    except OSError as e:
        errors.append(f"IOError after read: {e}")

    if errors:
        print("\n❌ Read errors:")
        for err in errors:
            print(f" - {err}")

    return users_db

def log_event(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            result = f"user={args[0]} -> DENY (Registration error: {e})"
        event = {
            "event": "login",
            "user": args[0],
            "result": "success" if "ALLOW" in str(result) else "failure",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "args": args,
            "kwargs": kwargs
        }
        try:
            with open("data/log.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError as e:
            print(f"Logging error: {e}")
        return result
    return wrapper

@log_event
def login(username: str, password: str) -> str:
    if not username or not password:
        return f"user={username} -> DENY (Empty credentials)"
    users_db = read_users()
    for u, h in users_db:
        try:
            if u == username and h == generate_hash(password, salt):
                return f"user={username} -> ALLOW"
        except ValidationError as e:
            return f"user={username} -> DENY (Registration error: {e})"
        except ValueError as e:
            return f"user={username} -> DENY (Registration error: {e})"
    return f"user={username} -> DENY (Invalid login)"

def main():
    create_users(users_to_register)
    users_db = read_users()
    print("\n📋 Users DB:")
    for u, h in users_db:
        print(f"{u:<10} | {h}")
    print("\n🔐 Login attempts:")
    print(login("alice", "SecurePass123!"))   # успіх
    print(login("bob", "WrongPass"))          # неправильний пароль
    print(login("ghost", "NoPass"))           # користувач не існує
    print(login("charlie", "short"))          # занадто короткий пароль

if __name__ == "__main__":
    main()
