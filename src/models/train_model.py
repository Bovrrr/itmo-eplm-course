"""Модуль для обучения ML моделей с расширенным ClearML трекингом."""

import json
import logging
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from catboost import CatBoostClassifier
from clearml import Task
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
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC

from src.clearml_utils import (
    clearml_task,
    log_artifact,
    log_metrics,
    log_time,
    register_model,
    set_tags,
)
from src.config.loader import load_model_config
from src.models.model_configs import get_model_config


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
        # Проверка типа для MyPy (load_model_config всегда возвращает BaseModel)
        if isinstance(pydantic_config, dict):
            # Fallback на старый способ
            model_class_name = pydantic_config["model_class"]
            params = pydantic_config["params"]
        else:
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


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, output_path: Path) -> plt.Figure:
    """Создать и сохранить confusion matrix.

    Args:
        y_true: Истинные метки.
        y_pred: Предсказанные метки.
        output_path: Путь для сохранения изображения.

    Returns:
        Matplotlib Figure объект.
    """
    cm = confusion_matrix(y_true, y_pred)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=True,
        square=True,
        xticklabels=["Class 0", "Class 1"],
        yticklabels=["Class 0", "Class 1"],
        ax=ax,
    )
    ax.set_title("Confusion Matrix", fontsize=14, fontweight="bold")
    ax.set_ylabel("True Label", fontsize=12)
    ax.set_xlabel("Predicted Label", fontsize=12)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig


def plot_roc_curve_fig(
    y_true: np.ndarray, y_proba: np.ndarray, output_path: Path
) -> tuple[plt.Figure, float]:
    """Создать и сохранить ROC curve.

    Args:
        y_true: Истинные метки.
        y_proba: Вероятности для положительного класса.
        output_path: Путь для сохранения изображения.

    Returns:
        Tuple (Figure, ROC AUC score).
    """
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    roc_auc = roc_auc_score(y_true, y_proba)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {roc_auc:.3f})")
    ax.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--", label="Random")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title("Receiver Operating Characteristic (ROC) Curve", fontsize=14, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(alpha=0.3)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig, float(roc_auc)


def plot_feature_importance(
    model: Any, feature_names: list[str], output_path: Path
) -> plt.Figure | None:
    """Создать и сохранить график feature importance.

    Args:
        model: Обученная модель с атрибутом feature_importances_.
        feature_names: Названия признаков.
        output_path: Путь для сохранения изображения.

    Returns:
        Matplotlib Figure объект или None.
    """
    if not hasattr(model, "feature_importances_"):
        return None

    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title("Feature Importances", fontsize=14, fontweight="bold")
    ax.bar(range(len(importances)), importances[indices], align="center")
    ax.set_xticks(range(len(importances)))
    ax.set_xticklabels([feature_names[i] for i in indices], rotation=45, ha="right")
    ax.set_xlabel("Features", fontsize=12)
    ax.set_ylabel("Importance", fontsize=12)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig


