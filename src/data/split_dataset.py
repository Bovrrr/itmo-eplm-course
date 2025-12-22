"""Разделение данных на train/val/test наборы."""

import json
from pathlib import Path
from typing import Any

import click
import pandas as pd
from sklearn.model_selection import train_test_split

from src.config.loader import load_pipeline_config
from src.utils.notifications import notify_info, notify_metrics, notify_success, stage_notification


def split_data(
    data: pd.DataFrame,
    train_size: float,
    val_size: float,
    test_size: float,
    random_state: int,
    stratify_column: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Разделить данные на train/val/test.

    Args:
        data: Исходные данные
        train_size: Размер train set (0.0-1.0)
        val_size: Размер validation set (0.0-1.0)
        test_size: Размер test set (0.0-1.0)
        random_state: Seed для воспроизводимости
        stratify_column: Колонка для stratified split (опционально)

    Returns:
        Tuple из (train, val, test) DataFrame
    """
    # Проверка что сумма размеров = 1
    total = train_size + val_size + test_size
    if not (0.99 <= total <= 1.01):
        raise ValueError(f"Sizes must sum to 1.0, got {total:.3f}")

    # Подготовить stratify
    stratify_y = data[stratify_column] if stratify_column else None

    # Шаг 1: Отделить test set от остального
    temp_size = train_size + val_size
    train_val, test = train_test_split(
        data,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_y,
    )

    # Шаг 2: Разделить train и val
    # Пересчитать пропорцию: val_size относительно temp_size
    val_ratio = val_size / temp_size
    stratify_temp = train_val[stratify_column] if stratify_column else None

    train, val = train_test_split(
        train_val,
        test_size=val_ratio,
        random_state=random_state,
        stratify=stratify_temp,
    )

    return train, val, test


@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    default="configs/pipeline.yaml",
    help="Path to pipeline configuration file",
)
@click.option(
    "--input",
    type=click.Path(exists=True, path_type=Path),
    default="data/processed/titanic_processed.csv",
    help="Path to processed data file",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default="data/processed",
    help="Directory to save split datasets",
)
def main(config: Path, input: Path, output_dir: Path) -> None:
    """Разделить данные на train/val/test наборы.

    Использует параметры из pipeline configuration (data_split секция).
    Сохраняет 3 CSV файла и JSON с метриками разделения.
    """
    with stage_notification("Data Split"):
        # Загрузить конфигурацию
        notify_info(f"Loading pipeline config from {config}")
        pipeline_config = load_pipeline_config(config)
        split_config = pipeline_config.data_split

        # Загрузить данные
        notify_info(f"Loading data from {input}")
        data = pd.read_csv(input)
        notify_success(f"Loaded {len(data)} rows, {len(data.columns)} columns")

        # Определить колонку для stratification
        stratify_column = (
            "Survived" if split_config.stratify and "Survived" in data.columns else None
        )
        if stratify_column:
            notify_info(f"Using stratified split on '{stratify_column}' column")

        # Разделить данные
        train, val, test = split_data(
            data=data,
            train_size=split_config.train_size,
            val_size=split_config.val_size,
            test_size=split_config.test_size,
            random_state=split_config.random_state,
            stratify_column=stratify_column,
        )

        # Создать output директорию если не существует
        output_dir.mkdir(parents=True, exist_ok=True)

        # Сохранить splits
        train_path = output_dir / "train.csv"
        val_path = output_dir / "val.csv"
        test_path = output_dir / "test.csv"

        notify_info("Saving split datasets...")
        train.to_csv(train_path, index=False)
        val.to_csv(val_path, index=False)
        test.to_csv(test_path, index=False)

        notify_success(f"Saved train set: {train_path} ({len(train)} rows)")
        notify_success(f"Saved val set: {val_path} ({len(val)} rows)")
        notify_success(f"Saved test set: {test_path} ({len(test)} rows)")

        # Подготовить метрики
        summary: dict[str, Any] = {
            "total_rows": len(data),
            "train_rows": len(train),
            "val_rows": len(val),
            "test_rows": len(test),
            "train_ratio": len(train) / len(data),
            "val_ratio": len(val) / len(data),
            "test_ratio": len(test) / len(data),
            "stratified": split_config.stratify,
            "random_state": split_config.random_state,
        }

        # Добавить статистику по классам если stratified
        if stratify_column:
            summary["train_class_distribution"] = train[stratify_column].value_counts().to_dict()
            summary["val_class_distribution"] = val[stratify_column].value_counts().to_dict()
            summary["test_class_distribution"] = test[stratify_column].value_counts().to_dict()

        # Сохранить метрики
        metrics_path = output_dir / "split_summary.json"
        with metrics_path.open("w") as f:
            json.dump(summary, f, indent=2)

        notify_success(f"Saved metrics: {metrics_path}")

        # Вывести summary
        display_summary = {
            "Total rows": summary["total_rows"],
            "Train rows": summary["train_rows"],
            "Val rows": summary["val_rows"],
            "Test rows": summary["test_rows"],
            "Train ratio": summary["train_ratio"],
            "Val ratio": summary["val_ratio"],
            "Test ratio": summary["test_ratio"],
            "Stratified": summary["stratified"],
            "Random state": summary["random_state"],
        }
        notify_metrics(display_summary, title="Split Summary")


if __name__ == "__main__":
    main()
