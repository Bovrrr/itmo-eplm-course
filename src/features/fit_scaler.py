"""Обучение StandardScaler на train данных.

Этот скрипт обучает scaler на train split и сохраняет его для
использования в transform_features.py. Это первый шаг в параллельном
feature engineering pipeline.
"""

from pathlib import Path

import click
import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.utils.notifications import notify_info, notify_success, stage_notification


@click.command()
@click.option(
    "--train-path",
    type=click.Path(exists=True, path_type=Path),
    default=Path("data/processed/train.csv"),
    help="Path to train dataset",
)
@click.option(
    "--output-path",
    type=click.Path(path_type=Path),
    default=Path("data/features/scaler.pkl"),
    help="Path to save fitted scaler",
)
def main(train_path: Path, output_path: Path) -> None:
    """Fit StandardScaler on train data and save it."""
    with stage_notification("Fit Scaler"):
        notify_info(f"Loading train data from {train_path}")
        train = pd.read_csv(train_path)
        notify_success(f"Loaded {len(train)} train samples")

        # Определить feature columns (все кроме target)
        feature_cols = [col for col in train.columns if col != "Survived"]
        notify_info(f"Fitting scaler on {len(feature_cols)} features")

        # Обучить scaler
        scaler = StandardScaler()
        scaler.fit(train[feature_cols])

        # Создать директорию если нужно
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Сохранить scaler
        joblib.dump(scaler, output_path)
        notify_success(f"Scaler saved to {output_path}")

        # Логировать статистику scaler
        notify_info(f"Scaler mean: {scaler.mean_[:3]}... (showing first 3)")
        notify_info(f"Scaler scale: {scaler.scale_[:3]}... (showing first 3)")


if __name__ == "__main__":
    main()
