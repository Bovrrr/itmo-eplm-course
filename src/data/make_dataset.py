import json
import logging
from pathlib import Path

import click
import pandas as pd
from dotenv import find_dotenv, load_dotenv
from sklearn.datasets import load_iris


def load_titanic_from_sklearn() -> pd.DataFrame:
    """Load Titanic-like dataset from sklearn Iris dataset for demonstration."""
    iris = load_iris(as_frame=True)
    df = iris.frame
    # Rename to be more Titanic-like for demo purposes
    df = df.rename(
        columns={
            "sepal length (cm)": "Age",
            "sepal width (cm)": "Fare",
            "petal length (cm)": "Parch",
            "petal width (cm)": "SibSp",
        }
    )
    df["Survived"] = (iris.target > 0).astype(int)
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
        logger.warning(f"Input file {input_path} not found, creating sample data")
        df = load_titanic_from_sklearn()
        input_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(input_path, index=False)
        logger.info(f"Created sample data at {input_path}")
    else:
        df = pd.read_csv(input_path)

    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")

    # Basic data cleaning
    logger.info("Performing data cleaning...")

    # Remove duplicates
    initial_rows = len(df)
    df = df.drop_duplicates()
    logger.info(f"Removed {initial_rows - len(df)} duplicate rows")

    # Handle missing values - forward fill for now
    missing_before = df.isnull().sum().sum()
    df = df.fillna(df.mean(numeric_only=True))
    logger.info(f"Filled {missing_before} missing values")

    # Reset index
    df = df.reset_index(drop=True)

    # Save processed data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path} ({len(df)} rows)")

    # Save data summary as metrics
    summary = {
        "n_rows": int(len(df)),
        "n_columns": int(len(df.columns)),
        "n_missing": int(df.isnull().sum().sum()),
        "columns": list(df.columns),
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
