"""Декораторы для автоматического логирования в ClearML."""

import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar, cast

from clearml import Task

F = TypeVar("F", bound=Callable[..., Any])


def clearml_task(
    project_name: str = "titanic_classification",
    task_name: str | None = None,
    task_type: str = "training",
    reuse_last_task_id: bool = False,
    auto_connect_frameworks: bool = True,
) -> Callable[[F], F]:
    """Декоратор для автоматического управления ClearML Task lifecycle.

    Args:
        project_name: Название проекта в ClearML.
        task_name: Название задачи. Если None, используется имя функции.
        task_type: Тип задачи (training, testing, inference, etc.).
        reuse_last_task_id: Использовать последний task_id (для debug).
        auto_connect_frameworks: Автоматически подключать фреймворки (matplotlib, etc.).

    Returns:
        Декорированная функция с автоматическим управлением ClearML Task.

    Example:
        >>> @clearml_task(project_name="my_project", task_name="train_rf")
        >>> def train_model(params):
        ...     # training code
        ...     return {"accuracy": 0.95}
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Определить имя задачи
            actual_task_name = task_name or func.__name__

            # Проверить, есть ли уже активный Task (например, от pipeline)
            existing_task = Task.current_task()
            owns_task = existing_task is None

            if owns_task:
                # Создать новый Task только если его нет
                task = Task.init(
                    project_name=project_name,
                    task_name=actual_task_name,
                    task_type=task_type,
                    reuse_last_task_id=reuse_last_task_id,
                    auto_connect_frameworks=auto_connect_frameworks,
                )
            else:
                # Использовать существующий Task (от pipeline)
                task = existing_task

            try:
                result = func(*args, **kwargs)
                if owns_task:
                    task.mark_completed()
                return result
            except Exception as e:
                if owns_task:
                    task.mark_failed()
                raise e
            finally:
                if owns_task:
                    task.close()

        return cast("F", wrapper)

    return decorator


def log_time[T: Callable[..., Any]](func: T) -> T:
    """Декоратор для автоматического логирования времени выполнения функции.

    Логирует метрику 'execution_time_seconds' в активный ClearML Task.

    Args:
        func: Функция для декорирования.

    Returns:
        Декорированная функция с логированием времени.

    Example:
        >>> @log_time
        >>> def train_model():
        ...     # training code
        ...     pass
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed_time = time.time() - start_time
            # Логировать только если есть активный Task
            task = Task.current_task()
            if task is not None:
                logger = task.get_logger()
                logger.report_scalar(
                    title="Timing",
                    series="execution_time_seconds",
                    value=elapsed_time,
                    iteration=0,
                )
            print(f"[{func.__name__}] Execution time: {elapsed_time:.2f}s")

    return cast("T", wrapper)
