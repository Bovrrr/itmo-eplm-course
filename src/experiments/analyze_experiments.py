"""Анализ результатов ML экспериментов.

Этот модуль предоставляет функции для анализа и визуализации результатов
экспериментов, залогированных в MLflow.

Пример использования:
    uv run python src/experiments/analyze_experiments.py
"""

import json
import sys
from pathlib import Path
from typing import Any

import click
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from rich.console import Console

from src.mlflow_utils import (
    export_runs_to_dataframe,
    get_experiment_summary,
    plot_metrics_comparison,
    plot_metrics_heatmap,
)

# Настройка стиля графиков
sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 300
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["figure.figsize"] = (12, 6)

# Rich console
console = Console()


def create_boxplot_by_model_class(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Создать boxplot для сравнения метрик по типам моделей.

    Args:
        df: DataFrame с результатами экспериментов
        output_path: Путь для сохранения графика

    Example:
        >>> create_boxplot_by_model_class(df, Path("boxplot.png"))
    """
    # Извлечь тип модели из параметров
    df_plot = df.copy()
    df_plot["model_class"] = df_plot["param_model_type"]

    # Выбрать метрики для визуализации
    metrics = ["metric_accuracy", "metric_f1_score"]

    # Создать subplot для каждой метрики
    fig, axes = plt.subplots(1, len(metrics), figsize=(14, 6))

    for idx, metric in enumerate(metrics):
        sns.boxplot(
            data=df_plot,
            x="model_class",
            y=metric,
            ax=axes[idx],
            palette="Set2",
        )
        axes[idx].set_title(f"Распределение {metric.split('.')[-1]} по типам моделей")
        axes[idx].set_xlabel("Тип модели")
        axes[idx].set_ylabel(metric.split(".")[-1].capitalize())
        axes[idx].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    console.print(f"[green]✓ Boxplot сохранён: {output_path}")


def create_training_time_comparison(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Создать график сравнения времени обучения.

    Args:
        df: DataFrame с результатами экспериментов
        output_path: Путь для сохранения графика

    Example:
        >>> create_training_time_comparison(df, Path("time.png"))
    """
    # Отсортировать по времени обучения
    df_plot = df.sort_values("metric_train_time_seconds", ascending=False)

    plt.figure(figsize=(12, 8))
    sns.barplot(
        data=df_plot,
        y="param_config_name",
        x="metric_train_time_seconds",
        palette="viridis",
    )

    plt.title("Сравнение времени обучения моделей", fontsize=16, fontweight="bold")
    plt.xlabel("Время обучения (секунды)", fontsize=12)
    plt.ylabel("Конфигурация модели", fontsize=12)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    console.print(f"[green]✓ График времени обучения сохранён: {output_path}")


def create_best_models_summary(
    df: pd.DataFrame,
    output_path: Path,
    top_n: int = 5,
) -> None:
    """Создать summary график топ-N моделей.

    Args:
        df: DataFrame с результатами экспериментов
        output_path: Путь для сохранения графика
        top_n: Количество лучших моделей для отображения

    Example:
        >>> create_best_models_summary(df, Path("best.png"), top_n=5)
    """
    # Топ-N моделей по accuracy
    df_top = df.nlargest(top_n, "metric_accuracy")

    # Выбрать метрики для визуализации
    metrics = [
        "metric_accuracy",
        "metric_precision",
        "metric_recall",
        "metric_f1_score",
    ]

    # Подготовить данные
    plot_data = []
    for _, row in df_top.iterrows():
        config_name = row["param_config_name"]
        for metric in metrics:
            plot_data.append(
                {
                    "model": config_name,
                    "metric": metric.replace("metric_", ""),
                    "value": row[metric],
                }
            )

    df_plot = pd.DataFrame(plot_data)

    plt.figure(figsize=(14, 8))
    sns.barplot(
        data=df_plot,
        x="model",
        y="value",
        hue="metric",
        palette="Set2",
    )

    plt.title(f"Топ-{top_n} моделей по accuracy", fontsize=16, fontweight="bold")
    plt.xlabel("Модель", fontsize=12)
    plt.ylabel("Значение метрики", fontsize=12)
    plt.ylim(0, 1.1)
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Метрика", loc="lower right")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    console.print(f"[green]✓ График топ-{top_n} моделей сохранён: {output_path}")


def export_best_models(
    df: pd.DataFrame,
    output_path: Path,
) -> dict[str, Any]:
    """Найти и экспортировать лучшие модели по метрикам.

    Args:
        df: DataFrame с результатами экспериментов
        output_path: Путь для сохранения JSON

    Returns:
        Словарь с лучшими моделями по каждой метрике

    Example:
        >>> best = export_best_models(df, Path("best.json"))
        >>> print(best["best_accuracy"]["config_name"])
    """
    metrics = ["accuracy", "precision", "recall", "f1_score"]

    best_models: dict[str, Any] = {}

    for metric in metrics:
        metric_col = f"metric_{metric}"
        best_row = df.loc[df[metric_col].idxmax()]

        best_models[f"best_{metric}"] = {
            "config_name": best_row["param_config_name"],
            "model_class": best_row["param_model_type"],
            "value": float(best_row[metric_col]),
            "run_id": best_row["run_id"],
        }

    # Сохранить в JSON
    with output_path.open("w") as f:
        json.dump(best_models, f, indent=2)

    console.print(f"[green]✓ Лучшие модели экспортированы: {output_path}")

    return best_models


@click.command()
@click.option(
    "--experiment-name",
    default="titanic_classification",
    help="Имя эксперимента в MLflow",
)
@click.option(
    "--output-dir",
    default="reports/figures/hw03",
    help="Директория для сохранения визуализаций",
)
@click.option(
    "--top-n",
    default=18,
    help="Количество последних runs для анализа (по timestamp)",
)
def main(experiment_name: str, output_dir: str, top_n: int) -> None:  # noqa: PLR0915
    """Анализировать результаты ML экспериментов.

    Этот скрипт:
    1. Экспортирует runs из MLflow в CSV
    2. Создаёт 5 типов визуализаций
    3. Находит лучшие модели по метрикам
    4. Сохраняет результаты в reports/

    Примеры использования:

        # Анализ с параметрами по умолчанию
        $ python src/experiments/analyze_experiments.py

        # Анализ другого эксперимента
        $ python src/experiments/analyze_experiments.py --experiment-name "my_exp"
    """
    console.rule("[bold blue]Анализ результатов экспериментов")

    # Создать выходную директорию
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[cyan]Эксперимент: {experiment_name}")
    console.print(f"[cyan]Выходная директория: {output_dir}\n")

    # 1. Экспортировать runs в DataFrame
    console.print("[yellow]1. Экспорт данных из MLflow...")
    try:
        df = export_runs_to_dataframe(experiment_name)
    except Exception as e:
        console.print(f"[bold red]Ошибка при экспорте данных: {e}")
        console.print("[yellow]Убедитесь что:")
        console.print("  - Эксперимент существует в MLflow")
        console.print("  - Runs были успешно залогированы")
        console.print("  - Путь к mlruns/ корректен")
        sys.exit(1)

    if df.empty:
        console.print(f"[bold red]Эксперимент '{experiment_name}' не содержит runs!")
        console.print(
            "[yellow]Запустите: uv run python src/experiments/run_experiments.py --models all"
        )
        sys.exit(1)

    console.print(f"[green]✓ Загружено {len(df)} runs")

    # Фильтровать только последние top_n runs (по timestamp)
    if top_n > 0 and len(df) > top_n:
        df = df.sort_values("start_time", ascending=False).head(top_n)
        console.print(f"[yellow]Фильтр: анализируем только последние {top_n} runs")

    # Получить общую статистику
    summary = get_experiment_summary(experiment_name)
    console.print(
        f"[cyan]Runs: total={summary['total_runs']}, active={summary['active_runs']}, finished={summary['finished_runs']}"
    )

    # 2. Сохранить в CSV
    csv_path = Path("reports/experiment_results.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    console.print(f"[green]✓ Экспортировано в CSV: {csv_path}\n")

    # 3. Создать визуализации
    console.print("[yellow]2. Создание визуализаций...")

    # 3.1 Metrics comparison (используя mlflow_utils)
    try:
        metrics = ["accuracy", "precision", "recall", "f1_score"]
        plot_metrics_comparison(
            experiment_name,
            metrics,
            output_path / "metrics_comparison.png",
        )
    except Exception as e:
        console.print(f"[red]Ошибка при создании metrics_comparison: {e}")

    # 3.2 Metrics heatmap (используя mlflow_utils)
    try:
        plot_metrics_heatmap(
            experiment_name,
            output_path / "metrics_heatmap.png",
        )
    except Exception as e:
        console.print(f"[red]Ошибка при создании metrics_heatmap: {e}")

    # 3.3 Boxplot по типам моделей
    try:
        create_boxplot_by_model_class(
            df,
            output_path / "model_comparison_boxplot.png",
        )
    except Exception as e:
        console.print(f"[red]Ошибка при создании boxplot: {e}")

    # 3.4 Сравнение времени обучения
    try:
        create_training_time_comparison(
            df,
            output_path / "training_time_comparison.png",
        )
    except Exception as e:
        console.print(f"[red]Ошибка при создании training_time: {e}")

    # 3.5 Топ-5 моделей
    try:
        create_best_models_summary(
            df,
            output_path / "best_models_summary.png",
            top_n=5,
        )
    except Exception as e:
        console.print(f"[red]Ошибка при создании best_models: {e}")

    console.print("")

    # 4. Найти лучшие модели
    console.print("[yellow]3. Поиск лучших моделей...")
    best_models_path = Path("reports/best_models.json")
    try:
        best_models = export_best_models(df, best_models_path)

        # Вывести лучшие модели
        console.print("\n[bold cyan]Лучшие модели по метрикам:")
        for metric_name, model_info in best_models.items():
            console.print(
                f"  • {metric_name}: [green]{model_info['config_name']}[/green] "
                f"({model_info['value']:.4f})"
            )
    except Exception as e:
        console.print(f"[red]Ошибка при экспорте лучших моделей: {e}")

    # 5. Вывести рекомендации
    console.print("\n[bold blue]Рекомендации:")
    console.print("  1. Просмотреть визуализации в reports/figures/hw03/")
    console.print("  2. Открыть MLflow UI: mlflow ui --port 5000")
    console.print("  3. Обновить REPORT.md с результатами")

    console.print("\n[bold green]✨ Анализ завершён успешно!")


if __name__ == "__main__":
    main()
