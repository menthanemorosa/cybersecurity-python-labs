"""Модуль реалізації класів користувача, сесії та аудиту (Завдання 1)."""

import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone

PBKDF2_ITERATIONS = 100_000
SESSION_TIMEOUT_SEC = 900


class User:
    """Клас для представлення користувача системи."""

    def __init__(self, username: str, email: str, role: str = "user") -> None:
        self.username = username
        self.email = email  # Викликає setter з валідацією
        self.role = role
        self.active: bool = True
        self.__password_hash: bytes = b""
        self.__password_salt: bytes = b""

    @property
    def email(self) -> str:
        """Геттер для email."""
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        """Сеттер email з перевіркою формату за допомогою regex."""
        pattern = r"^[a-zA-Z][a-zA-Z0-9._-]{2,63}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, value):
            raise ValueError(f"Некоректний email-адрес: {value}")
        self._email = value

    def set_password(self, password: str) -> None:
        """Хешування пароля із використанням PBKDF2-HMAC-SHA256 та криптографічної солі."""
        if not password:
            raise ValueError("Пароль не може бути порожнім.")
        self.__password_salt = os.urandom(16)
        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )

    def check_password(self, password: str) -> bool:
        """Бепечна перевірка пароля з захистом від атак за часом (Timing Attacks)."""
        if not self.__password_hash or not self.__password_salt:
            return False
        computed_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )
        return hmac.compare_digest(self.__password_hash, computed_hash)

    def deactivate(self) -> None:
        """Деактивація користувача."""
        self.active = False

    def __str__(self) -> str:
        status = "Active" if self.active else "Inactive"
        return f"User({self.username}, Email: {self.email}, Role: {self.role}, Status: {status})"


class Admin(User):
    """Адміністратор системи (успадковує User, реалізує permissions)."""

    def __init__(self, username: str, email: str, permissions: set[str] | None = None) -> None:
        super().__init__(username, email, role="admin")
        self.permissions: set[str] = set(permissions) if permissions else set()

    def grant_permission(self, permission: str) -> None:
        """Надання привиду."""
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        """Вилучення привілею."""
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        """Перевірка наявності привілею."""
        return permission in self.permissions

    def __str__(self) -> str:
        base_str = super().__str__()
        perms = ", ".join(sorted(self.permissions)) if self.permissions else "None"
        return f"{base_str} [Permissions: {perms}]"


class Session:
    """Клас моніторингу та управління сесією користувача."""

    def __init__(self, ip: str) -> None:
        self.ip = ip
        now = datetime.now(timezone.utc)
        self.login_time: datetime = now
        self.last_activity: datetime = now

    def touch(self) -> None:
        """Оновлення часу останньої активності."""
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        """Перевірка дійсності сесії за таймаутом."""
        if timeout_sec <= 0:
            raise ValueError("Таймаут повинен бути додатним числом.")
        now = datetime.now(timezone.utc)
        elapsed = (now - self.last_activity).total_seconds()
        return elapsed < timeout_sec


@dataclass
class AuditEntry:
    """Запис аудиту системних подій."""

    timestamp: datetime
    username: str
    action: str


