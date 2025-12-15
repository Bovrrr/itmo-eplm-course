"""Утилиты для анализа MLflow экспериментов."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from mlflow.entities import Run
from mlflow.tracking import MlflowClient


def get_best_run(
    experiment_name: str,
    metric: str = "accuracy",
    ascending: bool = False,
) -> Run | None:
    """Найти лучший run в эксперименте по заданной метрике.

    Args:
        experiment_name: Название эксперимента.
        metric: Название метрики для сортировки.
        ascending: True если меньше значение = лучше (например, для loss).

    Returns:
        Объект Run с лучшим значением метрики, или None если runs не найдены.

    Example:
        >>> best_run = get_best_run("titanic_classification", metric="accuracy")
        >>> if best_run:
        >>>     print(f"Best accuracy: {best_run.data.metrics['accuracy']}")
    """
    client = MlflowClient()

    # Получить эксперимент
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        print(f"Experiment '{experiment_name}' not found")
        return None

    # Получить все runs
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=[f"metrics.{metric} {'ASC' if ascending else 'DESC'}"],
        max_results=1,
    )

    if not runs:
        print(f"No runs found in experiment '{experiment_name}'")
        return None

    return runs[0]


def compare_runs(
    experiment_name: str,
    run_ids: list[str] | None = None,
    metrics: list[str] | None = None,
) -> pd.DataFrame:
    """Сравнить несколько runs из эксперимента.

    Args:
        experiment_name: Название эксперимента.
        run_ids: Список ID runs для сравнения. Если None, берутся все runs.
        metrics: Список метрик для включения в сравнение. Если None, берутся все.

    Returns:
        DataFrame с параметрами и метриками всех runs.

    Example:
        >>> df = compare_runs("titanic_classification", metrics=["accuracy", "f1_score"])
        >>> print(df.sort_values("accuracy", ascending=False))
    """
    client = MlflowClient()

    # Получить эксперимент
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        raise ValueError(f"Experiment '{experiment_name}' not found")

    # Получить runs
    if run_ids is not None:
        runs = [client.get_run(run_id) for run_id in run_ids]
    else:
        runs = client.search_runs(experiment_ids=[experiment.experiment_id])

    if not runs:
        return pd.DataFrame()

    # Собрать данные
    data = []
    for run in runs:
        row = {
            "run_id": run.info.run_id,
            "run_name": run.info.run_name or "unnamed",
            "start_time": run.info.start_time,
            "status": run.info.status,
        }

        # Добавить параметры
        row.update({f"param_{k}": v for k, v in run.data.params.items()})

        # Добавить метрики (фильтровать если указан список)
        if metrics is not None:
            row.update({f"metric_{k}": v for k, v in run.data.metrics.items() if k in metrics})
        else:
            row.update({f"metric_{k}": v for k, v in run.data.metrics.items()})

        data.append(row)

    return pd.DataFrame(data)


def get_experiment_summary(experiment_name: str) -> dict[str, int | float | str]:
    """Получить сводку по эксперименту.

    Args:
        experiment_name: Название эксперимента.

    Returns:
        Словарь со статистикой эксперимента.

    Example:
        >>> summary = get_experiment_summary("titanic_classification")
        >>> print(f"Total runs: {summary['total_runs']}")
    """
    client = MlflowClient()

    # Получить эксперимент
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        raise ValueError(f"Experiment '{experiment_name}' not found")

    # Получить все runs
    runs = client.search_runs(experiment_ids=[experiment.experiment_id])

    # Собрать статистику
    summary: dict[str, int | float | str] = {
        "experiment_name": experiment_name,
        "experiment_id": experiment.experiment_id,
        "total_runs": len(runs),
        "active_runs": sum(1 for r in runs if r.info.status == "RUNNING"),
        "finished_runs": sum(1 for r in runs if r.info.status == "FINISHED"),
        "failed_runs": sum(1 for r in runs if r.info.status == "FAILED"),
    }

    # Найти лучшие метрики (если runs есть)
    if runs:
        # Собрать все метрики
        all_metrics: set[str] = set()
        for run in runs:
            all_metrics.update(run.data.metrics.keys())

        # Для каждой метрики найти мин/макс
        for metric in all_metrics:
            values = [run.data.metrics[metric] for run in runs if metric in run.data.metrics]
            if values:
                summary[f"best_{metric}"] = max(values)
                summary[f"worst_{metric}"] = min(values)
                summary[f"mean_{metric}"] = sum(values) / len(values)

    return summary


def export_runs_to_dataframe(experiment_name: str) -> pd.DataFrame:
    """Экспортировать все runs эксперимента в pandas DataFrame.

    Args:
        experiment_name: Название эксперимента.

    Returns:
        DataFrame со всеми параметрами и метриками всех runs.

    Example:
        >>> df = export_runs_to_dataframe("titanic_classification")
        >>> df.to_csv("experiment_results.csv", index=False)
    """
    return compare_runs(experiment_name, run_ids=None, metrics=None)


def plot_metrics_comparison(
    experiment_name: str,
    metrics: list[str],
    output_path: str | Path | None = None,
) -> None:
    """Визуализировать сравнение метрик между runs.

    Создаёт bar plot для сравнения указанных метрик между всеми runs.

    Args:
        experiment_name: Название эксперимента.
        metrics: Список метрик для визуализации.
        output_path: Путь для сохранения графика. Если None, показывает интерактивно.

    Example:
        >>> plot_metrics_comparison(
        >>>     "titanic_classification",
        >>>     metrics=["accuracy", "f1_score"],
        >>>     output_path="reports/figures/metrics_comparison.png"
        >>> )
    """
    # Получить данные
    df = compare_runs(experiment_name, metrics=metrics)

    if df.empty:
        print("No runs to plot")
        return

    # Подготовить данные для plotting
    plot_data = df[["run_name"] + [f"metric_{m}" for m in metrics]].copy()
    plot_data = plot_data.rename(columns={f"metric_{m}": m for m in metrics})

    # Создать фигуру
    fig, ax = plt.subplots(figsize=(12, 6))

    # Построить grouped bar chart
    plot_data.set_index("run_name")[metrics].plot(kind="bar", ax=ax)

    ax.set_title(f"Metrics Comparison - {experiment_name}", fontsize=14, fontweight="bold")
    ax.set_xlabel("Run Name", fontsize=12)
    ax.set_ylabel("Metric Value", fontsize=12)
    ax.legend(title="Metrics", fontsize=10)
    ax.grid(axis="y", alpha=0.3)

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Сохранить или показать
    if output_path is not None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved to {output_path}")
    else:
        plt.show()

    plt.close()


def plot_metrics_heatmap(
    experiment_name: str,
    output_path: str | Path | None = None,
) -> None:
    """Создать heatmap корреляции метрик.

    Args:
        experiment_name: Название эксперимента.
        output_path: Путь для сохранения графика. Если None, показывает интерактивно.

    Example:
        >>> plot_metrics_heatmap(
        >>>     "titanic_classification",
        >>>     output_path="reports/figures/metrics_heatmap.png"
        >>> )
    """
    # Получить данные
    df = export_runs_to_dataframe(experiment_name)

    if df.empty:
        print("No runs to plot")
        return

    # Выбрать только метрики
    metric_cols = [col for col in df.columns if col.startswith("metric_")]
    if not metric_cols:
        print("No metrics found")
        return

    metrics_df = df[metric_cols].copy()
    metrics_df.columns = [col.replace("metric_", "") for col in metric_cols]

    # Вычислить корреляцию
    corr = metrics_df.corr()

    # Создать heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        square=True,
        linewidths=1,
        cbar_kws={"shrink": 0.8},
        ax=ax,
    )

    ax.set_title(
        f"Metrics Correlation Heatmap - {experiment_name}",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )

    plt.tight_layout()

    # Сохранить или показать
    if output_path is not None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Heatmap saved to {output_path}")
    else:
        plt.show()

    plt.close()
