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

import json
import logging
import sys
from pathlib import Path
from typing import Any

import click
import joblib
import pandas as pd
from clearml import PipelineController

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Название проекта
PROJECT_NAME = "titanic_classification"
PIPELINE_NAME = "Titanic ML Pipeline"


def step_prepare_data() -> dict[str, Any]:
    """Stage 1: Подготовка данных.

    Вызывает prepare_data() для подготовки сырых данных.

    Returns:
        Результат выполнения.
    """
    import logging

    from src.data.make_dataset import prepare_data

    _logger = logging.getLogger(__name__)
    _logger.info("Running step: prepare_data")

    input_path = Path("data/raw/titanic.csv")
    output_path = Path("data/processed/titanic_processed.csv")

    try:
        prepare_data(input_path, output_path)
        success = True
    except Exception as e:
        _logger.error(f"prepare_data failed: {e}")
        success = False

    result = {
        "success": success,
        "output_exists": output_path.exists(),
    }

    _logger.info(f"step_prepare_data completed: {result}")
    return result


def step_split_data() -> dict[str, Any]:
    """Stage 2: Разделение данных.

    Вызывает split_data() для разделения на train/val/test.

    Returns:
        Результат выполнения.
    """
    import logging

    from src.config.loader import load_pipeline_config
    from src.data.split_dataset import split_data

    _logger = logging.getLogger(__name__)
    _logger.info("Running step: split_data")

    try:
        config = load_pipeline_config(Path("configs/pipeline.yaml"))
        data = pd.read_csv("data/processed/titanic_processed.csv")

        train, val, test = split_data(
            data=data,
            train_size=config.data_split.train_size,
            val_size=config.data_split.val_size,
            test_size=config.data_split.test_size,
            random_state=config.data_split.random_state,
            stratify_column="Survived" if config.data_split.stratify else None,
        )

        Path("data/processed").mkdir(parents=True, exist_ok=True)
        train.to_csv("data/processed/train.csv", index=False)
        val.to_csv("data/processed/val.csv", index=False)
        test.to_csv("data/processed/test.csv", index=False)

        success = True
    except Exception as e:
        _logger.error(f"split_data failed: {e}")
        success = False

    result = {
        "success": success,
        "train_exists": Path("data/processed/train.csv").exists(),
        "val_exists": Path("data/processed/val.csv").exists(),
        "test_exists": Path("data/processed/test.csv").exists(),
    }

    _logger.info(f"step_split_data completed: {result}")
    return result


def step_feature_engineering() -> dict[str, Any]:
    """Stage 3: Feature Engineering.

    Вызывает apply_feature_scaling() для создания признаков.

    Returns:
        Результат выполнения.
    """
    import logging

    from src.features.build_features import apply_feature_scaling

    _logger = logging.getLogger(__name__)
    _logger.info("Running step: feature_engineering")

    try:
        train = pd.read_csv("data/processed/train.csv")
        val = pd.read_csv("data/processed/val.csv")
        test = pd.read_csv("data/processed/test.csv")

        train_scaled, val_scaled, test_scaled, _ = apply_feature_scaling(train, val, test)

        Path("data/features").mkdir(parents=True, exist_ok=True)
        train_scaled.to_csv("data/features/train_features.csv", index=False)
        val_scaled.to_csv("data/features/val_features.csv", index=False)
        test_scaled.to_csv("data/features/test_features.csv", index=False)

        success = True
    except Exception as e:
        _logger.error(f"feature_engineering failed: {e}")
        success = False

    result = {
        "success": success,
        "train_features_exists": Path("data/features/train_features.csv").exists(),
        "val_features_exists": Path("data/features/val_features.csv").exists(),
        "test_features_exists": Path("data/features/test_features.csv").exists(),
    }

    _logger.info(f"step_feature_engineering completed: {result}")
    return result


def step_validate_data() -> dict[str, Any]:
    """Stage 4: Валидация данных.

    Вызывает функции валидации для проверки качества данных.

    Returns:
        Результат выполнения.
    """
    import logging
    from pathlib import Path
    from typing import Any

    from src.config.loader import load_pipeline_config
    from src.data.validate_dataset import check_duplicates, check_missing_values, check_outliers

    _logger = logging.getLogger(__name__)
    _logger.info("Running step: validate_data")

    try:
        config = load_pipeline_config(Path("configs/pipeline.yaml")).data_validation

        train = pd.read_csv("data/processed/train.csv")
        val = pd.read_csv("data/processed/val.csv")
        test = pd.read_csv("data/processed/test.csv")

        report: dict[str, Any] = {"train": {}, "val": {}, "test": {}, "issues": [], "passed": True}

        for name, data in [("train", train), ("val", val), ("test", test)]:
            if config.check_missing:
                report[name]["missing"] = check_missing_values(data, config.max_missing_ratio)
            if config.check_duplicates:
                report[name]["duplicates"] = check_duplicates(data)
            if config.check_outliers:
                report[name]["outliers"] = check_outliers(data, config.outlier_std_threshold)

        with open("data/processed/validation_report.json", "w") as f:
            json.dump(report, f, indent=2)

        success = True
    except Exception as e:
        _logger.error(f"validate_data failed: {e}")
        success = False

    result = {
        "success": success,
        "report_exists": Path("data/processed/validation_report.json").exists(),
    }

    _logger.info(f"step_validate_data completed: {result}")
    return result