class AuditLog:
    """Журнал аудиту для збереження історій дій користувачів."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def add_log(self, username: str, action: str) -> None:
        """Додавання нового запису в аудит."""
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            username=username,
            action=action,
        )
        self.entries.append(entry)

    def show_all(self) -> list[str]:
        """Отримання всіх записів у текстовому вигляді."""
        res = []
        for e in self.entries:
            ts_str = e.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
            res.append(f"[{ts_str}] User: {e.username} | Action: {e.action}")
        return res


class UserAccount:
    """Композитний клас, що об'єднує User, Session та AuditLog."""

    def __init__(self, user: User, audit_log: AuditLog | None = None) -> None:
        self.user = user
        self.session: Session | None = None
        self.audit_log = audit_log if audit_log is not None else AuditLog()

    def login(self, username: str, password: str, ip: str) -> bool:
        """Авторизація користувача з фіксацією результату в аудиті."""
        if not self.user.active:
            self.audit_log.add_log(username, "login_failure_inactive_account")
            return False

        if self.user.username == username and self.user.check_password(password):
            self.session = Session(ip)
            self.session.touch()
            self.audit_log.add_log(username, "login_success")
            return True

        self.audit_log.add_log(username, "login_failure")
        return False

    def is_authenticated(self) -> bool:
        """Перевірка чи існує активна сесія."""
        if self.session is None:
            return False
        if self.session.is_active(SESSION_TIMEOUT_SEC):
            return True
        return False

    def logout(self) -> None:
        """Завершення сеансу."""
        if self.session:
            self.audit_log.add_log(self.user.username, "logout")
            self.session = None

    def __getitem__(self, item: str):
        allowed_fields = {
            "user": self.user,
            "session": self.session,
            "audit_log": self.audit_log,
        }
        if item in allowed_fields:
            return allowed_fields[item]
        raise KeyError(f"Неприпустимий ключ доступу: {item}")

    def __setitem__(self, key: str, value) -> None:
        if key == "user":
            if not isinstance(value, User):
                raise TypeError("Значення повинно бути об'єктом класу User")
            self.user = value
        elif key == "session":
            if value is not None and not isinstance(value, Session):
                raise TypeError("Значення повинно бути об'єктом класу Session")
            self.session = value
        elif key == "audit_log":
            if not isinstance(value, AuditLog):
                raise TypeError("Значення повинно бути об'єктом класу AuditLog")
            self.audit_log = value
        else:
            raise KeyError(f"Неприпустимий ключ доступу для запису: {key}")


def run_demo() -> None:
    """Сценарій демонстрації функціоналу Завдання 1."""
    print("=" * 60)
    print("      ДЕМОНСТРАЦІЯ ЗАВДАННЯ 1 (ООП, Сесії, Валідація)")
    print("=" * 60)

    # 1. Створення користувачів
    user1 = User("j_smith", "j.smith@corp.com")
    user1.set_password("SecureP@ss123")

    admin1 = Admin("admin_alex", "alex.admin@corp.com")
    admin1.set_password("SuperSecret2026!")
    admin1.grant_permission("READ_LOGS")
    admin1.grant_permission("DELETE_USER")

    audit = AuditLog()
    account1 = UserAccount(user1, audit)

    print(f"[+] Створено користувача: {user1}")
    print(f"[+] Створено адміністратора: {admin1}")
    print(f"    Перевірка прав Admin: HAS 'READ_LOGS' -> {admin1.has_permission('READ_LOGS')}")

    # 2. Невдалий вхід
    print("\n[>] Спроба входу з невірним паролем...")
    res_fail = account1.login("j_smith", "WrongPassword", "192.168.1.50")
    print(f"    Результат входу: {res_fail} | Authenticated: {account1.is_authenticated()}")

    # 3. Успішний вхід
    print("\n[>] Спроба входу з вірним паролем...")
    res_success = account1.login("j_smith", "SecureP@ss123", "192.168.1.50")
    print(f"    Результат входу: {res_success} | Authenticated: {account1.is_authenticated()}")

    # 4. Перевірка валідації email через property
    print("\n[>] Валідація Email адреси:")
    try:
        user1.email = "valid.user_123@sub.domain.com"
        print(f"    [OK] Оновлено email: {user1.email}")
        print("    [!] Спроба встановити некоректний email 'bad_email@'...")
        user1.email = "bad_email@"
    except ValueError as e:
        print(f"    [CATCH] Перехоплено помилку валідації: {e}")

    # 5. Вихід з системи
    print("\n[>] Завершення сеансу (Logout)...")
    account1.logout()
    print(f"    Authenticated після logout: {account1.is_authenticated()}")

    # 6. Доступ через __getitem__
    print("\n[>] Перевірка спеціального методу __getitem__:")
    print(f"    account['user'] -> {account1['user']}")

    # 7. Друк Журналу аудиту
    print("\n=== Журнал подій безпеки (AuditLog) ===")
    for log_line in audit.show_all():
        print(f"  {log_line}")
    print("=" * 60)