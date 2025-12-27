# ClearML интеграция

Руководство по настройке и использованию ClearML для трекинга экспериментов.

## Обзор

ClearML — облачная платформа для:

- Трекинга ML экспериментов
- Model Registry
- Orchestration pipelines
- Data Management

---

## Получение credentials

1. Зарегистрируйтесь на [https://app.clear.ml](https://app.clear.ml) (бесплатно)
2. Войдите в аккаунт
3. Перейдите в **Settings → Workspace → Create new credentials**
4. Скопируйте **Access Key** и **Secret Key**

---

## Настройка окружения

### Вариант A: Через .env файл (рекомендуется для Docker)

```bash
# Скопировать .env.example в .env
cp .env.example .env

# Отредактировать .env и заполнить ваши credentials
# CLEARML_API_ACCESS_KEY=ваш_access_key
# CLEARML_API_SECRET_KEY=ваш_secret_key
```

### Вариант B: Через clearml-init (для локальной разработки)

```bash
uv run clearml-init
# Следовать инструкциям на экране
```

---

## Запуск экспериментов

### В Docker (рекомендуется)

```bash
# Собрать образ
docker-compose build

# Подготовить данные через DVC
docker-compose run --rm dvc

# Запустить все 18 экспериментов
docker-compose run --rm experiments

# Или запустить ClearML Pipeline
docker-compose run --rm pipeline
```

### Локально (для разработки)

```bash
# Подготовить данные
uv run dvc repro

# Запустить один эксперимент
uv run python src/models/train_model.py random_forest_medium

# Запустить все эксперименты
uv run python -m src.experiments.run_experiments --models all

# Запустить ClearML Pipeline
uv run python -m src.pipelines.clearml_pipeline --local
```

---

## Просмотр результатов

Откройте [https://app.clear.ml](https://app.clear.ml) и перейдите в:

- **Projects → titanic_classification** — список всех экспериментов
- Нажмите на эксперимент для просмотра деталей

### Вкладки эксперимента

| Вкладка | Содержимое |
|---------|------------|
| **Scalars** | Графики метрик (accuracy, f1, etc.) |
| **Plots** | Confusion matrix, ROC curve |
| **Artifacts** | Файлы (модели, отчёты) |
| **Configuration** | Параметры эксперимента |
| **Console** | Логи выполнения |

---

## Model Registry

### Просмотр моделей через CLI

```bash
# Список всех моделей
docker-compose run --rm registry list-models

# Найти лучшую модель по accuracy
docker-compose run --rm registry best-model --metric accuracy

# Сравнение моделей
docker-compose run --rm registry compare-models
```

### Через веб-интерфейс

1. Откройте [https://app.clear.ml](https://app.clear.ml)
2. Перейдите в **Models** в левом меню
3. Фильтруйте по проекту `titanic_classification`

---

## Docker-сервисы

| Сервис | Команда | Описание |
|--------|---------|----------|
| `experiments` | `docker-compose run --rm experiments` | Запустить все 18 экспериментов |
| `pipeline` | `docker-compose run --rm pipeline` | Запустить ClearML Pipeline |
| `train` | `docker-compose run --rm train random_forest_large` | Обучить одну модель |
| `dvc` | `docker-compose run --rm dvc` | Подготовить данные через DVC |
| `registry` | `docker-compose run --rm registry list-models` | Model Registry CLI |
| `jupyter` | `docker-compose up jupyter` | Jupyter Lab на порту 8888 |

---

## Архитектура Pipeline

```
prepare_data
    ↓
split_data
    ↓
    ├── feature_engineering (параллельно)
    └── validate_data       (параллельно)
         ↓
    train_model
         ↓
    evaluate_model
         ↓
    validate_model
```

Все stages автоматически логируются в ClearML с:

- Входными/выходными артефактами
- Метриками качества
- Временем выполнения
- Параметрами конфигурации

---

## Структура проекта

```
src/
├── clearml_utils/           # Утилиты для ClearML
│   ├── __init__.py
│   ├── decorators.py        # @clearml_task, @log_time
│   ├── task_utils.py        # log_metrics, log_artifact, etc.
│   └── model_utils.py       # register_model, load_model
├── models/
│   ├── train_model.py       # Обучение с ClearML трекингом
│   └── model_registry.py    # CLI для Model Registry
├── experiments/
│   └── run_experiments.py   # Массовый запуск экспериментов
└── pipelines/
    └── clearml_pipeline.py  # ClearML Pipeline (7 stages)
```

---

## Troubleshooting

### Ошибка "Could not find credentials"

Проверьте что `.env` файл существует и содержит правильные credentials:

```bash
cat .env | grep CLEARML
```

### Ошибка "No such file: train_features.csv"

Данные не подготовлены. Запустите DVC:

```bash
docker-compose run --rm dvc
```

### Эксперименты не появляются в ClearML UI

1. Проверьте credentials
2. Проверьте подключение к интернету
3. Подождите 1-2 минуты (может быть задержка синхронизации)

---

## Полезные ссылки

- [ClearML Documentation](https://clear.ml/docs/)
- [ClearML Python SDK](https://clear.ml/docs/latest/docs/references/sdk)
- [ClearML Pipelines](https://clear.ml/docs/latest/docs/pipelines)
