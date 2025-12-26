"""CLI для работы с ClearML Model Registry.

Этот модуль предоставляет команды для просмотра и управления моделями
в ClearML Model Registry.

Пример использования:
    uv run python -m src.models.model_registry list-models
    uv run python -m src.models.model_registry best-model --metric accuracy
    uv run python -m src.models.model_registry compare-models
"""

import logging
from typing import Any

import click
from clearml import Model, Task
from rich.console import Console
from rich.table import Table

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rich console для красивого вывода
console = Console()

# Название проекта по умолчанию
DEFAULT_PROJECT = "titanic_classification"


@click.group()
def cli() -> None:
    """CLI для работы с ClearML Model Registry.

    Команды для просмотра и управления моделями в ClearML.
    """
    pass


@cli.command("list-models")
@click.option(
    "--project",
    default=DEFAULT_PROJECT,
    help="Название проекта ClearML",
)
@click.option(
    "--limit",
    default=20,
    help="Максимальное количество моделей для показа",
)
def list_models(project: str, limit: int) -> None:
    """Показать список всех моделей в проекте.

    Example:
        $ python -m src.models.model_registry list-models
        $ python -m src.models.model_registry list-models --project my_project
    """
    console.rule(f"[bold blue]Модели в проекте: {project}")

    try:
        # Получить все модели проекта
        models = Model.query_models(
            project_name=project,
            max_results=limit,
        )

        if not models:
            console.print("[yellow]Модели не найдены")
            return

        # Создать таблицу
        table = Table(title=f"Модели ({len(models)})")
        table.add_column("#", justify="right", style="dim")
        table.add_column("ID", style="cyan")
        table.add_column("Название", style="green")
        table.add_column("Framework", style="yellow")
        table.add_column("Теги", style="magenta")

        for idx, model in enumerate(models, 1):
            tags = ", ".join(model.tags) if model.tags else "-"

            table.add_row(
                str(idx),
                model.id[:8] + "...",
                model.name or "-",
                model.framework or "-",
                tags,
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Ошибка: {e}")
        logger.error(f"Failed to list models: {e}", exc_info=True)


@cli.command("best-model")
@click.option(
    "--project",
    default=DEFAULT_PROJECT,
    help="Название проекта ClearML",
)
@click.option(
    "--metric",
    default="accuracy",
    help="Метрика для сравнения (accuracy, f1_score, roc_auc)",
)
@click.option(
    "--higher-is-better/--lower-is-better",
    default=True,
    help="Направление оптимизации метрики",
)
def best_model(project: str, metric: str, higher_is_better: bool) -> None:
    """Найти лучшую модель по указанной метрике.

    Example:
        $ python -m src.models.model_registry best-model --metric accuracy
        $ python -m src.models.model_registry best-model --metric f1_score
    """
    console.rule(f"[bold blue]Лучшая модель по метрике: {metric}")

    try:
        # Получить все завершённые задачи проекта
        tasks = Task.get_tasks(
            project_name=project,
            task_filter={"status": ["completed"]},
        )

        if not tasks:
            console.print("[yellow]Завершённые задачи не найдены")
            return

        best_task = None
        best_value = float("-inf") if higher_is_better else float("inf")
        results: list[dict[str, Any]] = []

        for task in tasks:
            # Получить метрики задачи
            scalars = task.get_reported_scalars()
            if "Metrics" in scalars and metric in scalars["Metrics"]:
                values = scalars["Metrics"][metric]["y"]
                if values:
                    value = values[-1]  # Последнее значение
                    results.append(
                        {
                            "task_id": task.id,
                            "task_name": task.name,
                            "value": value,
                        }
                    )

                    if (
                        higher_is_better
                        and value > best_value
                        or not higher_is_better
                        and value < best_value
                    ):
                        best_value = value
                        best_task = task

        if not results:
            console.print(f"[yellow]Метрика '{metric}' не найдена ни в одной задаче")
            return

        # Отсортировать результаты
        results.sort(key=lambda x: x["value"], reverse=higher_is_better)

        # Показать топ-5
        table = Table(title=f"Топ-5 по {metric}")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Task Name", style="cyan")
        table.add_column(metric.capitalize(), justify="right", style="green")
        table.add_column("Task ID", style="yellow")

        for idx, result in enumerate(results[:5], 1):
            is_best = "🏆 " if idx == 1 else ""
            table.add_row(
                str(idx),
                f"{is_best}{result['task_name']}",
                f"{result['value']:.4f}",
                result["task_id"][:12] + "...",
            )

        console.print(table)

        if best_task:
            console.print(f"\n[bold green]🏆 Лучшая модель: {best_task.name}")
            console.print(f"   Task ID: {best_task.id}")
            console.print(f"   {metric}: {best_value:.4f}")

    except Exception as e:
        console.print(f"[bold red]Ошибка: {e}")
        logger.error(f"Failed to find best model: {e}", exc_info=True)


@cli.command("compare-models")
@click.option(
    "--project",
    default=DEFAULT_PROJECT,
    help="Название проекта ClearML",
)
@click.option(
    "--limit",
    default=10,
    help="Максимальное количество моделей для сравнения",
)
def compare_models(project: str, limit: int) -> None:  # noqa: PLR0912
    """Сравнить модели по всем метрикам.

    Example:
        $ python -m src.models.model_registry compare-models
        $ python -m src.models.model_registry compare-models --limit 5
    """
    console.rule(f"[bold blue]Сравнение моделей в проекте: {project}")

    try:
        # Получить все завершённые задачи проекта
        tasks = Task.get_tasks(
            project_name=project,
            task_filter={"status": ["completed"]},
        )

        if not tasks:
            console.print("[yellow]Завершённые задачи не найдены")
            return

        # Собрать метрики для каждой задачи
        results: list[dict[str, Any]] = []
        metrics_set: set[str] = set()

        for task in tasks[:limit]:
            scalars = task.get_reported_scalars()
            task_metrics: dict[str, float] = {}

            if "Metrics" in scalars:
                for metric_name, metric_data in scalars["Metrics"].items():
                    if "y" in metric_data and metric_data["y"]:
                        task_metrics[metric_name] = metric_data["y"][-1]
                        metrics_set.add(metric_name)

            if task_metrics:
                results.append(
                    {
                        "task_id": task.id,
                        "task_name": task.name,
                        "metrics": task_metrics,
                    }
                )

        if not results:
            console.print("[yellow]Метрики не найдены")
            return

        # Отсортировать по accuracy (если есть)
        results.sort(
            key=lambda x: x["metrics"].get("accuracy", 0),
            reverse=True,
        )

        # Создать таблицу
        table = Table(title=f"Сравнение моделей ({len(results)})")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Task Name", style="cyan")

        # Добавить колонки для каждой метрики
        metric_columns = sorted(metrics_set)
        for metric in metric_columns:
            table.add_column(metric[:12], justify="right", style="green")

        # Добавить строки
        for idx, result in enumerate(results, 1):
            row = [str(idx), result["task_name"]]
            for metric in metric_columns:
                value = result["metrics"].get(metric)
                if value is not None:
                    row.append(f"{value:.4f}")
                else:
                    row.append("-")
            table.add_row(*row)

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Ошибка: {e}")
        logger.error(f"Failed to compare models: {e}", exc_info=True)


@cli.command("model-info")
@click.argument("model_id")
def model_info(model_id: str) -> None:
    """Показать детальную информацию о модели.

    Example:
        $ python -m src.models.model_registry model-info abc123
    """
    console.rule(f"[bold blue]Информация о модели: {model_id}")

    try:
        # Получить модель по ID
        model = Model(model_id=model_id)

        table = Table(title="Детали модели", show_header=False)
        table.add_column("Параметр", style="cyan")
        table.add_column("Значение", style="green")

        table.add_row("ID", model.id)
        table.add_row("Название", model.name or "-")
        table.add_row("Framework", model.framework or "-")
        table.add_row("Теги", ", ".join(model.tags) if model.tags else "-")
        table.add_row("Создано", model.created or "-")
        table.add_row("URL", model.url or "-")

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Ошибка: {e}")
        logger.error(f"Failed to get model info: {e}", exc_info=True)


@cli.command("list-tasks")
@click.option(
    "--project",
    default=DEFAULT_PROJECT,
    help="Название проекта ClearML",
)
@click.option(
    "--status",
    default="completed",
    type=click.Choice(["completed", "running", "failed", "all"]),
    help="Фильтр по статусу задач",
)
@click.option(
    "--limit",
    default=20,
    help="Максимальное количество задач",
)
def list_tasks(project: str, status: str, limit: int) -> None:
    """Показать список задач проекта.

    Example:
        $ python -m src.models.model_registry list-tasks
        $ python -m src.models.model_registry list-tasks --status running
    """
    console.rule(f"[bold blue]Задачи в проекте: {project}")

    try:
        # Подготовить фильтр
        status_filter = None if status == "all" else {"status": [status]}

        # Получить задачи
        tasks = Task.get_tasks(
            project_name=project,
            task_filter=status_filter,
        )

        if not tasks:
            console.print(f"[yellow]Задачи со статусом '{status}' не найдены")
            return

        # Ограничить количество
        tasks = tasks[:limit]

        # Создать таблицу
        table = Table(title=f"Задачи ({len(tasks)})")
        table.add_column("#", justify="right", style="dim")
        table.add_column("ID", style="cyan")
        table.add_column("Название", style="green")
        table.add_column("Статус", style="yellow")
        table.add_column("Создано", style="blue")

        for idx, task in enumerate(tasks, 1):
            status_icon = {
                "completed": "✅",
                "running": "🔄",
                "failed": "❌",
                "created": "📝",
            }.get(task.status, "❓")

            created = str(task.data.started)[:19] if task.data.started else "-"

            table.add_row(
                str(idx),
                task.id[:12] + "...",
                task.name or "-",
                f"{status_icon} {task.status}",
                created,
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Ошибка: {e}")
        logger.error(f"Failed to list tasks: {e}", exc_info=True)


if __name__ == "__main__":
    cli()
