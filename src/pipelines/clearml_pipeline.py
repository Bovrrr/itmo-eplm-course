"""ClearML Pipeline для ML-проекта Titanic.

Этот модуль реализует полный ML пайплайн с использованием ClearML PipelineController.
Pipeline состоит из 7 stages, аналогично DVC pipeline:

1. prepare_data    - Подготовка данных
2. split_data      - Разделение на train/val/test
3. feature_eng     - Feature engineering (параллельно с validate_data)
4. validate_data   - Валидация данных (параллельно с feature_eng)
5. train_model     - Обучение модели
6. evaluate_model  - Оценка модели
7. validate_model  - Валидация модели

Пример использования:
    uv run python -m src.pipelines.clearml_pipeline --local
    uv run python -m src.pipelines.clearml_pipeline --config random_forest_medium
"""

import logging
import os
import shutil
import subprocess  # nosec B404 - subprocess is used for running pipeline stages
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

import click
from clearml import PipelineController, Task

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Название проекта
PROJECT_NAME = "titanic_classification"
PIPELINE_NAME = "Titanic ML Pipeline"


def get_python_cmd() -> str:
    """Определить команду для запуска python.

    В Docker контейнере uv недоступен, поэтому используем python напрямую.
    Локально используем uv run python.

    Returns:
        Команда для запуска python скриптов.
    """
    # Проверяем, находимся ли мы в Docker (uv недоступен)
    if shutil.which("uv") is None:
        return "python"
    # Проверяем переменную окружения для явного указания режима
    if os.environ.get("IN_DOCKER", "").lower() in ("1", "true", "yes"):
        return "python"
    return "uv run python"


def run_command(cmd: str) -> dict[str, Any]:
    """Выполнить shell команду и вернуть результат.

    Args:
        cmd: Shell команда для выполнения.

    Returns:
        Словарь с результатами выполнения.
    """
    logger.info(f"Running: {cmd}")
    result = subprocess.run(  # nosec B602 - shell commands are internal, not user input
        cmd,
        check=False,
        shell=True,
        capture_output=True,
        text=True,
    )

    output = {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": result.returncode == 0,
    }

    if result.returncode != 0:
        logger.error(f"Command failed: {result.stderr}")
    else:
        logger.info("Command completed successfully")

    return output


def step_prepare_data() -> dict[str, Any]:
    """Stage 1: Подготовка данных.

    Запускает make_dataset.py для подготовки сырых данных.

    Returns:
        Результат выполнения.
    """
    task = Task.current_task()
    if task:
        task.set_parameter("stage", "prepare_data")

    python_cmd = get_python_cmd()
    cmd = f"{python_cmd} -m src.data.make_dataset"
    result = run_command(cmd)

    # Проверить что файл создан
    output_file = Path("data/processed/titanic_processed.csv")
    result["output_exists"] = output_file.exists()

    if task:
        task.get_logger().report_scalar(
            title="Stage Status",
            series="prepare_data",
            value=1 if result["success"] else 0,
            iteration=0,
        )

    return result


def step_split_data() -> dict[str, Any]:
    """Stage 2: Разделение данных.

    Запускает split_dataset.py для разделения на train/val/test.

    Returns:
        Результат выполнения.
    """
    task = Task.current_task()
    if task:
        task.set_parameter("stage", "split_data")

    python_cmd = get_python_cmd()
    cmd = f"{python_cmd} -m src.data.split_dataset --config configs/pipeline.yaml"
    result = run_command(cmd)

    # Проверить что файлы созданы
    result["train_exists"] = Path("data/processed/train.csv").exists()
    result["val_exists"] = Path("data/processed/val.csv").exists()
    result["test_exists"] = Path("data/processed/test.csv").exists()

    if task:
        task.get_logger().report_scalar(
            title="Stage Status",
            series="split_data",
            value=1 if result["success"] else 0,
            iteration=0,
        )

    return result


def step_feature_engineering() -> dict[str, Any]:
    """Stage 3: Feature Engineering.

    Запускает build_features.py для создания признаков.

    Returns:
        Результат выполнения.
    """
    task = Task.current_task()
    if task:
        task.set_parameter("stage", "feature_engineering")

    python_cmd = get_python_cmd()
    cmd = f"{python_cmd} -m src.features.build_features --config configs/pipeline.yaml --data-dir data/processed"
    result = run_command(cmd)

    # Проверить что файлы созданы
    result["train_features_exists"] = Path("data/features/train_features.csv").exists()
    result["val_features_exists"] = Path("data/features/val_features.csv").exists()
    result["test_features_exists"] = Path("data/features/test_features.csv").exists()

    if task:
        task.get_logger().report_scalar(
            title="Stage Status",
            series="feature_engineering",
            value=1 if result["success"] else 0,
            iteration=0,
        )

    return result


def step_validate_data() -> dict[str, Any]:
    """Stage 4: Валидация данных.

    Запускает validate_dataset.py для проверки качества данных.

    Returns:
        Результат выполнения.
    """
    task = Task.current_task()
    if task:
        task.set_parameter("stage", "validate_data")

    python_cmd = get_python_cmd()
    cmd = f"{python_cmd} -m src.data.validate_dataset --config configs/pipeline.yaml"
    result = run_command(cmd)

    # Проверить что отчёт создан
    result["report_exists"] = Path("data/processed/validation_report.json").exists()

    if task:
        task.get_logger().report_scalar(
            title="Stage Status",
            series="validate_data",
            value=1 if result["success"] else 0,
            iteration=0,
        )

    return result


def step_train_model(config_name: str = "random_forest_medium") -> dict[str, Any]:
    """Stage 5: Обучение модели.

    Запускает train_model.py для обучения ML модели.

    Args:
        config_name: Имя конфигурации модели.

    Returns:
        Результат выполнения.
    """
    task = Task.current_task()
    if task:
        task.set_parameter("stage", "train_model")
        task.set_parameter("model_config", config_name)

    python_cmd = get_python_cmd()
    cmd = f"{python_cmd} src/models/train_model.py {config_name}"
    result = run_command(cmd)

    # Проверить что модель создана
    result["model_exists"] = Path("models/model.pkl").exists()
    result["metrics_exists"] = Path("models/metrics.json").exists()

    if task:
        task.get_logger().report_scalar(
            title="Stage Status",
            series="train_model",
            value=1 if result["success"] else 0,
            iteration=0,
        )

    return result


def step_evaluate_model() -> dict[str, Any]:
    """Stage 6: Оценка модели.

    Запускает evaluate_model.py для оценки модели на test данных.

    Returns:
        Результат выполнения.
    """
    task = Task.current_task()
    if task:
        task.set_parameter("stage", "evaluate_model")

    python_cmd = get_python_cmd()
    cmd = f"{python_cmd} -m src.models.evaluate_model --config configs/pipeline.yaml"
    result = run_command(cmd)

    # Проверить что метрики созданы
    result["eval_metrics_exists"] = Path("models/evaluation_metrics.json").exists()

    if task:
        task.get_logger().report_scalar(
            title="Stage Status",
            series="evaluate_model",
            value=1 if result["success"] else 0,
            iteration=0,
        )

    return result


def step_validate_model() -> dict[str, Any]:
    """Stage 7: Валидация модели.

    Запускает validate_model.py для финальной валидации модели.

    Returns:
        Результат выполнения.
    """
    task = Task.current_task()
    if task:
        task.set_parameter("stage", "validate_model")

    python_cmd = get_python_cmd()
    cmd = f"{python_cmd} -m src.models.validate_model --config configs/pipeline.yaml"
    result = run_command(cmd)

    # Проверить что отчёт создан
    result["validation_report_exists"] = Path("models/model_validation_report.json").exists()

    if task:
        task.get_logger().report_scalar(
            title="Stage Status",
            series="validate_model",
            value=1 if result["success"] else 0,
            iteration=0,
        )

    return result


def create_pipeline(config_name: str = "random_forest_medium") -> PipelineController:
    """Создать ClearML Pipeline.

    Args:
        config_name: Имя конфигурации модели.

    Returns:
        Настроенный PipelineController.
    """
    # Создать контроллер пайплайна
    pipe = PipelineController(
        name=PIPELINE_NAME,
        project=PROJECT_NAME,
        version="1.0",
        add_pipeline_tags=True,
    )

    # Добавить параметры пайплайна
    pipe.add_parameter(
        name="model_config",
        default=config_name,
        description="Конфигурация модели для обучения",
    )

    # Stage 1: Prepare Data
    pipe.add_function_step(
        name="prepare_data",
        function=step_prepare_data,
        function_return=["prepare_result"],
        cache_executed_step=True,
    )

    # Stage 2: Split Data (зависит от prepare_data)
    pipe.add_function_step(
        name="split_data",
        function=step_split_data,
        function_return=["split_result"],
        parents=["prepare_data"],
        cache_executed_step=True,
    )

    # Stage 3: Feature Engineering (зависит от split_data)
    pipe.add_function_step(
        name="feature_engineering",
        function=step_feature_engineering,
        function_return=["feature_result"],
        parents=["split_data"],
        cache_executed_step=True,
    )

    # Stage 4: Validate Data (параллельно с feature_engineering)
    pipe.add_function_step(
        name="validate_data",
        function=step_validate_data,
        function_return=["validate_data_result"],
        parents=["split_data"],
        cache_executed_step=True,
    )

    # Stage 5: Train Model (зависит от feature_engineering и validate_data)
    pipe.add_function_step(
        name="train_model",
        function=step_train_model,
        function_kwargs={"config_name": "${pipeline.model_config}"},
        function_return=["train_result"],
        parents=["feature_engineering", "validate_data"],
        cache_executed_step=False,  # Не кэшировать обучение
    )

    # Stage 6: Evaluate Model (зависит от train_model)
    pipe.add_function_step(
        name="evaluate_model",
        function=step_evaluate_model,
        function_return=["evaluate_result"],
        parents=["train_model"],
        cache_executed_step=False,
    )

    # Stage 7: Validate Model (зависит от evaluate_model)
    pipe.add_function_step(
        name="validate_model",
        function=step_validate_model,
        function_return=["validate_model_result"],
        parents=["evaluate_model"],
        cache_executed_step=False,
    )

    return pipe


def run_pipeline_local(config_name: str = "random_forest_medium") -> bool:
    """Запустить пайплайн локально (без ClearML Agent).

    Args:
        config_name: Имя конфигурации модели.

    Returns:
        True если пайплайн успешно завершился.
    """
    logger.info(f"Starting local pipeline with config: {config_name}")

    # Создать Task для отслеживания
    task = Task.init(
        project_name=PROJECT_NAME,
        task_name=f"Pipeline: {config_name}",
        task_type=Task.TaskTypes.controller,
    )

    try:
        # Выполнить все stages последовательно
        stages: list[tuple[str, Callable[..., dict[str, Any]], dict[str, Any]]] = [
            ("prepare_data", step_prepare_data, {}),
            ("split_data", step_split_data, {}),
            ("feature_engineering", step_feature_engineering, {}),
            ("validate_data", step_validate_data, {}),
            ("train_model", step_train_model, {"config_name": config_name}),
            ("evaluate_model", step_evaluate_model, {}),
            ("validate_model", step_validate_model, {}),
        ]

        all_success = True
        for stage_name, stage_func, stage_kwargs in stages:
            logger.info(f"Running stage: {stage_name}")
            result = stage_func(**stage_kwargs)

            if not result.get("success", False):
                logger.error(f"Stage {stage_name} failed!")
                all_success = False
                break

            logger.info(f"Stage {stage_name} completed successfully")

        if all_success:
            task.mark_completed()
            logger.info("Pipeline completed successfully!")
        else:
            task.mark_failed()
            logger.error("Pipeline failed!")

        return all_success

    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}")
        task.mark_failed()
        return False

    finally:
        task.close()


@click.command()  # type: ignore[untyped-decorator]
@click.option(  # type: ignore[untyped-decorator]
    "--config",
    default="random_forest_medium",
    help="Конфигурация модели для обучения",
)
@click.option(  # type: ignore[untyped-decorator]
    "--local/--remote",
    default=True,
    help="Запустить локально или через ClearML Agent",
)
@click.option(  # type: ignore[untyped-decorator]
    "--queue",
    default="default",
    help="Очередь ClearML для удалённого запуска",
)
def main(config: str, local: bool, queue: str) -> None:
    """Запустить ClearML Pipeline.

    Example:
        # Локальный запуск
        $ python -m src.pipelines.clearml_pipeline --local

        # Удалённый запуск через ClearML Agent
        $ python -m src.pipelines.clearml_pipeline --remote --queue default
    """
    logger.info(f"Starting pipeline with config: {config}")
    logger.info(f"Local mode: {local}")

    if local:
        # Локальный запуск
        success = run_pipeline_local(config)
        sys.exit(0 if success else 1)
    else:
        # Создать и запустить пайплайн через ClearML
        pipe = create_pipeline(config)

        # Установить параметры
        pipe.set_default_execution_queue(queue)

        # Запустить пайплайн
        logger.info(f"Enqueuing pipeline to queue: {queue}")
        pipe.start(queue=queue)

        logger.info("Pipeline started. Check ClearML UI for progress.")
        logger.info(f"Pipeline ID: {pipe.pipeline_task.id}")


if __name__ == "__main__":
    main()
