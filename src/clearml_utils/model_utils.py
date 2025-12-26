"""Утилиты для работы с моделями в ClearML."""

from pathlib import Path
from typing import Any

import joblib
from clearml import InputModel, OutputModel, Task


def register_model(
    model: Any,
    model_path: str | Path,
    model_name: str = "titanic_classifier",
    framework: str = "scikit-learn",
    tags: list[str] | None = None,
) -> OutputModel | None:
    """Зарегистрировать модель в ClearML Model Registry.

    Args:
        model: Обученная модель для сохранения.
        model_path: Путь для сохранения модели на диск.
        model_name: Имя модели в реестре.
        framework: Фреймворк модели.
        tags: Теги для модели.

    Returns:
        OutputModel объект или None если нет активного Task.

    Example:
        >>> from sklearn.ensemble import RandomForestClassifier
        >>> model = RandomForestClassifier()
        >>> model.fit(X_train, y_train)
        >>> output_model = register_model(model, "models/model.pkl")
    """
    task = Task.current_task()
    if task is None:
        return None

    # Сохранить модель на диск
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)

    # Создать OutputModel
    output_model = OutputModel(
        task=task,
        name=model_name,
        framework=framework,
        tags=tags or [],
    )

    # Загрузить веса модели
    output_model.update_weights(
        weights_filename=str(model_path),
        auto_delete_file=False,
    )

    return output_model


def load_model(
    model_id: str | None = None,
    model_name: str | None = None,
    project_name: str = "titanic_classification",
    tags: list[str] | None = None,
) -> Any:
    """Загрузить модель из ClearML Model Registry.

    Args:
        model_id: ID модели в ClearML (приоритет).
        model_name: Имя модели для поиска.
        project_name: Название проекта для поиска.
        tags: Теги для фильтрации моделей.

    Returns:
        Загруженная модель.

    Raises:
        ValueError: Если модель не найдена.

    Example:
        >>> model = load_model(model_id="abc123")
        >>> # или
        >>> model = load_model(model_name="titanic_classifier", tags=["production"])
    """
    if model_id:
        # Загрузить по ID
        input_model = InputModel(model_id=model_id)
    elif model_name:
        # Найти модель по имени
        models = InputModel.query_models(
            project_name=project_name,
            model_name=model_name,
            tags=tags or [],
        )
        if not models:
            raise ValueError(f"Model '{model_name}' not found in project '{project_name}'")
        # Взять последнюю модель
        input_model = InputModel(model_id=models[0].id)
    else:
        raise ValueError("Either model_id or model_name must be provided")

    # Скачать и загрузить модель
    local_path = input_model.get_local_copy()
    return joblib.load(local_path)


def get_best_model(
    project_name: str = "titanic_classification",
    metric_name: str = "accuracy",
    metric_title: str = "Metrics",
    higher_is_better: bool = True,
) -> tuple[str, float]:
    """Найти лучшую модель по метрике.

    Args:
        project_name: Название проекта.
        metric_name: Название метрики.
        metric_title: Заголовок группы метрик.
        higher_is_better: True если большее значение лучше.

    Returns:
        Tuple (task_id, metric_value) лучшей модели.

    Raises:
        ValueError: Если нет завершённых задач.

    Example:
        >>> task_id, accuracy = get_best_model(metric_name="accuracy")
        >>> print(f"Best model: {task_id} with accuracy {accuracy:.4f}")
    """
    # Получить все завершённые задачи проекта
    tasks = Task.get_tasks(
        project_name=project_name,
        task_filter={"status": ["completed"]},
    )

    if not tasks:
        raise ValueError(f"No completed tasks in project '{project_name}'")

    best_task_id = None
    best_value = float("-inf") if higher_is_better else float("inf")

    for task in tasks:
        # Получить метрики задачи
        scalars = task.get_reported_scalars()
        if metric_title in scalars and metric_name in scalars[metric_title]:
            values = scalars[metric_title][metric_name]["y"]
            if values:
                value = values[-1]  # Последнее значение
                if (
                    higher_is_better
                    and value > best_value
                    or not higher_is_better
                    and value < best_value
                ):
                    best_value = value
                    best_task_id = task.id

    if best_task_id is None:
        raise ValueError(f"Metric '{metric_name}' not found in any task")

    return best_task_id, float(best_value)
