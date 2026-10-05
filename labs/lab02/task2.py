"""Аудитор безпеки HTTP-заголовків відповідей (Варіант 9)."""

import csv
import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path

# Критичні заголовки безпеки
REQUIRED_SECURITY_HEADERS = {
    "Strict-Transport-Security": 25,
    "Content-Security-Policy": 25,
    "X-Frame-Options": 15,
    "X-Content-Type-Options": 15,
}

# Регулярні вирази для виявлення версій ПЗ (software version leak)
VERSION_REGEX = re.compile(r"\b(\d+\.\d+(?:\.\d+)?)\b")


@dataclass
class HeaderAuditResult:
    """Результат аудиту заголовків для одного ресурсу."""

    url: str
    security_score: int
    grade: str
    status: str
    missing_headers: list[str]
    leaks: list[str]


def evaluate_score(score: int) -> tuple[str, str]:
    """Визначення оцінки та статусу за підсумковим балом."""
    if score >= 85:
        return "PASS", "A+" if score >= 95 else "A"
    if score >= 60:
        return "WARN", "B" if score >= 70 else "C"
    return "FAIL", "F"


def audit_http_headers(
    headers_file: Path,
    strict_mode: bool = False,
) -> tuple[list[HeaderAuditResult], list[str]]:
    """Основна функція розбору та аудиту HTTP заголовків з JSON-файлу."""
    if not headers_file.exists():
        raise FileNotFoundError(f"Файл із заголовками не знайдено: {headers_file}")

    with headers_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    results: list[HeaderAuditResult] = []
    leak_alerts: list[str] = []

    for item in data:
        url = item.get("url", "Unknown Resource")
        headers = {k.lower(): v for k, v in item.get("headers", {}).items()}

        score = 100
        missing: list[str] = []
        leaks: list[str] = []

        # 1. Перевірка наявності критичних заголовків безпеки
        for req_header, weight in REQUIRED_SECURITY_HEADERS.items():
            if req_header.lower() not in headers:
                missing.append(req_header)
                score -= weight

        # 2. Перевірка витоку версій ПЗ у Server та X-Powered-By
        server_val = headers.get("server", "")
        if server_val:
            match = VERSION_REGEX.search(server_val)
            if match or strict_mode:
                msg = f"[LEAK] {url} leaks version in 'Server': {server_val}"
                leaks.append(f"Server: {server_val}")
                leak_alerts.append(msg)
                score -= 10

        x_powered = headers.get("x-powered-by", "")
        if x_powered:
            msg = f"[LEAK] {url} leaks tech stack in 'X-Powered-By': {x_powered}"
            leaks.append(f"X-Powered-By: {x_powered}")
            leak_alerts.append(msg)
            score -= 10

        score = max(0, score)
        status, grade = evaluate_score(score)

        results.append(
            HeaderAuditResult(
                url=url,
                security_score=score,
                grade=grade,
                status=status,
                missing_headers=missing,
                leaks=leaks,
            )
        )

    return results, leak_alerts


def print_formatted_report(results: list[HeaderAuditResult], leak_alerts: list[str]) -> None:
    """Виведення гарно відформатованого консольного звіту."""
    print("\n" + "=" * 80)
    print(f"{'Target Resource':<35} {'Security Score':<18} {'Status':<8} {'Missing Security Headers'}")
    print("-" * 80)

    for r in results:
        missing_str = ", ".join(r.missing_headers) if r.missing_headers else "None"
        score_str = f"{r.security_score}/100 ({r.grade})"
        print(f"{r.url:<35} {score_str:<18} {r.status:<8} {missing_str}")

    if leak_alerts:
        print("\n=== Server Software Leak Alerts ===")
        for alert in leak_alerts:
            print(alert)

    print("=" * 80 + "\n")


def export_report_csv(results: list[HeaderAuditResult], output_file: Path) -> None:
    """Збереження результатів у CSV-файл."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Security Score", "Grade", "Status", "Missing Headers", "Software Leaks"])
        for r in results:
            writer.writerow([
                r.url,
                r.security_score,
                r.grade,
                r.status,
                "; ".join(r.missing_headers),
                "; ".join(r.leaks),
            ])


def export_report_json(results: list[HeaderAuditResult], output_file: Path) -> None:
    """Збереження результатів у JSON-файл."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    data_to_save = [asdict(r) for r in results]
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(data_to_save, f, indent=2, ensure_ascii=False)


def run_analyzer(
    headers_file: Path,
    output_path: Path,
    strict: bool = False,
    log_level: str = "INFO",
) -> None:
    """Головний сценарій запуску CLI утиліти аналізу заголовків."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="[%(levelname)s] %(message)s")

    logging.info("Auditing HTTP response headers from %s...", headers_file)

    results, leak_alerts = audit_http_headers(headers_file, strict_mode=strict)
    print_formatted_report(results, leak_alerts)

    if output_path.suffix.lower() == ".json":
        export_report_json(results, output_path)
    else:
        export_report_csv(results, output_path)

    logging.info("Header audit report generated at %s", output_path)