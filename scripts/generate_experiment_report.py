#!/usr/bin/env python
"""Автоматическая генерация отчёта об экспериментах в Markdown.

Этот скрипт читает результаты экспериментов из CSV/JSON файлов
и генерирует структурированный Markdown отчёт для документации.

Пример использования:
    uv run python scripts/generate_experiment_report.py

    # С кастомными путями
    uv run python scripts/generate_experiment_report.py \\
        --results reports/experiment_results.csv \\
        --output docs/experiments/results.md
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def load_results(results_path: Path) -> list[dict[str, Any]]:
    """Загрузить результаты экспериментов из CSV.

    Args:
        results_path: Путь к CSV файлу с результатами.

    Returns:
        Список словарей с результатами.
    """
    if HAS_PANDAS:
        df = pd.read_csv(results_path)
        result: list[dict[str, Any]] = df.to_dict("records")
        return result

    print("Warning: pandas not available, using basic CSV parsing")
    with open(results_path) as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_best_models(best_models_path: Path) -> dict[str, Any]:
    """Загрузить информацию о лучших моделях.

    Args:
        best_models_path: Путь к JSON файлу.

    Returns:
        Словарь с лучшими моделями по метрикам.
    """
    with open(best_models_path) as f:
        result: dict[str, Any] = json.load(f)
        return result


def generate_results_table(results: list[dict[str, Any]]) -> str:
    """Генерировать таблицу результатов в Markdown.

    Args:
        results: Список результатов экспериментов.

    Returns:
        Markdown таблица.
    """
    if not results:
        return "*Нет данных*"

    # Определить колонки
    columns = ["config_name", "model_type", "accuracy", "precision", "recall", "f1_score"]
    headers = ["Конфигурация", "Тип модели", "Accuracy", "Precision", "Recall", "F1-Score"]

    # Заголовок таблицы
    table = "| " + " | ".join(headers) + " |\n"
    table += "|" + "|".join(["---"] * len(headers)) + "|\n"

    # Сортировка по accuracy
    sorted_results = sorted(
        results,
        key=lambda x: float(x.get("metric_accuracy", x.get("accuracy", 0))),
        reverse=True,
    )

    # Строки таблицы
    for row in sorted_results[:10]:  # Топ-10
        values = []
        for col in columns:
            # Поддержка разных форматов имён колонок
            value = row.get(col) or row.get(f"metric_{col}") or row.get(f"param_{col}", "—")
            if isinstance(value, float):
                value = f"{value:.4f}"
            values.append(str(value))
        table += "| " + " | ".join(values) + " |\n"

    return table


def generate_report(
    results: list[dict[str, Any]],
    best_models: dict[str, Any] | None = None,
    figures_dir: str = "../assets/figures",
) -> str:
    """Генерировать полный Markdown отчёт.

    Args:
        results: Список результатов экспериментов.
        best_models: Словарь с лучшими моделями (опционально).
        figures_dir: Относительный путь к директории с графиками.

    Returns:
        Полный Markdown отчёт.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    report = f"""# Результаты экспериментов

*Автоматически сгенерировано: {now}*

## Обзор

Всего экспериментов: **{len(results)}**

---

## Топ-10 моделей по Accuracy

{generate_results_table(results)}

---

## Визуализации

### Сравнение метрик

![Metrics Comparison]({figures_dir}/metrics_comparison.png)

### Корреляция метрик

![Metrics Heatmap]({figures_dir}/metrics_heatmap.png)

### Время обучения

![Training Time]({figures_dir}/training_time_comparison.png)

---

"""

    if best_models:
        report += """## Лучшие модели по метрикам

| Метрика | Модель | Значение |
|---------|--------|----------|
"""
        for metric, info in best_models.items():
            if isinstance(info, dict):
                name = info.get("config_name", "—")
                value = info.get("value", 0)
                report += f"| {metric} | {name} | {value:.4f} |\n"

    report += """
---

## Воспроизведение

```bash
# Запуск всех экспериментов
uv run python -m src.experiments.run_experiments --models all

# Генерация этого отчёта
uv run python scripts/generate_experiment_report.py
```
"""

    return report


def main() -> None:
    """Главная функция скрипта."""
    parser = argparse.ArgumentParser(
        description="Генерация отчёта об экспериментах",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("reports/experiment_results.csv"),
        help="Путь к CSV с результатами (default: reports/experiment_results.csv)",
    )
    parser.add_argument(
        "--best-models",
        type=Path,
        default=Path("reports/best_models.json"),
        help="Путь к JSON с лучшими моделями (default: reports/best_models.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/experiments/generated_results.md"),
        help="Путь для сохранения отчёта (default: docs/experiments/generated_results.md)",
    )
    parser.add_argument(
        "--figures-dir",
        type=str,
        default="../assets/figures",
        help="Относительный путь к графикам (default: ../assets/figures)",
    )

    args = parser.parse_args()

    # Загрузка данных
    if args.results.exists():
        print(f"Загрузка результатов из {args.results}")
        results = load_results(args.results)
    else:
        print(f"Файл {args.results} не найден, создаю пустой отчёт")
        results = []

    best_models = None
    if args.best_models.exists():
        print(f"Загрузка лучших моделей из {args.best_models}")
        best_models = load_best_models(args.best_models)

    # Генерация отчёта
    report = generate_report(results, best_models, args.figures_dir)

    # Сохранение
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Отчёт сохранён: {args.output}")


if __name__ == "__main__":
    main()
