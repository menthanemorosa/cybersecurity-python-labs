"""Головний модуль запуску утиліт Лабораторної роботи №2."""

import argparse
import sys
from pathlib import Path

from labs.lab02.task1 import run_demo
from labs.lab02.task2 import run_analyzer


def main() -> None:
    """Розбір аргументів командного рядка та маршрутизація викликів."""
    parser = argparse.ArgumentParser(
        description="Лабораторна робота №2: CLI утиліти кібербезпеки (Варіант 9)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Доступні команди")

    # Підкоманда demo
    subparsers.add_parser("demo", help="Запустити демонстрацію Завдання 1 (ООП, Сесії)")

    # Підкоманда analyze
    analyze_parser = subparsers.add_parser("analyze", help="Запустити аудит HTTP-заголовків (Завдання 2)")
    analyze_parser.add_argument(
        "--headers-file",
        type=Path,
        default=Path("labs/lab02/data/http_headers.json"),
        help="Шлях до JSON-файлу з дампами HTTP-заголовків",
    )
    analyze_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("labs/lab02/data/headers_audit.csv"),
        help="Шлях для збереження результату аудиту (.csv або .json)",
    )
    analyze_parser.add_argument(
        "--strict",
        action="store_true",
        help="Увімкнути суворий режим перевірки",
    )
    analyze_parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Рівень логування (default: INFO)",
    )

    args = parser.parse_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "analyze":
        run_analyzer(
            headers_file=args.headers_file,
            output_path=args.output,
            strict=args.strict,
            log_level=args.log_level,
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()