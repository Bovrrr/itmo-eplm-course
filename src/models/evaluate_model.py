"""Оценка обученной модели на test set."""

import json
from pathlib import Path
from typing import Any

import click
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from src.config.loader import load_pipeline_config
from src.utils.notifications import notify_info, notify_metrics, notify_success, stage_notification


def evaluate_classifier(model: Any, x_test: pd.DataFrame, y_test: pd.Series) -> dict[str, Any]:
    """Оценить классификатор на test set.

    Args:
        model: Обученная модель
        x_test: Признаки test set
        y_test: Целевая переменная test set

    Returns:
        Словарь с метриками
    """
    # Предсказания
    y_pred = model.predict(x_test)
    y_pred_proba = model.predict_proba(x_test)[:, 1] if hasattr(model, "predict_proba") else None

    # Вычислить метрики
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
    }

    # ROC AUC если есть вероятности
    if y_pred_proba is not None:
        metrics["roc_auc"] = float(roc_auc_score(y_test, y_pred_proba))

    return metrics


def generate_confusion_matrix_plot(y_test: pd.Series, y_pred: np.ndarray) -> dict[str, Any]:
    """Сгенерировать данные для confusion matrix plot.

    Args:
        y_test: Истинные метки
        y_pred: Предсказанные метки

    Returns:
        Словарь для DVC plot
    """
    cm = confusion_matrix(y_test, y_pred)

    # Формат для DVC plots
    plot_data = {
        "data": [
            {"actual": "0", "predicted": "0", "count": int(cm[0, 0])},
            {"actual": "0", "predicted": "1", "count": int(cm[0, 1])},
            {"actual": "1", "predicted": "0", "count": int(cm[1, 0])},
            {"actual": "1", "predicted": "1", "count": int(cm[1, 1])},
        ]
    }

    return plot_data


def generate_roc_curve_plot(y_test: pd.Series, y_pred_proba: np.ndarray) -> dict[str, Any]:
    """Сгенерировать данные для ROC curve plot.

    Args:
        y_test: Истинные метки
        y_pred_proba: Вероятности класса 1

    Returns:
        Словарь для DVC plot
    """
    fpr, tpr, _ = roc_curve(y_test, y_pred_proba)

    # Формат для DVC plots
    plot_data = {
        "data": [{"fpr": float(f), "tpr": float(t)} for f, t in zip(fpr, tpr, strict=False)]
    }

    return plot_data


@click.command()
@click.option(
    "--model-path",
    type=click.Path(exists=True, path_type=Path),
    default="models/model.pkl",
    help="Path to trained model",
)
@click.option(
    "--test-data",
    type=click.Path(exists=True, path_type=Path),
    default="data/features/test_features.csv",
    help="Path to test dataset with features",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default="models",
    help="Directory to save evaluation results",
)
def main(model_path: Path, test_data: Path, output_dir: Path) -> None:
    """Оценить обученную модель на test set.

    Вычисляет метрики и создаёт plots для DVC.
    """
    with stage_notification("Model Evaluation"):
        # Загрузить конфигурацию через Hydra (для валидации)
        load_pipeline_config()

        # Загрузить модель
        notify_info(f"Loading model from {model_path}")
        model = joblib.load(model_path)
        notify_success("Model loaded successfully")

        # Загрузить test данные
        notify_info(f"Loading test data from {test_data}")
        test = pd.read_csv(test_data)
        notify_success(f"Loaded {len(test)} test samples")

        # Разделить на X и y
        if "Survived" in test.columns:
            x_test = test.drop("Survived", axis=1)
            y_test = test["Survived"]
        else:
            raise ValueError("Target column 'Survived' not found in test data")

        # Оценить модель
        notify_info("Evaluating model on test set...")
        metrics = evaluate_classifier(model, x_test, y_test)
        notify_success("Model evaluation completed")

        # Сохранить метрики
        output_dir.mkdir(parents=True, exist_ok=True)
        metrics_path = output_dir / "evaluation_metrics.json"
        with metrics_path.open("w") as f:
            json.dump(metrics, f, indent=2)
        notify_success(f"Saved metrics: {metrics_path}")

        # Создать plots директорию
        plots_dir = output_dir / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)

        # Генерировать confusion matrix plot
        y_pred = model.predict(x_test)
        cm_plot = generate_confusion_matrix_plot(y_test, y_pred)
        cm_path = plots_dir / "confusion_matrix.json"
        with cm_path.open("w") as f:
            json.dump(cm_plot, f, indent=2)
        notify_success(f"Saved confusion matrix plot: {cm_path}")

        # Генерировать ROC curve plot (если есть predict_proba)
        if hasattr(model, "predict_proba"):
            y_pred_proba = model.predict_proba(x_test)[:, 1]
            roc_plot = generate_roc_curve_plot(y_test, y_pred_proba)
            roc_path = plots_dir / "roc_curve.json"
            with roc_path.open("w") as f:
                json.dump(roc_plot, f, indent=2)
            notify_success(f"Saved ROC curve plot: {roc_path}")

        # Вывести summary
        display_metrics = {
            "Accuracy": metrics["accuracy"],
            "Precision": metrics["precision"],
            "Recall": metrics["recall"],
            "F1 Score": metrics["f1_score"],
        }
        if "roc_auc" in metrics:
            display_metrics["ROC AUC"] = metrics["roc_auc"]

        notify_metrics(display_metrics, title="Test Set Evaluation")


if __name__ == "__main__":
    main()
