"""Утилиты для уведомлений и красивого вывода в терминал."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@contextmanager
def stage_notification(stage_name: str) -> Generator[None]:
    """Context manager для уведомлений о начале и завершении stage.

    Args:
        stage_name: Название stage (например, "Data Split")

    Example:
        with stage_notification("Data Split"):
            # ... код stage
            notify_metrics({"train_size": 500}, title="Split Summary")
    """
    # Уведомление о начале
    console.print(
        Panel(
            f"[bold cyan]Starting stage:[/bold cyan] {stage_name}",
            border_style="cyan",
            padding=(0, 2),
        )
    )

    try:
        yield
        # Уведомление об успешном завершении
        console.print(
            Panel(
                f"[bold green]✓ Stage completed:[/bold green] {stage_name}",
                border_style="green",
                padding=(0, 2),
            )
        )
    except Exception as e:
        # Уведомление об ошибке
        console.print(
            Panel(
                f"[bold red]✗ Stage failed:[/bold red] {stage_name}\n[red]Error:[/red] {e!s}",
                border_style="red",
                padding=(0, 2),
            )
        )
        raise


def notify_metrics(metrics: dict[str, Any], title: str = "Metrics") -> None:
    """Вывести метрики в виде красивой таблицы.

    Args:
        metrics: Словарь с метриками {название: значение}
        title: Заголовок таблицы

    Example:
        notify_metrics({
            "train_size": 500,
            "val_size": 100,
            "test_size": 100,
            "stratified": True
        }, title="Split Summary")
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    for key, value in metrics.items():
        # Форматирование значений
        if isinstance(value, float):
            formatted_value = f"{value:.4f}"
        elif isinstance(value, bool):
            formatted_value = "✓" if value else "✗"
        else:
            formatted_value = str(value)

        table.add_row(key, formatted_value)

    console.print(table)


def notify_info(message: str) -> None:
    """Вывести информационное сообщение.

    Args:
        message: Текст сообщения
    """
    console.print(f"[blue]ℹ[/blue] {message}")


def notify_success(message: str) -> None:
    """Вывести сообщение об успехе.

    Args:
        message: Текст сообщения
    """
    console.print(f"[green]✓[/green] {message}")


def notify_warning(message: str) -> None:
    """Вывести предупреждение.

    Args:
        message: Текст предупреждения
    """
    console.print(f"[yellow]⚠[/yellow] {message}")


def notify_error(message: str) -> None:
    """Вывести сообщение об ошибке.

    Args:
        message: Текст ошибки
    """
    console.print(f"[red]✗[/red] {message}")
