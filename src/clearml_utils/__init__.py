"""Утилиты для работы с ClearML.

Модуль предоставляет обёртки и утилиты для интеграции ClearML
в ML-пайплайн проекта.
"""

from src.clearml_utils.decorators import clearml_task, log_time
from src.clearml_utils.model_utils import load_model, register_model
from src.clearml_utils.task_utils import (
    get_current_task,
    log_artifact,
    log_hyperparams,
    log_metrics,
    log_plot,
    set_tags,
)

__all__ = [
    "clearml_task",
    "log_time",
    "log_hyperparams",
    "log_metrics",
    "log_artifact",
    "log_plot",
    "set_tags",
    "get_current_task",
    "register_model",
    "load_model",
]
