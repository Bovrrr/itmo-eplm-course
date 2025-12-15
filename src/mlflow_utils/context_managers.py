"""Контекстные менеджеры для работы с MLflow."""

from types import TracebackType
from typing import Literal

import mlflow
from mlflow.entities import Run


class MlflowRunContext:
    """Контекстный менеджер для управления жизненным циклом MLflow run.

    Автоматически создаёт run при входе в контекст и завершает при выходе.
    Обрабатывает исключения и гарантирует корректное завершение run.

    Args:
        experiment_name: Название эксперимента. Если None, используется текущий.
        run_name: Название run. Если None, генерируется автоматически.
        nested: Создать вложенный run (если уже есть активный run).
        tags: Словарь тегов для run.

    Example:
        >>> with MlflowRunContext(experiment_name="test", run_name="my_run") as run:
        >>>     mlflow.log_param("key", "value")
        >>>     mlflow.log_metric("accuracy", 0.95)
    """

    def __init__(
        self,
        experiment_name: str | None = None,
        run_name: str | None = None,
        nested: bool = False,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Инициализация контекстного менеджера."""
        self.experiment_name = experiment_name
        self.run_name = run_name
        self.nested = nested
        self.tags = tags or {}
        self.run: Run | None = None

    def __enter__(self) -> Run:
        """Вход в контекст - создание MLflow run."""
        # Установить эксперимент если указан
        if self.experiment_name is not None:
            mlflow.set_experiment(self.experiment_name)

        # Создать run
        self.run = mlflow.start_run(run_name=self.run_name, nested=self.nested)

        # Установить теги
        if self.tags:
            mlflow.set_tags(self.tags)

        return self.run

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Выход из контекста - завершение MLflow run.

        Args:
            exc_type: Тип исключения (если было).
            exc_val: Значение исключения (если было).
            exc_tb: Traceback исключения (если было).

        Returns:
            False - исключения не подавляются.
        """
        # Если было исключение, пометить run как failed
        if exc_type is not None and mlflow.active_run() is not None:
            mlflow.set_tag("status", "failed")
            mlflow.set_tag("error_type", exc_type.__name__)
            if exc_val is not None:
                mlflow.set_tag("error_message", str(exc_val))

        # Завершить run
        mlflow.end_run()

        # Не подавлять исключения
        return False


class ExperimentContext:
    """Контекстный менеджер для временного переключения эксперимента.

    Автоматически возвращает предыдущий эксперимент при выходе из контекста.

    Args:
        experiment_name: Название эксперимента для переключения.

    Example:
        >>> with ExperimentContext("temporary_experiment"):
        >>>     # Здесь работаем с temporary_experiment
        >>>     mlflow.start_run()
        >>>     mlflow.log_param("test", 1)
        >>>     mlflow.end_run()
        >>> # Здесь вернулись к предыдущему эксперименту
    """

    def __init__(self, experiment_name: str) -> None:
        """Инициализация контекстного менеджера."""
        self.experiment_name = experiment_name
        self.previous_experiment_id: str | None = None

    def __enter__(self) -> None:
        """Вход в контекст - переключение на новый эксперимент."""
        # Сохранить ID текущего эксперимента
        active_run = mlflow.active_run()
        if active_run is not None:
            self.previous_experiment_id = active_run.info.experiment_id
        else:
            # Получить текущий эксперимент через поиск
            try:
                current_exp = mlflow.get_experiment_by_name(mlflow.get_tracking_uri())
                if current_exp is not None:
                    self.previous_experiment_id = current_exp.experiment_id
            except Exception:
                # Если не удалось получить, оставляем None
                pass

        # Переключиться на новый эксперимент
        mlflow.set_experiment(self.experiment_name)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Выход из контекста - возврат к предыдущему эксперименту."""
        # Вернуться к предыдущему эксперименту если был
        if self.previous_experiment_id is not None:
            try:
                experiment = mlflow.get_experiment(self.previous_experiment_id)
                if experiment is not None:
                    mlflow.set_experiment(experiment.name)
            except Exception:
                # Если не удалось восстановить, игнорируем
                pass

        return False


class ArtifactLoggingContext:
    """Контекстный менеджер для пакетного логирования артефактов.

    Собирает пути к артефактам во время выполнения и логирует их все
    при выходе из контекста.

    Args:
        artifact_path: Путь в MLflow для сохранения артефактов.

    Example:
        >>> with ArtifactLoggingContext(artifact_path="plots") as ctx:
        >>>     # Создаём файлы
        >>>     plt.savefig("plot1.png")
        >>>     ctx.add_artifact("plot1.png")
        >>>     plt.savefig("plot2.png")
        >>>     ctx.add_artifact("plot2.png")
        >>> # Все файлы залогированы автоматически
    """

    def __init__(self, artifact_path: str | None = None) -> None:
        """Инициализация контекстного менеджера."""
        self.artifact_path = artifact_path
        self.artifacts: list[str] = []

    def add_artifact(self, local_path: str) -> None:
        """Добавить артефакт для логирования.

        Args:
            local_path: Локальный путь к файлу артефакта.
        """
        self.artifacts.append(local_path)

    def __enter__(self) -> "ArtifactLoggingContext":
        """Вход в контекст."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Выход из контекста - логирование всех собранных артефактов."""
        # Логировать только если есть активный run и нет исключений
        if exc_type is None and mlflow.active_run() is not None:
            for artifact_path in self.artifacts:
                try:
                    mlflow.log_artifact(artifact_path, self.artifact_path)
                except Exception as e:
                    print(f"Warning: Failed to log artifact {artifact_path}: {e}")

        return False