@clearml_task(project_name="titanic_classification", task_type="training")
@log_time
def train_model_pipeline(  # noqa: PLR0912
    train_data_path: str,
    val_data_path: str,
    model_output_path: str,
    config_name: str = "random_forest_medium",
    random_state: int = 42,
) -> dict[str, float]:
    """Обучить ML модель с полным ClearML трекингом.

    Args:
        train_data_path: Путь к train данным с признаками (CSV).
        val_data_path: Путь к validation данным с признаками (CSV).
        model_output_path: Путь для сохранения обученной модели.
        config_name: Имя конфигурации модели из model_configs.
        random_state: Random state для воспроизводимости.

    Returns:
        Словарь с метриками модели.
    """
    logger = logging.getLogger(__name__)
    task = Task.current_task()

    # Получить конфигурацию модели
    config = get_model_config(config_name)

    # Установить имя задачи и теги
    if task:
        task.set_name(config_name)
        set_tags([config_name, config["model_class"]])

    logger.info(f"Training model: {config_name}")
    logger.info(f"Model class: {config['model_class']}")

    # Загрузить train данные
    logger.info(f"Loading train data from {train_data_path}")
    train_df = pd.read_csv(train_data_path)

    # Загрузить validation данные
    logger.info(f"Loading validation data from {val_data_path}")
    val_df = pd.read_csv(val_data_path)

    # Подготовить признаки и целевую переменную для train
    if "Survived" not in train_df.columns:
        logger.warning("'Survived' column not found in train, using last column as target")
        x_train = train_df.iloc[:, :-1]
        y_train = train_df.iloc[:, -1]
    else:
        x_train = train_df.drop("Survived", axis=1)
        y_train = train_df["Survived"]

    # Подготовить признаки и целевую переменную для validation
    if "Survived" not in val_df.columns:
        logger.warning("'Survived' column not found in val, using last column as target")
        x_test = val_df.iloc[:, :-1]
        y_test = val_df.iloc[:, -1]
    else:
        x_test = val_df.drop("Survived", axis=1)
        y_test = val_df["Survived"]

    # Выбрать только числовые колонки
    x_train = x_train.select_dtypes(include=["number"])
    x_test = x_test.select_dtypes(include=["number"])
    feature_names = list(x_train.columns)

    logger.info(f"Train features shape: {x_train.shape}, Val features shape: {x_test.shape}")
    logger.info(f"Train target shape: {y_train.shape}, Val target shape: {y_test.shape}")

    # Логировать гиперпараметры через ClearML connect
    if task:
        hyperparams = {
            "config_name": config_name,
            "model_type": config["model_class"],
            "random_state": random_state,
            "n_features": x_train.shape[1],
            "n_train_samples": x_train.shape[0],
            "n_val_samples": x_test.shape[0],
        }
        # Добавить параметры модели
        for param_name, param_value in config["params"].items():
            hyperparams[f"model_{param_name}"] = param_value

        task.connect(hyperparams, name="hyperparameters")

    # Создать и обучить модель
    logger.info(f"Creating model from config: {config_name}")
    model = create_model_from_config(config_name)

    logger.info("Training model...")
    train_start = time.time()
    model.fit(x_train, y_train)
    train_time = time.time() - train_start
    logger.info(f"Model trained in {train_time:.2f}s")

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

    # Логировать метрики через ClearML
    metrics_dict = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "train_time_seconds": train_time,
    }
    log_metrics(metrics_dict, title="Metrics")

    # Создать временную директорию для артефактов
    artifacts_dir = Path(model_output_path).parent / "artifacts_tmp"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # 1. Confusion Matrix
    cm_path = artifacts_dir / "confusion_matrix.png"
    cm_fig = plot_confusion_matrix(y_test.values, y_pred, cm_path)
    if task:
        task.get_logger().report_matplotlib_figure(
            title="Confusion Matrix",
            series="confusion_matrix",
            figure=cm_fig,
            iteration=0,
        )
    plt.close(cm_fig)
    logger.info("Confusion matrix logged")

    # 2. ROC Curve (если модель поддерживает predict_proba)
    roc_auc = None
    if hasattr(model, "predict_proba"):
        try:
            y_proba = model.predict_proba(x_test)[:, 1]
            roc_path = artifacts_dir / "roc_curve.png"
            roc_fig, roc_auc = plot_roc_curve_fig(y_test.values, y_proba, roc_path)
            if task:
                task.get_logger().report_matplotlib_figure(
                    title="ROC Curve",
                    series="roc_curve",
                    figure=roc_fig,
                    iteration=0,
                )
            plt.close(roc_fig)
            log_metrics({"roc_auc": roc_auc}, title="Metrics")
            logger.info(f"ROC curve logged (AUC: {roc_auc:.4f})")
        except Exception as e:
            logger.warning(f"Could not compute ROC curve: {e}")

    # 3. Feature Importance (для tree-based моделей)
    if hasattr(model, "feature_importances_"):
        fi_path = artifacts_dir / "feature_importance.png"
        fi_fig = plot_feature_importance(model, feature_names, fi_path)
        if fi_fig and task:
            task.get_logger().report_matplotlib_figure(
                title="Feature Importance",
                series="feature_importance",
                figure=fi_fig,
                iteration=0,
            )
            plt.close(fi_fig)
        logger.info("Feature importance logged")

    # 4. Classification Report
    clf_report = classification_report(y_test, y_pred, output_dict=True)
    clf_report_path = artifacts_dir / "classification_report.json"
    with open(clf_report_path, "w") as f:
        json.dump(clf_report, f, indent=2)
    log_artifact(clf_report_path, name="classification_report")
    logger.info("Classification report logged")

    # 5. Логировать размер модели
    model_temp_path = artifacts_dir / "model_temp.pkl"
    joblib.dump(model, model_temp_path)
    model_size_bytes = model_temp_path.stat().st_size
    log_metrics({"model_size_bytes": float(model_size_bytes)}, title="Model Info")
    logger.info(f"Model size: {model_size_bytes / 1024:.2f} KB")

    # Сохранить модель на диск и зарегистрировать в ClearML
    model_output_path_obj = Path(model_output_path)
    register_model(
        model=model,
        model_path=model_output_path_obj,
        model_name=f"titanic_{config_name}",
        tags=[config_name, config["model_class"]],
    )
    logger.info(f"Model saved and registered: {model_output_path_obj}")

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
    if roc_auc is not None:
        metrics["roc_auc"] = float(roc_auc)

    metrics_path = model_output_path_obj.parent / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    log_artifact(metrics_path, name="metrics")
    logger.info(f"Metrics saved to {metrics_path}")

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
        metrics = train_model_pipeline(
            train_data_path="data/features/train_features.csv",
            val_data_path="data/features/val_features.csv",
            model_output_path="models/model.pkl",
            config_name=config_name,
        )
        logger.info(f"Training completed. Final metrics: {metrics}")
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise
