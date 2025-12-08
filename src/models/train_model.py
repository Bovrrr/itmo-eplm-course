import json
import logging
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split


def setup_mlflow_tracking() -> None:
    """Set up MLflow tracking with local file backend."""
    tracking_uri = f"file:{Path.cwd()}/mlruns"
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("titanic_classification")


def train_model_pipeline(
    data_path: str,
    model_output_path: str,
    test_size: float = 0.2,
    random_state: int = 42,
    n_estimators: int = 100,
) -> dict[str, float]:
    """Train a machine learning model with MLflow tracking.

    Args:
        data_path: Path to processed data CSV
        model_output_path: Path to save trained model
        test_size: Test set size (default 0.2)
        random_state: Random state for reproducibility
        n_estimators: Number of trees in Random Forest

    Returns:
        Dictionary with model performance metrics
    """
    logger = logging.getLogger(__name__)

    setup_mlflow_tracking()

    with mlflow.start_run(run_name="random_forest_training"):
        logger.info("Loading data for training")
        df = pd.read_csv(data_path)

        # Prepare features and target
        # Assuming 'Survived' is the target column
        if "Survived" not in df.columns:
            logger.warning("'Survived' column not found, using last column as target")
            features = df.iloc[:, :-1]
            target = df.iloc[:, -1]
        else:
            features = df.drop("Survived", axis=1)
            target = df["Survived"]

        # Select only numeric columns
        features = features.select_dtypes(include=["number"])

        logger.info(f"Features shape: {features.shape}, Target shape: {target.shape}")

        # Split data
        x_train, x_test, y_train, y_test = train_test_split(
            features, target, test_size=test_size, random_state=random_state
        )
        logger.info(f"Train set: {x_train.shape}, Test set: {x_test.shape}")

        # Log parameters
        mlflow.log_param("model_type", "RandomForest")
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("test_size", test_size)
        mlflow.log_param("random_state", random_state)
        mlflow.log_param("n_features", x_train.shape[1])

        # Train model
        logger.info("Training Random Forest model")
        model = RandomForestClassifier(
            n_estimators=n_estimators, random_state=random_state, n_jobs=-1
        )
        model.fit(x_train, y_train)

        # Generate predictions
        y_pred = model.predict(x_test)

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        logger.info(f"Model trained. Accuracy: {accuracy:.4f}, F1: {f1:.4f}")

        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("f1_score", f1)

        # Log model
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name="titanic_classifier",
        )
        logger.info("Model logged to MLflow")

        # Save model to disk
        model_output_path_obj = Path(model_output_path)
        model_output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_output_path_obj)
        logger.info(f"Model saved to {model_output_path_obj}")

        # Save metrics
        metrics = {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
        }
        metrics_path = model_output_path_obj.parent / "metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Metrics saved to {metrics_path}")

        # Log metrics file as artifact
        mlflow.log_artifact(str(metrics_path))

        return metrics


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    logger = logging.getLogger(__name__)

    try:
        metrics = train_model_pipeline(
            data_path="data/processed/titanic_processed.csv",
            model_output_path="models/model.pkl",
        )
        logger.info(f"Training completed. Final metrics: {metrics}")
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise
