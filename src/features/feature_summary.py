"""Генерация summary после feature engineering.

Этот скрипт создаёт JSON отчёт о результатах feature engineering,
включая статистику по всем splits и параметры scaler.
"""

import json
from pathlib import Path

import click
import joblib
import pandas as pd

from src.utils.notifications import notify_info, notify_success, stage_notification


@click.command()
@click.option(
    "--features-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("data/features"),
    help="Directory with feature files",
)
@click.option(
    "--output-path",
    type=click.Path(path_type=Path),
    default=Path("data/features/feature_summary.json"),
    help="Path to save summary JSON",
)
def main(features_dir: Path, output_path: Path) -> None:
    """Generate feature engineering summary report."""
    with stage_notification("Feature Summary"):
        # Загрузить все splits
        notify_info("Loading feature files...")
        train = pd.read_csv(features_dir / "train_features.csv")
        val = pd.read_csv(features_dir / "val_features.csv")
        test = pd.read_csv(features_dir / "test_features.csv")

        notify_success(f"Loaded train: {len(train)}, val: {len(val)}, test: {len(test)}")

        # Загрузить scaler
        scaler_path = features_dir / "scaler.pkl"
        scaler = joblib.load(scaler_path)

        # Определить feature columns
        feature_cols = [col for col in train.columns if col != "Survived"]

        # Собрать статистику
        summary = {
            "total_features": len(feature_cols),
            "feature_names": feature_cols,
            "splits": {
                "train": {
                    "samples": len(train),
                    "features": len(feature_cols),
                },
                "val": {
                    "samples": len(val),
                    "features": len(feature_cols),
                },
                "test": {
                    "samples": len(test),
                    "features": len(feature_cols),
                },
            },
            "total_samples": len(train) + len(val) + len(test),
            "scaler": {
                "type": "StandardScaler",
                "n_features": len(scaler.mean_),
                "mean": scaler.mean_.tolist(),
                "scale": scaler.scale_.tolist(),
            },
        }

        # Сохранить summary
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w") as f:
            json.dump(summary, f, indent=2)

        notify_success(f"Summary saved to {output_path}")
        notify_info(f"Total samples: {summary['total_samples']}")
        notify_info(f"Total features: {summary['total_features']}")


if __name__ == "__main__":
    main()
