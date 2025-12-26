"""Утилиты для работы с ClearML Task."""

from pathlib import Path
from typing import Any

from clearml import Task


def get_current_task() -> Task | None:
    """Получить текущий активный Task.

    Returns:
        Текущий Task или None если нет активного.
    """
    return Task.current_task()


def log_hyperparams(params: dict[str, Any], name: str = "General") -> None:
    """Логировать гиперпараметры в ClearML Task.

    Args:
        params: Словарь параметров для логирования.
        name: Название секции параметров.

    Example:
        >>> log_hyperparams({"learning_rate": 0.01, "n_estimators": 100})
    """
    task = Task.current_task()
    if task is None:
        return

    task.connect(params, name=name)


def log_metrics(
    metrics: dict[str, float],
    title: str = "Metrics",
    iteration: int = 0,
) -> None:
    """Логировать метрики в ClearML Task.

    Args:
        metrics: Словарь метрик для логирования.
        title: Заголовок группы метрик.
        iteration: Номер итерации.

    Example:
        >>> log_metrics({"accuracy": 0.95, "f1_score": 0.92})
    """
    task = Task.current_task()
    if task is None:
        return

    logger = task.get_logger()
    for name, value in metrics.items():
        logger.report_scalar(
            title=title,
            series=name,
            value=value,
            iteration=iteration,
        )


def log_artifact(
    artifact_path: str | Path,
    name: str | None = None,
    artifact_type: str = "file",
) -> None:
    """Загрузить артефакт в ClearML Task.

    Args:
        artifact_path: Путь к файлу артефакта.
        name: Имя артефакта (если None, используется имя файла).
        artifact_type: Тип артефакта.

    Example:
        >>> log_artifact("models/model.pkl", name="trained_model")
    """
    task = Task.current_task()
    if task is None:
        return

    artifact_path = Path(artifact_path)
    artifact_name = name or artifact_path.name

    task.upload_artifact(
        name=artifact_name,
        artifact_object=str(artifact_path),
    )


def log_plot(
    title: str,
    series: str,
    figure: Any,
    iteration: int = 0,
) -> None:
    """Логировать matplotlib figure в ClearML Task.

    Args:
        title: Заголовок графика.
        series: Название серии.
        figure: Matplotlib figure объект.
        iteration: Номер итерации.

    Example:
        >>> import matplotlib.pyplot as plt
        >>> fig, ax = plt.subplots()
        >>> ax.plot([1, 2, 3], [1, 4, 9])
        >>> log_plot("Training", "Loss Curve", fig)
    """
    task = Task.current_task()
    if task is None:
        return

    logger = task.get_logger()
    logger.report_matplotlib_figure(
        title=title,
        series=series,
        figure=figure,
        iteration=iteration,
    )


def set_tags(tags: list[str]) -> None:
    """Установить теги для ClearML Task.

    Args:
        tags: Список тегов.

    Example:
        >>> set_tags(["production", "v1.0", "random_forest"])
    """
    task = Task.current_task()
    if task is None:
        return

    task.add_tags(tags)


def log_model_info(
    model_class: str,
    config_name: str,
    description: str = "",
) -> None:
    """Логировать информацию о модели.

    Args:
        model_class: Класс модели (e.g., "RandomForestClassifier").
        config_name: Имя конфигурации.
        description: Описание модели.
    """
    task = Task.current_task()
    if task is None:
        return

    task.set_parameter("model_class", model_class)
    task.set_parameter("config_name", config_name)
    if description:
        task.set_parameter("description", description)
