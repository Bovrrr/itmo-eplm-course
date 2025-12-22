"""Feature engineering для ML моделей.

Применяет StandardScaler к данным:
- Fit на train set
- Transform на train/val/test sets
"""

import json
from pathlib import Path
from typing import Any

import click
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.config.loader import load_pipeline_config
from src.utils.notifications import notify_info, notify_metrics, notify_success, stage_notification


def apply_feature_scaling(
    train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, StandardScaler]:
    """Применить StandardScaler к данным.

    Fit на train, transform на train/val/test.

    Args:
        train: Train dataset
        val: Validation dataset
        test: Test dataset

    Returns:
        Кортеж (train_scaled, val_scaled, test_scaled, scaler)
    """
    # Определить feature columns (всё кроме Survived)
    feature_cols = [col for col in train.columns if col != "Survived"]

    # Fit scaler только на train
    scaler = StandardScaler()
    scaler.fit(train[feature_cols])

    # Transform все три датасета
    train_scaled = train.copy()
    val_scaled = val.copy()
    test_scaled = test.copy()

    train_scaled[feature_cols] = scaler.transform(train[feature_cols])
    val_scaled[feature_cols] = scaler.transform(val[feature_cols])
    test_scaled[feature_cols] = scaler.transform(test[feature_cols])

    return train_scaled, val_scaled, test_scaled, scaler


def calculate_feature_importance(data: pd.DataFrame) -> dict[str, float]:
    """Вычислить важность признаков.

    На данном этапе - фиктивные значения для демонстрации.

    Args:
        data: DataFrame с признаками

    Returns:
        Словарь {feature_name: importance}
    """
    # Фиктивные значения важности
    # В реальности используется RandomForest.feature_importances_ или SHAP
    feature_cols = [col for col in data.columns if col != "Survived"]

    # Генерируем случайные, но детерминированные значения
    importance = {}
    for i, col in enumerate(feature_cols):
        # Простая формула для детерминированности
        importance[col] = (len(feature_cols) - i) / sum(range(1, len(feature_cols) + 1))

    return importance


@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    default="configs/pipeline.yaml",
    help="Path to pipeline configuration file",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default="data/processed",
    help="Directory with train/val/test datasets",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default="data/features",
    help="Directory to save features",
)
def main(config: Path, data_dir: Path, output_dir: Path) -> None:
    """Построить признаки для ML моделей.

    Применяет StandardScaler:
    - Fit на train set
    - Transform на train/val/test sets
    """
    with stage_notification("Feature Engineering"):
        # Загрузить конфигурацию
        notify_info(f"Loading pipeline config from {config}")
        load_pipeline_config(config)  # Валидация конфигурации

        # Загрузить данные
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

        # Применить feature scaling
        notify_info("Applying StandardScaler (fit on train, transform all)...")
        train_scaled, val_scaled, test_scaled, scaler = apply_feature_scaling(train, val, test)
        notify_success("StandardScaler applied successfully")

        # Создать output директорию
        output_dir.mkdir(parents=True, exist_ok=True)

        # Сохранить признаки
        train_features_path = output_dir / "train_features.csv"
        val_features_path = output_dir / "val_features.csv"
        test_features_path = output_dir / "test_features.csv"

        train_scaled.to_csv(train_features_path, index=False)
        val_scaled.to_csv(val_features_path, index=False)
        test_scaled.to_csv(test_features_path, index=False)

        notify_success(f"Saved train features: {train_features_path}")
        notify_success(f"Saved val features: {val_features_path}")
        notify_success(f"Saved test features: {test_features_path}")

        # Вычислить важность признаков
        importance = calculate_feature_importance(train_scaled)
        importance_path = output_dir / "feature_importance.json"
        with importance_path.open("w") as f:
            json.dump(importance, f, indent=2)
        notify_success(f"Saved feature importance: {importance_path}")

        # Подготовить summary
        summary: dict[str, Any] = {
            "total_features": len(train_scaled.columns),
            "train_samples": len(train_scaled),
            "val_samples": len(val_scaled),
            "test_samples": len(test_scaled),
            "feature_names": list(train_scaled.columns),
            "target_column": "Survived" if "Survived" in train_scaled.columns else None,
            "scaler_mean": scaler.mean_.tolist(),
            "scaler_scale": scaler.scale_.tolist(),
        }

        # Сохранить summary
        summary_path = output_dir / "feature_summary.json"
        with summary_path.open("w") as f:
            json.dump(summary, f, indent=2)
        notify_success(f"Saved feature summary: {summary_path}")

        # Вывести summary
        display_summary = {
            "Total features": summary["total_features"],
            "Train samples": summary["train_samples"],
            "Val samples": summary["val_samples"],
            "Test samples": summary["test_samples"],
            "Target column": summary["target_column"] or "None",
        }
        notify_metrics(display_summary, title="Feature Engineering Summary")


if __name__ == "__main__":
    main()
