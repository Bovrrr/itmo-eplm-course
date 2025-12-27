# API Reference

Документация модулей и функций проекта.

## Обзор модулей

| Модуль | Описание |
|--------|----------|
| `src.data` | Загрузка, обработка и разделение данных |
| `src.models` | Обучение, оценка и валидация ML моделей |
| `src.experiments` | Массовый запуск и анализ экспериментов |
| `src.clearml_utils` | Интеграция с ClearML |
| `src.mlflow_utils` | *(Legacy, не используется)* |
| `src.config` | Управление конфигурациями через Pydantic |

---

## src.data

Модуль для работы с данными.

### make_dataset

Загрузка и первичная обработка данных Titanic.

```python
from src.data.make_dataset import prepare_data

# Подготовка данных
prepare_data(
    input_path=Path("data/raw/titanic.csv"),
    output_path=Path("data/processed/titanic_processed.csv")
)
```

::: src.data.make_dataset
    options:
      show_root_heading: false
      members:
        - load_titanic_dataset
        - prepare_data

### split_dataset

Разделение данных на train/val/test с стратификацией.

```python
from src.data.split_dataset import split_data

# Разделение 70/15/15
split_data(
    input_path=Path("data/processed/titanic_processed.csv"),
    output_dir=Path("data/processed/"),
    train_size=0.7,
    val_size=0.15,
    test_size=0.15
)
```

---

## src.models

Модуль для обучения и оценки моделей.

### train_model

Обучение модели с логированием в ClearML.

```python
from src.models.train_model import train_model_pipeline

# Обучение с конфигурацией
metrics = train_model_pipeline(
    train_data_path="data/features/train_features.csv",
    val_data_path="data/features/val_features.csv",
    model_output_path="models/model.pkl",
    config_name="random_forest_medium"
)
```

::: src.models.train_model
    options:
      show_root_heading: false
      members:
        - create_model_from_config
        - train_model_pipeline

### model_configs

Загрузка конфигураций моделей из YAML.

```python
from src.models.model_configs import get_model_config, get_all_config_names

# Получить список всех конфигураций
names = get_all_config_names()
# ['random_forest_small', 'random_forest_medium', 'svc_linear', ...]

# Получить конкретную конфигурацию
config = get_model_config("catboost_deep")
```

---

## src.experiments

Модуль для массового запуска экспериментов.

### run_experiments

CLI для запуска множества экспериментов.

```bash
# Запуск всех 18 экспериментов
uv run python -m src.experiments.run_experiments --models all

# Запуск конкретных моделей
uv run python -m src.experiments.run_experiments --models "svc_linear,random_forest_medium"
```

### analyze_experiments

Анализ результатов и генерация визуализаций.

```bash
# Анализ топ-18 моделей
uv run python -m src.experiments.analyze_experiments --top-n 18
```

**Создаваемые файлы:**

- `reports/figures/metrics_comparison.png`
- `reports/figures/metrics_heatmap.png`
- `reports/experiment_results.csv`
- `reports/best_models.json`

---

## src.clearml_utils

Утилиты для интеграции с ClearML.

### decorators

Декораторы для автоматического логирования.

```python
from src.clearml_utils.decorators import clearml_task, log_time

@clearml_task(project_name="titanic_classification", task_name="train")
def train():
    # Автоматически создаёт ClearML Task
    pass

@log_time
def process_data():
    # Логирует время выполнения
    pass
```

### task_utils

Утилиты для работы с ClearML Task.

```python
from src.clearml_utils.task_utils import log_metrics, log_artifact

# Логирование метрик
log_metrics({"accuracy": 0.85, "f1_score": 0.82})

# Логирование артефакта
log_artifact("model", "models/model.pkl")
```

### model_utils

Работа с ClearML Model Registry.

```python
from src.clearml_utils.model_utils import register_model, load_model

# Регистрация модели
register_model(
    model=trained_model,
    model_name="titanic_classifier",
    tags=["production", "v1"]
)

# Загрузка модели
model = load_model("titanic_classifier", version="latest")
```

---

## src.config

Управление конфигурациями через Pydantic.

### schemas

Pydantic схемы для валидации конфигураций.

```python
from src.config.schemas import RandomForestConfig, SVCConfig

# Создание конфигурации с валидацией
config = RandomForestConfig(
    model_class="RandomForestClassifier",
    n_estimators=100,
    max_depth=10,
    random_state=42
)
```

**Доступные классы:**

- `BaseModelConfig` — базовый класс
- `LogisticRegressionConfig`
- `SVCConfig`
- `RandomForestConfig`
- `GradientBoostingConfig`
- `CatBoostConfig`
- `KNNConfig`

### loader

Загрузка конфигураций из YAML с валидацией.

```python
from src.config.loader import load_model_config

# Загрузка с валидацией
config = load_model_config(Path("configs/model/random_forest_medium.yaml"))
```

---

## Примеры использования

### Полный pipeline обучения

```python
from pathlib import Path
from src.data.make_dataset import prepare_data
from src.data.split_dataset import split_data
from src.models.train_model import train_model_pipeline

# 1. Подготовка данных
prepare_data(
    input_path=Path("data/raw/titanic.csv"),
    output_path=Path("data/processed/titanic_processed.csv")
)

# 2. Разделение данных
split_data(
    input_path=Path("data/processed/titanic_processed.csv"),
    output_dir=Path("data/processed/")
)

# 3. Обучение модели
metrics = train_model_pipeline(
    train_data_path="data/processed/train.csv",
    val_data_path="data/processed/val.csv",
    model_output_path="models/model.pkl",
    config_name="catboost_deep"
)

print(f"Accuracy: {metrics['accuracy']:.4f}")
print(f"F1-Score: {metrics['f1_score']:.4f}")
```

### Массовое сравнение моделей

```python
from src.models.model_configs import get_all_config_names
from src.models.train_model import train_model_pipeline

results = {}
for config_name in get_all_config_names():
    metrics = train_model_pipeline(
        train_data_path="data/processed/train.csv",
        val_data_path="data/processed/val.csv",
        model_output_path=f"models/experiments/{config_name}/model.pkl",
        config_name=config_name
    )
    results[config_name] = metrics

# Найти лучшую модель
best_model = max(results.items(), key=lambda x: x[1]['accuracy'])
print(f"Best model: {best_model[0]} with accuracy {best_model[1]['accuracy']:.4f}")
```
