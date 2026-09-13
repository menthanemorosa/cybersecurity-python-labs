import os
import csv
import json
import hashlib
import sys
from datetime import datetime
from functools import wraps
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from shared.student import VARIANT_NUMBER

class ValidationError(Exception):
    pass

def generate_hash(password: str, salt: str) -> str:
    if not password or not salt:
        raise ValueError("Password or salt cannot be empty")
    if len(password) < 13:
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
    os.makedirs("labs/lab01/data", exist_ok=True)
    try:
        with open("labs/lab01/data/users.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for u, p in users_list:
                try:
                    writer.writerow(create_user(u, p))
                except (ValidationError, ValueError) as e:
                    print(f"Error creating user {u}: {e}")
    except (PermissionError, IOError) as e:
        print(f"File error: {e}")

def read_users():
    users_db = []
    try:
        with open("labs/lab01/data/users.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                users_db.append((row[0], row[1]))
    except FileNotFoundError:
        print("Database not found")
    return users_db

def log_event(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            result = False
            print(f"Login error: {e}")
        event = {
            "event": "login",
            "user": args[0],
            "result": "success" if result else "failure",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "args": args,
            "kwargs": kwargs
        }
        try:
            with open("labs/lab01/data/log.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except IOError as e:
            print(f"Logging error: {e}")
        return result
    return wrapper

@log_event
def login(username: str, password: str) -> bool:
    if not username or not password:
        raise ValueError("Username or password cannot be empty")
    users_db = read_users()
    for u, h in users_db:
        if u == username and h == generate_hash(password, salt):
            return True
    return False

def main():
    create_users(users_to_register)
    users_db = read_users()
    print("📋 Users DB:")
    for u, h in users_db:
        print(f"{u:<10} | {h}")
    print("\n🔐 Login attempts:")
    print(login("alice", "SecurePass123!"))
    print(login("bob", "WrongPass"))
    print(login("ghost", "NoPass"))

if __name__ == "__main__":
    main()
