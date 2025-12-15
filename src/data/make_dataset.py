import json
import logging
from pathlib import Path

import click
import pandas as pd
import seaborn as sns
from dotenv import find_dotenv, load_dotenv
from sklearn.preprocessing import StandardScaler


def load_titanic_dataset() -> pd.DataFrame:
    """Load Titanic dataset from seaborn.

    Returns:
        DataFrame with Titanic data (891 rows, 15 columns)
    """
    df = sns.load_dataset("titanic")

    # Rename 'survived' to 'Survived' for consistency
    df = df.rename(columns={"survived": "Survived"})

    # Add PassengerId if not exists
    if "PassengerId" not in df.columns:
        df["PassengerId"] = range(len(df))

    return df


def prepare_data(input_path: Path, output_path: Path) -> None:
    """Load raw data and prepare it for modeling.

    Args:
        input_path: Path to raw data CSV
        output_path: Path to save processed data
    """
    logger = logging.getLogger(__name__)

    # Load data
    logger.info(f"Loading data from {input_path}")
    if not input_path.exists():
        logger.warning(f"Input file {input_path} not found, loading from seaborn")
        df = load_titanic_dataset()
        input_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(input_path, index=False)
        logger.info(f"Created Titanic data at {input_path}")
    else:
        df = pd.read_csv(input_path)

    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")

    # Titanic-specific preprocessing
    logger.info("Performing Titanic preprocessing...")

    # Select features for modeling
    # Keep only numerical features: age, sibsp, parch, fare, pclass
    selected_cols = ["age", "sibsp", "parch", "fare", "pclass", "Survived"]

    # Check if columns exist
    missing_cols = [col for col in selected_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing columns: {missing_cols}, using available columns")
        selected_cols = [col for col in selected_cols if col in df.columns]

    df = df[selected_cols].copy()

    # Remove duplicates
    initial_rows = len(df)
    df = df.drop_duplicates()
    logger.info(f"Removed {initial_rows - len(df)} duplicate rows")

    # Handle missing values
    missing_before = df.isnull().sum().sum()

    # Fill age with median
    if "age" in df.columns:
        df["age"] = df["age"].fillna(df["age"].median())

    # Fill fare with median
    if "fare" in df.columns:
        df["fare"] = df["fare"].fillna(df["fare"].median())

    # Fill other numeric columns with 0
    df = df.fillna(0)

    logger.info(f"Filled {missing_before} missing values")

    # Apply StandardScaler to features (not target)
    if "Survived" in df.columns:
        feature_cols = [col for col in df.columns if col != "Survived"]
        scaler = StandardScaler()
        df[feature_cols] = scaler.fit_transform(df[feature_cols])
        logger.info(f"Applied StandardScaler to {len(feature_cols)} features")

    # Reset index
    df = df.reset_index(drop=True)

    # Note: PassengerId removed - it's just an index with no predictive power

    # Save processed data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path} ({len(df)} rows, {len(df.columns)} cols)")

    # Save data summary as metrics
    summary = {
        "n_rows": int(len(df)),
        "n_columns": int(len(df.columns)),
        "n_missing": int(df.isnull().sum().sum()),
        "columns": list(df.columns),
        "target_distribution": df["Survived"].value_counts().to_dict()
        if "Survived" in df.columns
        else {},
    }
    summary_path = output_path.parent / "data_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved data summary to {summary_path}")


@click.command()
@click.argument("input_filepath", type=click.Path(), default="data/raw/titanic.csv")
@click.argument(
    "output_filepath", type=click.Path(), default="data/processed/titanic_processed.csv"
)
def main(input_filepath: str, output_filepath: str) -> None:
    """Process raw data into cleaned format ready for modeling.

    Args:
        input_filepath: Path to raw data CSV (default: data/raw/titanic.csv)
        output_filepath: Path to save processed data (default: data/processed/titanic_processed.csv)
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting data preparation")

    input_path = Path(input_filepath)
    output_path = Path(output_filepath)

    prepare_data(input_path, output_path)

    logger.info("Data preparation completed successfully")


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # Find .env and load environment variables
    project_dir = Path(__file__).resolve().parents[2]
    load_dotenv(find_dotenv())

    main()
