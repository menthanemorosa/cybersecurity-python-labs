import os
import random
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

passwords = [
    "Digital@F0r3nsics", "plain", "Encrypt10n@Key", "member",
    "Security@Audit2023", "regular", "Hack3r@D3fense", "ordinary",
    "Threat@Intel", "usual"
]

criteria = {
    "min_length": 8,
    "require_digits": True,
    "require_upper": True,
    "require_special": True
}

forbidden_passwords = {"plain", "member", "regular", "ordinary", "usual", "user"}

indices = random.sample(range(len(passwords)), 3)
for i in indices:
    passwords.append(passwords[i])

def evaluate_password(pw: str) -> str:
    has_digit = any(ch.isdigit() for ch in pw)
    has_upper = any(ch.isupper() for ch in pw)
    has_lower = any(ch.islower() for ch in pw)
    has_special = any(not ch.isalnum() for ch in pw)
    min_length = criteria["min_length"]

    if pw in forbidden_passwords or len(pw) < min_length:
        return "Заборонений"

    criteria_count = sum([has_digit, has_upper, has_lower, has_special])

    if criteria_count == 0:
        return "Слабкий"
    elif criteria_count < 4:
        return "Середній"
    elif criteria_count == 4 and len(pw) < min_length + 4:
        return "Сильний"
    elif criteria_count == 4 and len(pw) >= min_length + 4 and passwords.count(pw) == 1:
        return "Дуже сильний"

    return "Слабкий"

print(f"Студент: {STUDENT_NAME}, Група: {GROUP_NAME}, Варіант: {VARIANT_NUMBER}")
print("-" * 60)
print(f"{'Пароль':<20} | {'Оцінка':<15}")
print("-" * 60)

for pw in passwords:
    print(f"{pw:<20} | {evaluate_password(pw):<15}")
    
