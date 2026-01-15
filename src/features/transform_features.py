"""Transform данных с использованием обученного scaler.

Этот скрипт применяет pre-fitted scaler к одному split (train, val или test).
Может выполняться параллельно для разных splits через DVC foreach.
"""

from pathlib import Path

import click
import joblib
import pandas as pd

from src.utils.notifications import notify_info, notify_success, stage_notification


@click.command()
@click.option(
    "--split",
    type=click.Choice(["train", "val", "test"], case_sensitive=False),
    required=True,
    help="Split name to process: train, val, or test",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("data/processed"),
    help="Directory with split CSV files",
)
@click.option(
    "--scaler-path",
    type=click.Path(exists=True, path_type=Path),
    default=Path("data/features/scaler.pkl"),
    help="Path to fitted scaler",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("data/features"),
    help="Directory to save transformed features",
)
def main(split: str, data_dir: Path, scaler_path: Path, output_dir: Path) -> None:
    """Transform a single split using the fitted scaler."""
    with stage_notification(f"Transform Features ({split})"):
        # Загрузить данные
        input_path = data_dir / f"{split}.csv"
        notify_info(f"Loading {split} data from {input_path}")
        data = pd.read_csv(input_path)
        notify_success(f"Loaded {len(data)} {split} samples")

        # Загрузить scaler
        notify_info(f"Loading scaler from {scaler_path}")
        scaler = joblib.load(scaler_path)

        # Определить feature columns
        feature_cols = [col for col in data.columns if col != "Survived"]
        notify_info(f"Transforming {len(feature_cols)} features")

        # Применить scaler
        data_scaled = data.copy()
        data_scaled[feature_cols] = scaler.transform(data[feature_cols])

        # Сохранить результат
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{split}_features.csv"
        data_scaled.to_csv(output_path, index=False)
        notify_success(f"Saved {split} features to {output_path}")

        # Логировать статистику
        notify_info(f"Output shape: {data_scaled.shape}")


if __name__ == "__main__":
    main()
