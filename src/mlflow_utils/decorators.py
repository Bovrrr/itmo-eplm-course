"""Декораторы для автоматического логирования в MLflow."""

import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar, cast

import mlflow

F = TypeVar("F", bound=Callable[..., Any])


def mlflow_run(
    experiment_name: str | None = None,
    run_name: str | None = None,
    nested: bool = False,
) -> Callable[[F], F]:
    """Декоратор для автоматического управления MLflow run lifecycle.

    Args:
        experiment_name: Название эксперимента. Если None, используется текущий.
        run_name: Название run. Если None, генерируется автоматически.
        nested: Создать вложенный run (если уже есть активный run).

    Returns:
        Декорированная функция с автоматическим управлением MLflow run.

    Example:
        >>> @mlflow_run(experiment_name="my_exp", run_name="test_run")
        >>> def train_model(params):
        >>>     mlflow.log_param("learning_rate", 0.01)
        >>>     return {"accuracy": 0.95}
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Установить эксперимент если указан
            if experiment_name is not None:
                mlflow.set_experiment(experiment_name)

            # Создать run
            with mlflow.start_run(run_name=run_name, nested=nested):
                result = func(*args, **kwargs)
            return result

        return cast("F", wrapper)

    return decorator


def log_time[F: Callable[..., Any]](func: F) -> F:
    """Декоратор для автоматического логирования времени выполнения функции.

    Логирует метрику 'execution_time_seconds' в активный MLflow run.

    Args:
        func: Функция для декорирования.

    Returns:
        Декорированная функция с логированием времени.

    Example:
        >>> @log_time
        >>> def train_model():
        >>>     # training code
        >>>     pass
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed_time = time.time() - start_time
            # Логировать только если есть активный run
            if mlflow.active_run() is not None:
                mlflow.log_metric("execution_time_seconds", elapsed_time)
            print(f"[{func.__name__}] Execution time: {elapsed_time:.2f}s")

    return cast("F", wrapper)


def log_params_and_metrics(
    params: dict[str, Any] | None = None,
    metrics: dict[str, float] | None = None,
) -> Callable[[F], F]:
    """Декоратор для автоматического логирования параметров и метрик.

    Args:
        params: Словарь параметров для логирования перед выполнением функции.
        metrics: Словарь метрик для логирования после выполнения функции.

    Returns:
        Декорированная функция с автоматическим логированием.

    Example:
        >>> @log_params_and_metrics(
        >>>     params={"model_type": "rf"},
        >>>     metrics={"train_accuracy": 0.95}
        >>> )
        >>> def train_model():
        >>>     return {"accuracy": 0.95}
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Логировать параметры перед выполнением
            if params and mlflow.active_run() is not None:
                for key, value in params.items():
                    mlflow.log_param(key, value)

            # Выполнить функцию
            result = func(*args, **kwargs)

            # Логировать метрики после выполнения
            if metrics and mlflow.active_run() is not None:
                for key, value in metrics.items():
                    mlflow.log_metric(key, value)

            return result

        return cast("F", wrapper)

    return decorator
