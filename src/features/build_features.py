"""Feature engineering для ML моделей.

На данном этапе это заглушка для демонстрации DVC pipeline.
Копирует train.csv → train_features.csv без трансформаций.
"""

import json
from pathlib import Path
from typing import Any

import click
import pandas as pd

from src.config.loader import load_pipeline_config
from src.utils.notifications import notify_info, notify_metrics, notify_success, stage_notification


def generate_features(data: pd.DataFrame) -> pd.DataFrame:
    """Сгенерировать признаки из данных.

    На данном этапе - заглушка, возвращает исходные данные.
    В будущем здесь будут:
    - Feature engineering (новые признаки)
    - Feature selection (отбор признаков)
    - Feature scaling (нормализация)

    Args:
        data: Исходные данные

    Returns:
        DataFrame с признаками
    """
    # TODO: Реальный feature engineering
    # Пока просто возвращаем исходные данные
    return data.copy()


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
    "--input",
    type=click.Path(exists=True, path_type=Path),
    default="data/processed/train.csv",
    help="Path to train dataset",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default="data/features",
    help="Directory to save features",
)
def main(config: Path, input: Path, output_dir: Path) -> None:
    """Построить признаки для ML моделей.

    На данном этапе это заглушка, которая:
    - Копирует train.csv → train_features.csv
    - Генерирует фиктивные feature_importance.json
    - Генерирует feature_summary.json
    """
    with stage_notification("Feature Engineering"):
        # Загрузить конфигурацию
        notify_info(f"Loading pipeline config from {config}")
        load_pipeline_config(config)  # Валидация конфигурации

        # Загрузить данные
        notify_info(f"Loading data from {input}")
        train = pd.read_csv(input)
        notify_success(f"Loaded {len(train)} rows, {len(train.columns)} columns")

        # Генерировать признаки
        notify_info("Generating features...")
        features = generate_features(train)
        notify_success(f"Generated {len(features.columns)} features")

        # Создать output директорию
        output_dir.mkdir(parents=True, exist_ok=True)

        # Сохранить признаки
        features_path = output_dir / "train_features.csv"
        features.to_csv(features_path, index=False)
        notify_success(f"Saved features: {features_path}")

        # Вычислить важность признаков
        importance = calculate_feature_importance(features)
        importance_path = output_dir / "feature_importance.json"
        with importance_path.open("w") as f:
            json.dump(importance, f, indent=2)
        notify_success(f"Saved feature importance: {importance_path}")

        # Подготовить summary
        summary: dict[str, Any] = {
            "total_features": len(features.columns),
            "total_samples": len(features),
            "feature_names": list(features.columns),
            "target_column": "Survived" if "Survived" in features.columns else None,
        }

        # Сохранить summary
        summary_path = output_dir / "feature_summary.json"
        with summary_path.open("w") as f:
            json.dump(summary, f, indent=2)
        notify_success(f"Saved feature summary: {summary_path}")

        # Вывести summary
        display_summary = {
            "Total features": summary["total_features"],
            "Total samples": summary["total_samples"],
            "Target column": summary["target_column"] or "None",
        }
        notify_metrics(display_summary, title="Feature Engineering Summary")


if __name__ == "__main__":
    main()
