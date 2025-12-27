# Быстрый старт

Запуск ML pipeline за 5 минут.

## Предварительные требования

Убедитесь, что выполнены шаги из [Установка](installation.md):

- [x] UV установлен
- [x] Репозиторий клонирован
- [x] Зависимости установлены (`uv sync`)

---

## Шаг 1: Подготовка данных

```bash
# Загрузка данных из DVC remote (если настроено)
uv run dvc pull

# Или подготовка данных с нуля
uv run python -m src.data.make_dataset
```

!!! info "Датасет Titanic"
    Проект использует датасет Titanic из seaborn. При первом запуске данные загружаются автоматически.

---

## Шаг 2: Запуск DVC Pipeline

### Просмотр структуры pipeline

```bash
uv run dvc dag
```

**Результат:**
```
           +---------+
           | prepare |
           +---------+
                *
           +-------+
           | split |
           +-------+**
        ***           ***
+---------------+         +---------------------+
| validate_data |         | feature_engineering |
+---------------+         +---------------------+
                               **        **
                         +-------+
                         | train |
                         +-------+
                        +----------+
                        | evaluate |
                        +----------+
                   +----------------+
                   | validate_model |
                   +----------------+
```

### Запуск полного pipeline

```bash
uv run dvc repro
```

Это выполнит все 7 stages:

1. **prepare** — загрузка и обработка данных
2. **split** — разделение на train/val/test
3. **feature_engineering** — создание признаков
4. **validate_data** — валидация качества данных
5. **train** — обучение модели
6. **evaluate** — оценка на test set
7. **validate_model** — проверка качества модели

---

## Шаг 3: Просмотр результатов

### Метрики

```bash
# Просмотр всех метрик
uv run dvc metrics show

# В формате таблицы
uv run dvc metrics show --md
```

**Пример вывода:**
```
Path                           accuracy    f1_score    precision
models/metrics.json            0.6842      0.625       0.6122
```

### MLflow UI

```bash
uv run mlflow ui --port 5000
```

Откройте [http://localhost:5000](http://localhost:5000) для просмотра:

- Все запуски экспериментов
- Параметры и метрики
- Артефакты (модели, графики)

---

## Шаг 4: Обучение с разными конфигурациями

### Доступные конфигурации

```bash
ls configs/model/
```

**18 конфигураций:**
- `random_forest_*.yaml` — Random Forest (4 варианта)
- `gradient_boosting_*.yaml` — Gradient Boosting (3 варианта)
- `catboost_*.yaml` — CatBoost (2 варианта)
- `logistic_regression_*.yaml` — Logistic Regression (4 варианта)
- `svc_*.yaml` — SVC (3 варианта)
- `knn_*.yaml` — KNN (2 варианта)

### Запуск с конкретной конфигурацией

```bash
# Обучение CatBoost
uv run python src/models/train_model.py catboost_deep

# Обучение SVC с RBF kernel
uv run python src/models/train_model.py svc_rbf_c1
```

### Массовый запуск всех экспериментов

```bash
uv run python -m src.experiments.run_experiments --models all
```

---

## Шаг 5: Анализ экспериментов

```bash
# Генерация визуализаций и таблиц
uv run python -m src.experiments.analyze_experiments --top-n 18
```

**Создаваемые файлы:**
- `reports/figures/` — графики сравнения
- `reports/experiment_results.csv` — полная таблица результатов
- `reports/best_models.json` — лучшие модели по метрикам

---

## Docker (альтернатива)

### Подготовка данных

```bash
docker-compose run --rm dvc
```

### Запуск всех экспериментов

```bash
docker-compose run --rm experiments
```

### Просмотр в ClearML

Откройте [https://app.clear.ml](https://app.clear.ml) → Projects → titanic_classification

---

## Что дальше?

- [Версионирование данных](../guides/versioning.md) — DVC и MLflow
- [ClearML интеграция](../guides/clearml.md) — облачный трекинг
- [API Reference](../api/index.md) — документация модулей
- [Результаты экспериментов](../experiments/results.md) — анализ моделей
