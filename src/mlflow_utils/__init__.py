"""MLflow utilities module.

Этот модуль предоставляет набор утилит для упрощения работы с MLflow:
- Декораторы для автоматического логирования
- Контекстные менеджеры для управления lifecycle
- Функции анализа экспериментов
"""

from .analysis import (
    compare_runs,
    export_runs_to_dataframe,
    get_best_run,
    get_experiment_summary,
    plot_metrics_comparison,
    plot_metrics_heatmap,
)
from .context_managers import (
    ArtifactLoggingContext,
    ExperimentContext,
    MlflowRunContext,
)
from .decorators import log_params_and_metrics, log_time, mlflow_run

__version__ = "0.1.0"

__all__ = [
    # Decorators
    "mlflow_run",
    "log_time",
    "log_params_and_metrics",
    # Context managers
    "MlflowRunContext",
    "ExperimentContext",
    "ArtifactLoggingContext",
    # Analysis functions
    "get_best_run",
    "compare_runs",
    "get_experiment_summary",
    "export_runs_to_dataframe",
    "plot_metrics_comparison",
    "plot_metrics_heatmap",
]
