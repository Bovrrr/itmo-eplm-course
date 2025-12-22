"""Модуль для обучения ML моделей с расширенным MLflow трекингом."""

import json
import logging
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import seaborn as sns
from catboost import CatBoostClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC

from src.config.loader import load_model_config
from src.mlflow_utils import log_time, mlflow_run
from src.models.model_configs import get_model_config


def setup_mlflow_tracking() -> None:
    """Настройка MLflow tracking с локальным файловым бэкендом."""
    tracking_uri = f"file:{Path.cwd()}/mlruns"
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("titanic_classification")


def create_model_from_config(config_name: str) -> Any:
    """Создать модель из конфигурации.

    Сначала пытается загрузить через Pydantic (configs/model/*.yaml),
    затем fallback на старый способ (model_configs.py).

    Args:
        config_name: Имя конфигурации модели.

    Returns:
        Экземпляр ML модели.

    Raises:
        ValueError: Если класс модели не поддерживается.
    """
    # Маппинг имён классов на реальные классы
    model_classes = {
        "LogisticRegression": LogisticRegression,
        "SVC": SVC,
        "RandomForestClassifier": RandomForestClassifier,
        "GradientBoostingClassifier": GradientBoostingClassifier,
        "CatBoostClassifier": CatBoostClassifier,
        "KNeighborsClassifier": KNeighborsClassifier,
    }

    # Попробовать загрузить через Pydantic
    config_path = Path(f"configs/model/{config_name}.yaml")
    if config_path.exists():
        pydantic_config = load_model_config(config_path, validate=True)
        config_dict = pydantic_config.model_dump()
        model_class_name = config_dict["model_class"]

        # Извлечь только параметры модели (убрать meta поля)
        meta_fields = {"model_class", "description", "random_state"}
        params = {k: v for k, v in config_dict.items() if k not in meta_fields}
    else:
        # Fallback на старый способ
        config = get_model_config(config_name)
        model_class_name = config["model_class"]
        params = config["params"]

    if model_class_name not in model_classes:
        raise ValueError(
            f"Unsupported model class: {model_class_name}. Supported: {list(model_classes.keys())}"
        )

    model_class = model_classes[model_class_name]
    return model_class(**params)


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, output_path: Path) -> None:
    """Создать и сохранить confusion matrix.

    Args:
        y_true: Истинные метки.
        y_pred: Предсказанные метки.
        output_path: Путь для сохранения изображения.
    """
    cm = confusion_matrix(y_true, y_pred)

    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=True,
        square=True,
        xticklabels=["Class 0", "Class 1"],
        yticklabels=["Class 0", "Class 1"],
    )
    plt.title("Confusion Matrix", fontsize=14, fontweight="bold")
    plt.ylabel("True Label", fontsize=12)
    plt.xlabel("Predicted Label", fontsize=12)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_roc_curve_fig(y_true: np.ndarray, y_proba: np.ndarray, output_path: Path) -> float:
    """Создать и сохранить ROC curve.

    Args:
        y_true: Истинные метки.
        y_proba: Вероятности для положительного класса.
        output_path: Путь для сохранения изображения.

    Returns:
        ROC AUC score.
    """
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    roc_auc = roc_auc_score(y_true, y_proba)

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {roc_auc:.3f})")
    plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--", label="Random")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate", fontsize=12)
    plt.ylabel("True Positive Rate", fontsize=12)
    plt.title("Receiver Operating Characteristic (ROC) Curve", fontsize=14, fontweight="bold")
    plt.legend(loc="lower right", fontsize=10)
    plt.grid(alpha=0.3)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    return float(roc_auc)


def plot_feature_importance(model: Any, feature_names: list[str], output_path: Path) -> None:
    """Создать и сохранить график feature importance.

    Args:
        model: Обученная модель с атрибутом feature_importances_.
        feature_names: Названия признаков.
        output_path: Путь для сохранения изображения.
    """
    if not hasattr(model, "feature_importances_"):
        return

    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]

    plt.figure(figsize=(10, 6))
    plt.title("Feature Importances", fontsize=14, fontweight="bold")
    plt.bar(range(len(importances)), importances[indices], align="center")
    plt.xticks(
        range(len(importances)), [feature_names[i] for i in indices], rotation=45, ha="right"
    )
    plt.xlabel("Features", fontsize=12)
    plt.ylabel("Importance", fontsize=12)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


