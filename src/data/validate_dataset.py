"""Валидация качества данных (train/val/test)."""

import json
from pathlib import Path
from typing import Any

import click
import pandas as pd

from src.config.loader import load_pipeline_config
from src.utils.notifications import (
    notify_error,
    notify_info,
    notify_success,
    notify_warning,
    stage_notification,
)


def check_missing_values(data: pd.DataFrame, max_ratio: float) -> dict[str, Any]:
    """Проверить пропущенные значения.

    Args:
        data: DataFrame для проверки
        max_ratio: Максимальная допустимая доля пропусков (0.0-1.0)

    Returns:
        Словарь с информацией о пропусках
    """
    missing = data.isnull().sum()
    missing_ratio = missing / len(data)

    result: dict[str, Any] = {
        "total_missing": int(missing.sum()),
        "columns_with_missing": {},
        "issues": [],
    }

    for col, count in missing.items():
        if count > 0:
            ratio = missing_ratio[col]
            result["columns_with_missing"][col] = {
                "count": int(count),
                "ratio": float(ratio),
            }

            if ratio > max_ratio:
                issue = f"Column '{col}' has {ratio:.2%} missing values (max: {max_ratio:.2%})"
                result["issues"].append(issue)
                notify_warning(issue)

    return result


def check_duplicates(data: pd.DataFrame) -> dict[str, Any]:
    """Проверить дубликаты.

    Args:
        data: DataFrame для проверки

    Returns:
        Словарь с информацией о дубликатах
    """
    duplicates = data.duplicated().sum()

    result: dict[str, Any] = {
        "total_duplicates": int(duplicates),
        "duplicate_ratio": float(duplicates / len(data)),
        "issues": [],
    }

    if duplicates > 0:
        issue = f"Found {duplicates} duplicate rows ({duplicates / len(data):.2%})"
        result["issues"].append(issue)
        notify_warning(issue)

    return result


def check_outliers(data: pd.DataFrame, std_threshold: float) -> dict[str, Any]:
    """Детектировать выбросы методом IQR.

    Args:
        data: DataFrame для проверки
        std_threshold: Порог для детекции выбросов (в std)

    Returns:
        Словарь с информацией о выбросах
    """
    numeric_cols = data.select_dtypes(include=["number"]).columns
    result: dict[str, Any] = {
        "outliers_by_column": {},
        "total_outlier_rows": 0,
        "issues": [],
    }

    for col in numeric_cols:
        q1 = data[col].quantile(0.25)
        q3 = data[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - std_threshold * iqr
        upper_bound = q3 + std_threshold * iqr

        outliers = ((data[col] < lower_bound) | (data[col] > upper_bound)).sum()

        if outliers > 0:
            outlier_ratio = outliers / len(data)
            result["outliers_by_column"][col] = {
                "count": int(outliers),
                "ratio": float(outlier_ratio),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
            }

            if outlier_ratio > 0.05:  # Предупреждение если > 5%
                issue = f"Column '{col}' has {outlier_ratio:.2%} outliers"
                result["issues"].append(issue)
                notify_warning(issue)

    # Подсчитать общее количество строк с хотя бы одним выбросом
    outlier_mask = pd.Series([False] * len(data))
    for col in result["outliers_by_column"]:
        q1 = data[col].quantile(0.25)
        q3 = data[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - std_threshold * iqr
        upper_bound = q3 + std_threshold * iqr
        outlier_mask |= (data[col] < lower_bound) | (data[col] > upper_bound)

    result["total_outlier_rows"] = int(outlier_mask.sum())

    return result


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default="data/processed",
    help="Directory with train/val/test datasets",
)
def main(data_dir: Path) -> None:
    """Валидировать качество данных (train/val/test).

    Проверяет:
    - Пропущенные значения
    - Дубликаты
    - Выбросы (outliers)

    Сохраняет отчёт в validation_report.json.
    """
    with stage_notification("Data Validation"):
        # Загрузить конфигурацию через Hydra
        pipeline_config = load_pipeline_config()
        validation_config = pipeline_config.data_validation

        # Загрузить datasets
        train_path = data_dir / "train.csv"
        val_path = data_dir / "val.csv"
        test_path = data_dir / "test.csv"

        notify_info("Loading datasets...")
        train = pd.read_csv(train_path)
        val = pd.read_csv(val_path)
        test = pd.read_csv(test_path)
        notify_success(
            f"Loaded train: {len(train)} rows, val: {len(val)} rows, test: {len(test)} rows"
        )

        # Валидация
        report: dict[str, Any] = {
            "train": {},
            "val": {},
            "test": {},
            "issues": [],
            "passed": True,
        }

        for name, data in [("train", train), ("val", val), ("test", test)]:
            notify_info(f"Validating {name} dataset...")

            dataset_report: dict[str, Any] = {}

            # Проверка missing values
            if validation_config.check_missing:
                missing_result = check_missing_values(data, validation_config.max_missing_ratio)
                dataset_report["missing_values"] = missing_result
                report["issues"].extend([f"[{name}] {issue}" for issue in missing_result["issues"]])

            # Проверка дубликатов
            if validation_config.check_duplicates:
                duplicates_result = check_duplicates(data)
                dataset_report["duplicates"] = duplicates_result
                report["issues"].extend(
                    [f"[{name}] {issue}" for issue in duplicates_result["issues"]]
                )

            # Проверка outliers
            if validation_config.check_outliers:
                outliers_result = check_outliers(data, validation_config.outlier_std_threshold)
                dataset_report["outliers"] = outliers_result
                report["issues"].extend(
                    [f"[{name}] {issue}" for issue in outliers_result["issues"]]
                )

            report[name] = dataset_report

            # Сводка для dataset
            notify_success(
                f"{name}: {dataset_report.get('missing_values', {}).get('total_missing', 0)} missing, "
                f"{dataset_report.get('duplicates', {}).get('total_duplicates', 0)} duplicates, "
                f"{dataset_report.get('outliers', {}).get('total_outlier_rows', 0)} outlier rows"
            )

        # Определить статус прохождения
        report["passed"] = len(report["issues"]) == 0

        # Сохранить отчёт
        output_path = data_dir / "validation_report.json"
        with output_path.open("w") as f:
            json.dump(report, f, indent=2)

        notify_success(f"Saved validation report: {output_path}")

        # Итоговое сообщение
        if report["passed"]:
            notify_success("✓ All validation checks passed!")
        else:
            notify_warning(f"⚠ Found {len(report['issues'])} validation issues")
            for issue in report["issues"]:
                notify_error(f"  - {issue}")


if __name__ == "__main__":
    main()
