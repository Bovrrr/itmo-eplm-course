"""Валидация качества обученной модели."""

import json
from pathlib import Path
from typing import Any

import click

from src.config.loader import load_pipeline_config
from src.utils.notifications import (
    notify_error,
    notify_info,
    notify_success,
    notify_warning,
    stage_notification,
)


def validate_metrics(
    metrics: dict[str, float],
    min_accuracy: float,
    min_f1_score: float,
) -> dict[str, Any]:
    """Валидировать метрики модели.

    Args:
        metrics: Словарь с метриками модели
        min_accuracy: Минимальная допустимая accuracy
        min_f1_score: Минимальный допустимый F1-score

    Returns:
        Словарь с результатами валидации
    """
    result: dict[str, Any] = {
        "checks": [],
        "passed": True,
    }

    # Проверка accuracy
    accuracy_check = {
        "name": "accuracy_threshold",
        "actual": metrics.get("accuracy", 0.0),
        "threshold": min_accuracy,
        "passed": metrics.get("accuracy", 0.0) >= min_accuracy,
    }
    result["checks"].append(accuracy_check)

    if not accuracy_check["passed"]:
        result["passed"] = False
        notify_warning(
            f"Accuracy {accuracy_check['actual']:.4f} below threshold {min_accuracy:.4f}"
        )

    # Проверка F1-score
    f1_check = {
        "name": "f1_score_threshold",
        "actual": metrics.get("f1_score", 0.0),
        "threshold": min_f1_score,
        "passed": metrics.get("f1_score", 0.0) >= min_f1_score,
    }
    result["checks"].append(f1_check)

    if not f1_check["passed"]:
        result["passed"] = False
        notify_warning(f"F1-score {f1_check['actual']:.4f} below threshold {min_f1_score:.4f}")

    return result


@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    default="configs/pipeline.yaml",
    help="Path to pipeline configuration file",
)
@click.option(
    "--metrics-path",
    type=click.Path(exists=True, path_type=Path),
    default="models/evaluation_metrics.json",
    help="Path to evaluation metrics",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default="models",
    help="Directory to save validation report",
)
def main(config: Path, metrics_path: Path, output_dir: Path) -> None:
    """Валидировать качество обученной модели.

    Проверяет соответствие метрик заданным thresholds.
    """
    with stage_notification("Model Validation"):
        # Загрузить конфигурацию
        notify_info(f"Loading pipeline config from {config}")
        pipeline_config = load_pipeline_config(config)
        validation_config = pipeline_config.model_validation

        # Загрузить метрики
        notify_info(f"Loading evaluation metrics from {metrics_path}")
        with metrics_path.open() as f:
            metrics = json.load(f)
        notify_success("Loaded evaluation metrics")

        # Валидация метрик
        notify_info("Validating model metrics...")
        validation_result = validate_metrics(
            metrics=metrics,
            min_accuracy=validation_config.min_accuracy,
            min_f1_score=validation_config.min_f1_score,
        )

        # Сохранить отчёт
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "model_validation_report.json"
        with report_path.open("w") as f:
            json.dump(validation_result, f, indent=2)
        notify_success(f"Saved validation report: {report_path}")

        # Вывести результаты
        for check in validation_result["checks"]:
            status = "✓" if check["passed"] else "✗"
            notify_info(
                f"{status} {check['name']}: {check['actual']:.4f} "
                f"(threshold: {check['threshold']:.4f})"
            )

        # Итоговое сообщение
        if validation_result["passed"]:
            notify_success("✓ All validation checks passed!")
        else:
            notify_error("✗ Model validation failed - some checks did not pass")
            failed_checks = [c["name"] for c in validation_result["checks"] if not c["passed"]]
            notify_error(f"Failed checks: {', '.join(failed_checks)}")


if __name__ == "__main__":
    main()
