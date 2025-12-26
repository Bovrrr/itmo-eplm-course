"""Массовый запуск ML экспериментов с различными конфигурациями моделей.

Этот модуль предоставляет CLI для автоматического запуска экспериментов
с несколькими конфигурациями моделей и сохранения результатов.

Пример использования:
    uv run python src/experiments/run_experiments.py --models all
    uv run python src/experiments/run_experiments.py --models "rf_medium,lr_l1"
"""

import json
import logging
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from clearml import Task
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from src.models.model_configs import list_model_configs
from src.models.train_model import train_model_pipeline

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rich console для красивого вывода
console = Console()


def run_single_experiment(
    config_name: str,
    train_data_path: str,
    val_data_path: str,
    output_dir: Path,
    continue_on_error: bool = True,
) -> dict[str, Any]:
    """Запустить один эксперимент и вернуть результат.

    Args:
        config_name: Имя конфигурации модели
        train_data_path: Путь к train данным с признаками
        val_data_path: Путь к validation данным с признаками
        output_dir: Директория для сохранения модели
        continue_on_error: Продолжать ли при ошибке

    Returns:
        Словарь с результатами эксперимента:
        - config_name: имя конфигурации
        - status: "success" или "failed"
        - metrics: метрики модели (если успешно)
        - error: описание ошибки (если failed)
        - task_id: ClearML Task ID (если успешно)
        - execution_time: время выполнения в секундах

    Example:
        >>> result = run_single_experiment(
        ...     "random_forest_medium",
        ...     "data/features/train_features.csv",
        ...     "data/features/val_features.csv",
        ...     Path("models/experiments"),
        ... )
        >>> print(result["status"])
        'success'
    """
    start_time = time.time()

    # Создать директорию для модели
    model_dir = output_dir / config_name
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "model.pkl"

    try:
        # Запустить обучение модели через train_model_pipeline
        # train_model_pipeline уже создаёт свой ClearML Task через декоратор
        metrics = train_model_pipeline(
            train_data_path=train_data_path,
            val_data_path=val_data_path,
            model_output_path=str(model_path),
            config_name=config_name,
        )

        # Получить task_id из текущего task (если есть)
        task_id = None
        current_task = Task.current_task()
        if current_task:
            task_id = current_task.id

        execution_time = time.time() - start_time

        result: dict[str, Any] = {
            "config_name": config_name,
            "status": "success",
            "metrics": metrics,
            "task_id": task_id,
            "execution_time": execution_time,
        }

        logger.info(f"✅ {config_name}: success (accuracy={metrics.get('accuracy', 'N/A')})")

        return result

    except Exception as e:
        execution_time = time.time() - start_time

        logger.error(f"❌ {config_name}: failed - {e}")

        result = {
            "config_name": config_name,
            "status": "failed",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "execution_time": execution_time,
        }

        # Сохранить traceback в файл для отладки
        error_log = output_dir / f"{config_name}_error.log"
        error_log.write_text(
            f"Error: {e}\n\n"
            f"Traceback:\n{traceback.format_exc()}\n\n"
            f"Timestamp: {datetime.now().isoformat()}\n"
        )

        if not continue_on_error:
            raise

        return result


def generate_summary_report(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Сгенерировать summary report из результатов экспериментов.

    Args:
        results: Список результатов экспериментов

    Returns:
        Словарь с общей статистикой:
        - total_experiments: общее количество
        - successful: количество успешных
        - failed: количество неудачных
        - total_time_seconds: общее время выполнения
        - best_model: лучшая модель по accuracy
        - failed_models: список неудачных моделей
        - timestamp: время создания отчёта

    Example:
        >>> summary = generate_summary_report(results)
        >>> print(f"Success rate: {summary['successful']}/{summary['total_experiments']}")
    """
    successful_results = [r for r in results if r["status"] == "success"]
    failed_results = [r for r in results if r["status"] == "failed"]

    total_time = sum(r["execution_time"] for r in results)

    # Найти лучшую модель по accuracy
    best_model = None
    if successful_results:
        best_model = max(
            successful_results,
            key=lambda r: r["metrics"].get("accuracy", 0),
        )

    summary: dict[str, Any] = {
        "total_experiments": len(results),
        "successful": len(successful_results),
        "failed": len(failed_results),
        "total_time_seconds": total_time,
        "best_model": {
            "config_name": best_model["config_name"],
            "accuracy": best_model["metrics"].get("accuracy"),
            "task_id": best_model.get("task_id"),
        }
        if best_model
        else None,
        "failed_models": [
            {"config": r["config_name"], "error": r["error"]} for r in failed_results
        ],
        "timestamp": datetime.now().isoformat(),
    }

    return summary


def print_summary_table(summary: dict[str, Any], results: list[dict[str, Any]]) -> None:
    """Вывести красивую таблицу с результатами через rich.Table.

    Args:
        summary: Сводная статистика
        results: Список результатов экспериментов

    Example:
        >>> print_summary_table(summary, results)
        # Выводит красиво отформатированную таблицу в терминал
    """
    console.print("\n")
    console.rule("[bold blue]Результаты экспериментов")

    # Общая статистика
    stats_table = Table(title="Общая статистика", show_header=False)
    stats_table.add_column("Параметр", style="cyan")
    stats_table.add_column("Значение", style="green")

    stats_table.add_row("Всего экспериментов", str(summary["total_experiments"]))
    stats_table.add_row("Успешно", f"✅ {summary['successful']}")
    stats_table.add_row("Неудачно", f"❌ {summary['failed']}")
    stats_table.add_row("Общее время", f"{summary['total_time_seconds']:.1f} сек")

    if summary["best_model"]:
        best = summary["best_model"]
        stats_table.add_row(
            "Лучшая модель",
            f"{best['config_name']} (accuracy={best['accuracy']:.4f})",
        )

    console.print(stats_table)

    # Таблица результатов
    console.print("\n")
    results_table = Table(title="Детальные результаты")
    results_table.add_column("#", justify="right", style="dim")
    results_table.add_column("Конфигурация", style="cyan")
    results_table.add_column("Статус", justify="center")
    results_table.add_column("Accuracy", justify="right", style="green")
    results_table.add_column("F1 Score", justify="right", style="green")
    results_table.add_column("Время (с)", justify="right", style="yellow")

    for idx, result in enumerate(results, 1):
        status_icon = "✅" if result["status"] == "success" else "❌"

        if result["status"] == "success":
            metrics = result["metrics"]
            accuracy = f"{metrics.get('accuracy', 0):.4f}"
            f1_score = f"{metrics.get('f1_score', 0):.4f}"
        else:
            accuracy = "N/A"
            f1_score = "N/A"

        exec_time = f"{result['execution_time']:.2f}"

        results_table.add_row(
            str(idx),
            result["config_name"],
            status_icon,
            accuracy,
            f1_score,
            exec_time,
        )

    console.print(results_table)

    # Показать ошибки если есть
    if summary["failed_models"]:
        console.print("\n")
        console.print("[bold red]Неудачные эксперименты:")
        for failed in summary["failed_models"]:
            console.print(f"  - {failed['config']}: {failed['error']}")

    console.print("\n")


@click.command()
@click.option(
    "--models",
    default="all",
    help='Список моделей через запятую или "all" для всех',
)
@click.option(
    "--data-dir",
    default="data/features",
    help="Директория с train/val данными с признаками",
)
@click.option(
    "--output-dir",
    default="models/experiments",
    help="Директория для сохранения моделей",
)
@click.option(
    "--continue-on-error/--stop-on-error",
    default=True,
    help="Продолжать ли при ошибках",
)
def main(models: str, data_dir: str, output_dir: str, continue_on_error: bool) -> None:
    """Запустить массовые ML эксперименты.

    Этот скрипт автоматически запускает обучение моделей с различными
    конфигурациями, логирует результаты в ClearML и создаёт сводный отчёт.

    Примеры использования:

        # Запустить все эксперименты
        $ python src/experiments/run_experiments.py --models all

        # Запустить конкретные модели
        $ python src/experiments/run_experiments.py --models "rf_medium,lr_l1"

        # Остановиться при первой ошибке
        $ python src/experiments/run_experiments.py --models all --stop-on-error
    """
    console.rule("[bold blue]Массовый запуск экспериментов")

    # Определить список конфигураций
    if models.lower() == "all":
        config_names = list_model_configs()
    else:
        config_names = [name.strip() for name in models.split(",")]

    # Проверить что конфигурации существуют
    all_configs = list_model_configs()
    invalid_configs = [name for name in config_names if name not in all_configs]
    if invalid_configs:
        console.print(f"[bold red]Ошибка: неизвестные конфигурации: {invalid_configs}")
        console.print(f"[yellow]Доступные конфигурации: {', '.join(all_configs)}")
        sys.exit(1)

    # Проверить что данные существуют
    data_dir_path = Path(data_dir)
    train_file = data_dir_path / "train_features.csv"
    val_file = data_dir_path / "val_features.csv"

    if not train_file.exists() or not val_file.exists():
        console.print(f"[bold red]Ошибка: файлы с данными не найдены в {data_dir}")
        console.print("[yellow]Запустите: uv run dvc repro")
        sys.exit(1)

    # Создать выходную директорию
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Конструировать пути к train и val данным
    train_data_path = str(train_file)
    val_data_path = str(val_file)

    console.print(f"\n[cyan]Запуск {len(config_names)} экспериментов...")
    console.print(f"[cyan]Train данные: {train_data_path}")
    console.print(f"[cyan]Val данные: {val_data_path}")
    console.print(f"[cyan]Выходная директория: {output_dir}")
    console.print(f"[cyan]Continue on error: {continue_on_error}\n")

    # Запустить эксперименты с progress bar
    results: list[dict[str, Any]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            "Обучение моделей...",
            total=len(config_names),
        )

        for config_name in config_names:
            progress.update(task, description=f"Обучение: {config_name}")

            result = run_single_experiment(
                config_name=config_name,
                train_data_path=train_data_path,
                val_data_path=val_data_path,
                output_dir=output_path,
                continue_on_error=continue_on_error,
            )

            results.append(result)
            progress.advance(task)

    # Сгенерировать summary report
    summary = generate_summary_report(results)

    # Сохранить summary в JSON
    summary_path = output_path / "summary_report.json"
    with summary_path.open("w") as f:
        json.dump(summary, f, indent=2)

    console.print(f"\n[green]Summary report сохранён в: {summary_path}")

    # Вывести красивую таблицу с результатами
    print_summary_table(summary, results)

    # Вывести рекомендации
    if summary["successful"] == len(config_names):
        console.print("[bold green]🎉 Все эксперименты завершились успешно!")
    elif summary["successful"] > 0:
        console.print(
            f"[bold yellow]⚠️  Завершено {summary['successful']}/{len(config_names)} экспериментов"
        )
    else:
        console.print("[bold red]❌ Все эксперименты завершились с ошибками")
        sys.exit(1)

    console.print("\n[cyan]Следующие шаги:")
    console.print(
        "  1. Проанализировать результаты: uv run python src/experiments/analyze_experiments.py"
    )
    console.print("  2. Просмотреть ClearML UI: https://app.clear.ml")


if __name__ == "__main__":
    main()
