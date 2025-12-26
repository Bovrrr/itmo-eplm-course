"""Pydantic модели для валидации конфигураций ML моделей и pipeline."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

# ============= Enums для типов =============


class ModelType(str, Enum):
    """Типы поддерживаемых ML моделей."""

    LOGISTIC_REGRESSION = "LogisticRegression"
    SVC = "SVC"
    RANDOM_FOREST = "RandomForestClassifier"
    GRADIENT_BOOSTING = "GradientBoostingClassifier"
    CATBOOST = "CatBoostClassifier"
    KNN = "KNeighborsClassifier"


class PenaltyType(str, Enum):
    """Типы регуляризации для линейных моделей."""

    L1 = "l1"
    L2 = "l2"
    ELASTICNET = "elasticnet"
    NONE = "none"


class KernelType(str, Enum):
    """Типы ядер для SVC."""

    LINEAR = "linear"
    RBF = "rbf"
    POLY = "poly"
    SIGMOID = "sigmoid"


# ============= Базовая конфигурация =============


class BaseModelConfig(BaseModel):
    """Базовая конфигурация для всех ML моделей.

    Attributes:
        model_class: Тип модели (LogisticRegression, SVC, и т.д.)
        description: Описание конфигурации
        random_state: Seed для воспроизводимости
    """

    model_class: ModelType
    description: str = Field(..., min_length=10, max_length=200)
    random_state: int = Field(default=42, ge=0, le=2**32 - 1)

    class Config:
        """Конфигурация Pydantic модели."""

        frozen = False  # Для композиции конфигураций
        extra = "forbid"  # Запретить неизвестные поля


# ============= Конфигурации для конкретных моделей =============


class LogisticRegressionConfig(BaseModelConfig):
    """Конфигурация для LogisticRegression.

    Attributes:
        penalty: Тип регуляризации (l1, l2, elasticnet, none)
        C: Обратная сила регуляризации (меньше = сильнее регуляризация)
        solver: Алгоритм оптимизации
        max_iter: Максимальное количество итераций
        l1_ratio: Соотношение L1/L2 для elasticnet (0 = L2, 1 = L1)
    """

    model_class: Literal[ModelType.LOGISTIC_REGRESSION] = ModelType.LOGISTIC_REGRESSION
    penalty: PenaltyType
    C: float = Field(gt=0, le=100)
    solver: Literal["lbfgs", "liblinear", "saga", "sag"]
    max_iter: int = Field(default=1000, ge=100, le=10000)
    l1_ratio: float | None = Field(default=None, ge=0, le=1)

    @field_validator("l1_ratio")
    @classmethod
    def validate_l1_ratio(cls, v: float | None, info: ValidationInfo) -> float | None:
        """Валидация l1_ratio для elasticnet."""
        penalty = info.data.get("penalty")
        if penalty == PenaltyType.ELASTICNET and v is None:
            raise ValueError("l1_ratio required for elasticnet penalty")
        if penalty != PenaltyType.ELASTICNET and v is not None:
            raise ValueError("l1_ratio only for elasticnet penalty")
        return v

    @model_validator(mode="after")
    def validate_solver_penalty(self) -> "LogisticRegressionConfig":
        """Валидация совместимости solver и penalty."""
        incompatible = {
            ("lbfgs", PenaltyType.L1),
            ("sag", PenaltyType.L1),
            ("liblinear", PenaltyType.ELASTICNET),
        }
        if (self.solver, self.penalty) in incompatible:
            raise ValueError(f"Incompatible: solver={self.solver}, penalty={self.penalty}")
        return self


class SVCConfig(BaseModelConfig):
    """Конфигурация для Support Vector Classifier.

    Attributes:
        kernel: Тип ядра (linear, rbf, poly, sigmoid)
        C: Параметр регуляризации
        gamma: Коэффициент ядра ('scale', 'auto' или число)
        degree: Степень полинома для poly kernel
        probability: Включить вероятностные оценки
    """

    model_class: Literal[ModelType.SVC] = ModelType.SVC
    kernel: KernelType
    C: float = Field(gt=0, le=100)
    gamma: Literal["scale", "auto"] | float = Field(default="scale")
    degree: int = Field(default=3, ge=1, le=10)
    probability: bool = Field(default=True)

    @field_validator("gamma")
    @classmethod
    def validate_gamma(cls, v: str | float) -> str | float:
        """Валидация gamma."""
        if isinstance(v, float) and (v <= 0 or v > 1):
            raise ValueError("gamma must be in (0, 1] if numeric")
        return v


class RandomForestConfig(BaseModelConfig):
    """Конфигурация для RandomForestClassifier.

    Attributes:
        n_estimators: Количество деревьев
        max_depth: Максимальная глубина деревьев
        max_features: Количество признаков для разбиения ('sqrt', 'log2' или число)
        min_samples_split: Минимальное количество семплов для разбиения
        min_samples_leaf: Минимальное количество семплов в листе
        n_jobs: Количество потоков (-1 = все)
    """

    model_class: Literal[ModelType.RANDOM_FOREST] = ModelType.RANDOM_FOREST
    n_estimators: int = Field(ge=10, le=1000)
    max_depth: int | None = Field(default=None, ge=1, le=50)
    max_features: Literal["sqrt", "log2"] | int | float | None = Field(default="sqrt")
    min_samples_split: int = Field(default=2, ge=2, le=20)
    min_samples_leaf: int = Field(default=1, ge=1, le=20)
    n_jobs: int = Field(default=-1)

    @field_validator("max_features")
    @classmethod
    def validate_max_features(cls, v: str | int | float | None) -> str | int | float | None:
        """Валидация max_features."""
        if isinstance(v, float) and (v <= 0 or v > 1):
            raise ValueError("max_features must be in (0, 1] if float")
        if isinstance(v, int) and v <= 0:
            raise ValueError("max_features must be > 0 if int")
        return v


class GradientBoostingConfig(BaseModelConfig):
    """Конфигурация для GradientBoostingClassifier.

    Attributes:
        learning_rate: Скорость обучения
        n_estimators: Количество деревьев
        max_depth: Максимальная глубина деревьев
        subsample: Доля семплов для обучения каждого дерева
        min_samples_split: Минимальное количество семплов для разбиения
    """

    model_class: Literal[ModelType.GRADIENT_BOOSTING] = ModelType.GRADIENT_BOOSTING
    learning_rate: float = Field(gt=0, le=1)
    n_estimators: int = Field(ge=10, le=1000)
    max_depth: int = Field(ge=1, le=20)
    subsample: float = Field(default=1.0, gt=0, le=1)
    min_samples_split: int = Field(default=2, ge=2, le=20)


class CatBoostConfig(BaseModelConfig):
    """Конфигурация для CatBoostClassifier.

    Attributes:
        iterations: Количество итераций
        depth: Глубина деревьев
        learning_rate: Скорость обучения
        verbose: Включить вывод лога
    """

    model_class: Literal[ModelType.CATBOOST] = ModelType.CATBOOST
    iterations: int = Field(ge=10, le=10000)
    depth: int = Field(ge=1, le=16)
    learning_rate: float = Field(gt=0, le=1)
    verbose: bool = Field(default=False)


class KNNConfig(BaseModelConfig):
    """Конфигурация для KNeighborsClassifier.

    Attributes:
        n_neighbors: Количество соседей
        weights: Способ взвешивания ('uniform' или 'distance')
        algorithm: Алгоритм поиска соседей
        n_jobs: Количество потоков (-1 = все)
    """

    model_class: Literal[ModelType.KNN] = ModelType.KNN
    n_neighbors: int = Field(ge=1, le=50)
    weights: Literal["uniform", "distance"]
    algorithm: Literal["auto", "ball_tree", "kd_tree", "brute"] = Field(default="auto")
    n_jobs: int = Field(default=-1)


# ============= Pipeline конфигурация =============


class DataSplitConfig(BaseModel):
    """Конфигурация разделения данных на train/val/test.

    Attributes:
        train_size: Размер train set (0.0-1.0)
        val_size: Размер validation set (0.0-1.0)
        test_size: Размер test set (0.0-1.0)
        random_state: Seed для воспроизводимости
        stratify: Использовать stratified split
    """

    train_size: float = Field(default=0.7, gt=0, lt=1)
    val_size: float = Field(default=0.15, gt=0, lt=1)
    test_size: float = Field(default=0.15, gt=0, lt=1)
    random_state: int = Field(default=42, ge=0)
    stratify: bool = Field(default=True)

    @model_validator(mode="after")
    def validate_sizes_sum(self) -> "DataSplitConfig":
        """Проверка что сумма размеров = 1."""
        total = self.train_size + self.val_size + self.test_size
        if not (0.99 <= total <= 1.01):  # Допуск на float
            raise ValueError(f"Sizes must sum to 1, got {total:.3f}")
        return self


class DataValidationConfig(BaseModel):
    """Конфигурация валидации качества данных.

    Attributes:
        check_missing: Проверять пропущенные значения
        max_missing_ratio: Максимальная доля пропусков (0.0-1.0)
        check_duplicates: Проверять дубликаты
        check_outliers: Проверять выбросы
        outlier_std_threshold: Порог для детекции выбросов (в std)
    """

    check_missing: bool = Field(default=True)
    max_missing_ratio: float = Field(default=0.1, ge=0, le=1)
    check_duplicates: bool = Field(default=True)
    check_outliers: bool = Field(default=True)
    outlier_std_threshold: float = Field(default=3.0, gt=0)


class ModelValidationConfig(BaseModel):
    """Конфигурация валидации качества модели.

    Attributes:
        min_accuracy: Минимальная допустимая accuracy
        min_f1_score: Минимальный допустимый F1-score
        max_overfitting_gap: Максимальный разрыв между train и test метриками
    """

    min_accuracy: float = Field(default=0.6, ge=0, le=1)
    min_f1_score: float = Field(default=0.5, ge=0, le=1)
    max_overfitting_gap: float = Field(default=0.1, ge=0, le=1)


class PipelineConfig(BaseModel):
    """Общая конфигурация ML pipeline.

    Attributes:
        data_split: Параметры разделения данных
        data_validation: Параметры валидации данных
        model_validation: Параметры валидации модели
        clearml_project_name: Имя проекта в ClearML
        mlflow_tracking_uri: URI для MLflow tracking (для обратной совместимости)
        mlflow_experiment_name: Имя эксперимента в MLflow (для обратной совместимости)
    """

    data_split: DataSplitConfig = Field(default_factory=DataSplitConfig)
    data_validation: DataValidationConfig = Field(default_factory=DataValidationConfig)
    model_validation: ModelValidationConfig = Field(default_factory=ModelValidationConfig)
    clearml_project_name: str = Field(default="titanic_classification")
    mlflow_tracking_uri: str = Field(default="file:./mlruns")
    mlflow_experiment_name: str = Field(default="titanic_classification")


# ============= Union тип для всех моделей =============

ModelConfig = (
    LogisticRegressionConfig
    | SVCConfig
    | RandomForestConfig
    | GradientBoostingConfig
    | CatBoostConfig
    | KNNConfig
)