def step_train_model(config_name: str = "random_forest_medium") -> dict[str, Any]:
    """Stage 5: Обучение модели.

    Вызывает train_model_pipeline() для обучения ML модели.

    Args:
        config_name: Имя конфигурации модели.

    Returns:
        Результат выполнения.
    """
    import logging

    from src.models.train_model import train_model_pipeline

    _logger = logging.getLogger(__name__)
    _logger.info(f"Running step: train_model with config={config_name}")

    try:
        train_model_pipeline(
            train_data_path="data/features/train_features.csv",
            val_data_path="data/features/val_features.csv",
            model_output_path="models/model.pkl",
            config_name=config_name,
        )
        success = True
    except Exception as e:
        _logger.error(f"train_model failed: {e}")
        success = False

    result = {
        "success": success,
        "model_exists": Path("models/model.pkl").exists(),
        "metrics_exists": Path("models/metrics.json").exists(),
    }

    _logger.info(f"step_train_model completed: {result}")
    return result


def step_evaluate_model() -> dict[str, Any]:
    """Stage 6: Оценка модели.

    Вызывает evaluate_classifier() для оценки модели на test данных.

    Returns:
        Результат выполнения.
    """
    import logging
    from pathlib import Path

    import pandas as pd

    from src.clearml_utils import log_metrics
    from src.models.evaluate_model import evaluate_classifier

    _logger = logging.getLogger(__name__)
    _logger.info("Running step: evaluate_model")

    try:
        model = joblib.load("models/model.pkl")
        test = pd.read_csv("data/features/test_features.csv")

        x_test = test.drop("Survived", axis=1)
        y_test = test["Survived"]

        metrics = evaluate_classifier(model, x_test, y_test)

        # Логировать метрики test set в ClearML
        log_metrics(metrics, title="Test Set Metrics")
        _logger.info(f"Test metrics logged: {metrics}")

        Path("models").mkdir(parents=True, exist_ok=True)
        with open("models/evaluation_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

        success = True
    except Exception as e:
        _logger.error(f"evaluate_model failed: {e}")
        success = False

    result = {
        "success": success,
        "eval_metrics_exists": Path("models/evaluation_metrics.json").exists(),
    }

    _logger.info(f"step_evaluate_model completed: {result}")
    return result


def step_validate_model() -> dict[str, Any]:
    """Stage 7: Валидация модели.

    Вызывает validate_metrics() для финальной валидации модели.

    Returns:
        Результат выполнения.
    """
    import logging
    from pathlib import Path

    from src.config.loader import load_pipeline_config
    from src.models.validate_model import validate_metrics

    _logger = logging.getLogger(__name__)
    _logger.info("Running step: validate_model")

    try:
        config = load_pipeline_config(Path("configs/pipeline.yaml")).model_validation

        with open("models/evaluation_metrics.json") as f:
            metrics = json.load(f)

        validation_result = validate_metrics(
            metrics=metrics,
            min_accuracy=config.min_accuracy,
            min_f1_score=config.min_f1_score,
        )

        with open("models/model_validation_report.json", "w") as f:
            json.dump(validation_result, f, indent=2)

        success = True
    except Exception as e:
        _logger.error(f"validate_model failed: {e}")
        success = False

    result = {
        "success": success,
        "validation_report_exists": Path("models/model_validation_report.json").exists(),
    }

    _logger.info(f"step_validate_model completed: {result}")
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
    """Запустить пайплайн локально через PipelineController.start_locally().

    Использует ClearML PipelineController для запуска stages локально.
    Это позволяет ClearML построить DAG и отобразить его в UI.

    Args:
        config_name: Имя конфигурации модели.

    Returns:
        True если пайплайн успешно завершился.
    """
    logger.info(f"Starting local pipeline with config: {config_name}")

    try:
        # Создать и запустить pipeline через ClearML
        pipe = create_pipeline(config_name)

        # start_locally() выполняет все stages в текущем процессе
        # и создаёт DAG в ClearML UI
        pipe.start_locally(run_pipeline_steps_locally=True)

        logger.info("Pipeline completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}")
        return False


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