@mlflow_run(experiment_name="titanic_classification")
@log_time
def train_model_pipeline(  # noqa: PLR0915
    data_path: str,
    model_output_path: str,
    config_name: str = "random_forest_medium",
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, float]:
    """Обучить ML модель с полным MLflow трекингом.

    Args:
        data_path: Путь к обработанным данным (CSV).
        model_output_path: Путь для сохранения обученной модели.
        config_name: Имя конфигурации модели из model_configs.
        test_size: Размер тестовой выборки (default 0.2).
        random_state: Random state для воспроизводимости.

    Returns:
        Словарь с метриками модели.
    """
    logger = logging.getLogger(__name__)

    # Установить имя run в MLflow
    config = get_model_config(config_name)
    mlflow.set_tag("mlflow.runName", config_name)  # Установить название run для UI
    mlflow.set_tag("config_name", config_name)
    mlflow.set_tag("model_class", config["model_class"])
    mlflow.set_tag("description", config.get("description", ""))

    logger.info(f"Training model: {config_name}")
    logger.info(f"Model class: {config['model_class']}")

    # Загрузить данные
    logger.info("Loading data for training")
    df = pd.read_csv(data_path)

    # Подготовить признаки и целевую переменную
    if "Survived" not in df.columns:
        logger.warning("'Survived' column not found, using last column as target")
        features = df.iloc[:, :-1]
        target = df.iloc[:, -1]
    else:
        features = df.drop("Survived", axis=1)
        target = df["Survived"]

    # Выбрать только числовые колонки
    features = features.select_dtypes(include=["number"])
    feature_names = list(features.columns)

    logger.info(f"Features shape: {features.shape}, Target shape: {target.shape}")

    # Разделить на train/test
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=test_size, random_state=random_state
    )
    logger.info(f"Train set: {x_train.shape}, Test set: {x_test.shape}")

    # Логировать параметры конфигурации
    mlflow.log_param("config_name", config_name)
    mlflow.log_param("model_type", config["model_class"])
    mlflow.log_param("test_size", test_size)
    mlflow.log_param("random_state", random_state)
    mlflow.log_param("n_features", x_train.shape[1])
    mlflow.log_param("n_train_samples", x_train.shape[0])
    mlflow.log_param("n_test_samples", x_test.shape[0])

    # Логировать все параметры модели
    for param_name, param_value in config["params"].items():
        mlflow.log_param(f"model_{param_name}", param_value)

    # Создать и обучить модель
    logger.info(f"Creating model from config: {config_name}")
    model = create_model_from_config(config_name)

    logger.info("Training model...")
    train_start = time.time()
    model.fit(x_train, y_train)
    train_time = time.time() - train_start
    logger.info(f"Model trained in {train_time:.2f}s")

    # Логировать время обучения
    mlflow.log_metric("train_time_seconds", train_time)

    # Генерировать предсказания
    y_pred = model.predict(x_test)

    # Вычислить основные метрики
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average="binary", zero_division=0)
    recall = recall_score(y_test, y_pred, average="binary", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="binary", zero_division=0)

    logger.info(
        f"Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}"
    )

    # Логировать основные метрики
    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("precision", precision)
    mlflow.log_metric("recall", recall)
    mlflow.log_metric("f1_score", f1)

    # Создать временную директорию для артефактов
    artifacts_dir = Path(model_output_path).parent / "artifacts_tmp"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # 1. Confusion Matrix
    cm_path = artifacts_dir / "confusion_matrix.png"
    plot_confusion_matrix(y_test.values, y_pred, cm_path)
    mlflow.log_artifact(str(cm_path))
    logger.info("Confusion matrix logged")

    # 2. ROC Curve (если модель поддерживает predict_proba)
    if hasattr(model, "predict_proba"):
        try:
            y_proba = model.predict_proba(x_test)[:, 1]
            roc_path = artifacts_dir / "roc_curve.png"
            roc_auc = plot_roc_curve_fig(y_test.values, y_proba, roc_path)
            mlflow.log_artifact(str(roc_path))
            mlflow.log_metric("roc_auc", roc_auc)
            logger.info(f"ROC curve logged (AUC: {roc_auc:.4f})")
        except Exception as e:
            logger.warning(f"Could not compute ROC curve: {e}")

    # 3. Feature Importance (для tree-based моделей)
    if hasattr(model, "feature_importances_"):
        fi_path = artifacts_dir / "feature_importance.png"
        plot_feature_importance(model, feature_names, fi_path)
        mlflow.log_artifact(str(fi_path))
        logger.info("Feature importance logged")

    # 4. Classification Report
    clf_report = classification_report(y_test, y_pred, output_dict=True)
    clf_report_path = artifacts_dir / "classification_report.json"
    with open(clf_report_path, "w") as f:
        json.dump(clf_report, f, indent=2)
    mlflow.log_artifact(str(clf_report_path))
    logger.info("Classification report logged")

    # 5. Логировать размер модели
    model_temp_path = artifacts_dir / "model_temp.pkl"
    joblib.dump(model, model_temp_path)
    model_size_bytes = model_temp_path.stat().st_size
    mlflow.log_metric("model_size_bytes", model_size_bytes)
    logger.info(f"Model size: {model_size_bytes / 1024:.2f} KB")

    # Логировать модель в MLflow
    mlflow.sklearn.log_model(
        model,
        "model",
        registered_model_name="titanic_classifier",
    )
    logger.info("Model logged to MLflow")

    # Сохранить модель на диск
    model_output_path_obj = Path(model_output_path)
    model_output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_output_path_obj)
    logger.info(f"Model saved to {model_output_path_obj}")

    # Сохранить метрики
    metrics = {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "train_time_seconds": float(train_time),
        "model_size_bytes": int(model_size_bytes),
    }

    # Добавить ROC AUC если есть
    if hasattr(model, "predict_proba"):
        try:
            y_proba = model.predict_proba(x_test)[:, 1]
            metrics["roc_auc"] = float(roc_auc_score(y_test, y_proba))
        except Exception:
            pass

    metrics_path = model_output_path_obj.parent / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

    # Логировать metrics.json как артефакт
    mlflow.log_artifact(str(metrics_path))

    # Очистить временную директорию с артефактами
    shutil.rmtree(artifacts_dir, ignore_errors=True)

    return metrics


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    logger = logging.getLogger(__name__)

    # Можно передать config_name через аргумент командной строки
    config_name = sys.argv[1] if len(sys.argv) > 1 else "random_forest_medium"

    try:
        setup_mlflow_tracking()
        metrics = train_model_pipeline(
            data_path="data/processed/titanic_processed.csv",
            model_output_path="models/model.pkl",
            config_name=config_name,
        )
        logger.info(f"Training completed. Final metrics: {metrics}")
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise
