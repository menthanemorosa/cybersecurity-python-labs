import subprocess
import sys
from pathlib import Path

# Отримуємо шлях до папки, де лежить main.py
BASE_DIR = Path(__file__).parent

tasks = ["task1.py", "task2.py", "task3.py"]

for task in tasks:
    task_path = BASE_DIR / task

    print(f"\n{'=' * 20} RUNNING {task} {'=' * 20}\n")

    # Запуск скрипта через поточний інтерпретатор Python
    subprocess.run([sys.executable, str(task_path)])