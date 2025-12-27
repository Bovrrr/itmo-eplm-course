# Версионирование данных и моделей

Этот документ описывает систему версионирования данных и моделей в проекте.

## Обзор

Проект использует два инструмента для версионирования:

| Инструмент | Назначение |
|------------|------------|
| **DVC** | Версионирование данных и воспроизводимый pipeline |
| **ClearML** | Отслеживание экспериментов, Model Registry, orchestration |

!!! note "Примечание"
    MLflow был заменён на ClearML в ДЗ 5. Подробнее о ClearML см. [ClearML интеграция](clearml.md).

---

## DVC (Data Version Control)

### Инициализация DVC

DVC уже инициализирован в проекте (`.dvc/` директория). Для повторной инициализации:

```bash
uv run dvc init
```

### Remote Storage

Remote storage настроено для локального хранилища:

```bash
# Текущая конфигурация
uv run dvc remote list

# Пересконфигурирование (если необходимо)
uv run dvc remote add -d myremote /tmp/dvc_storage
```

**Опции для remote storage:**

| Тип | Пример | Описание |
|-----|--------|----------|
| Локально | `/tmp/dvc_storage` | Текущая конфигурация |
| В проекте | `./dvc_storage` | Версионирование с проектом |
| S3/AWS | `s3://bucket-name/path` | Облачное хранилище |
| MinIO | `s3://minio:9000/bucket` | Локальный S3 |

### Pipeline с DVC

Pipeline определен в `dvc.yaml`:

```bash
# Просмотр структуры pipeline
uv run dvc dag

# Запуск pipeline (выполнит все stage если входные данные изменились)
uv run dvc repro

# Принудительное переобучение всех stages
uv run dvc repro --force
```

#### Stages в pipeline

| Stage | Входные данные | Выходные данные | Скрипт |
|-------|----------------|-----------------|--------|
| prepare | `data/raw/titanic.csv` | `data/processed/titanic_processed.csv` | `src/data/make_dataset.py` |
| split | `data/processed/titanic_processed.csv` | `train.csv`, `val.csv`, `test.csv` | `src/data/split_dataset.py` |
| train | `train.csv`, `val.csv` | `models/model.pkl` | `src/models/train_model.py` |
| evaluate | `model.pkl`, `test.csv` | `models/evaluation_metrics.json` | `src/models/evaluate_model.py` |

### Работа с версиями данных

```bash
# Добавить данные под версионирование
uv run dvc add data/raw/titanic.csv
# Это создаст файл data/raw/titanic.csv.dvc

# Пушить данные в remote storage
uv run dvc push

# Пулить данные из remote storage (после клонирования репо)
uv run dvc pull

# Просмотр истории версий (если используется Git)
git log --oneline -- data/raw/titanic.csv.dvc
```

---

## ClearML (Experiment Tracking)

ClearML используется для:

- **Трекинга экспериментов** — параметры, метрики, артефакты
- **Model Registry** — хранение и версионирование моделей
- **Pipelines** — оркестрация ML workflows

### Что логируется при обучении

При запуске `src/models/train_model.py`, модель автоматически логирует в ClearML:

**Параметры:**

- `model_type` — тип модели (RandomForest, SVC, etc.)
- `n_estimators` — количество деревьев
- `test_size` — размер test set
- `random_state` — seed для воспроизводимости
- `n_features` — количество признаков

**Метрики:**

- `accuracy` — точность модели
- `precision` — precision score
- `recall` — recall score
- `f1_score` — F1-мера
- `roc_auc` — площадь под ROC-кривой

**Артефакты:**

- `model/` — сохраненная модель (sklearn format)
- `confusion_matrix.png` — матрица ошибок
- `roc_curve.png` — ROC-кривая

### Просмотр результатов

```bash
# Откройте ClearML веб-интерфейс
# https://app.clear.ml
# Projects → titanic_classification
```

Подробнее см. [ClearML интеграция](clearml.md).

---

## Полный workflow

### Первый запуск

```bash
# 1. Установить зависимости
uv sync

# 2. Настроить ClearML credentials (один раз)
uv run clearml-init

# 3. Запустить полный DVC pipeline
uv run dvc repro

# 4. Запушить данные в DVC remote
uv run dvc push

# 5. Коммитить изменения в Git
git add dvc.yaml dvc.lock .dvc/config
git commit -m "feat: инициализирован DVC pipeline"
```

### Воспроизведение результатов (после clone)

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd itmo-eplm-course

# 2. Установить зависимости
uv sync

# 3. Загрузить версионированные данные
uv run dvc pull

# 4. Воспроизвести pipeline
uv run dvc repro

# 5. Просмотреть результаты в ClearML
# https://app.clear.ml → Projects → titanic_classification
```

### После обновления кода или данных

```bash
# Если изменились исходные данные
uv run dvc repro

# Если изменился только код модели
uv run dvc repro --single-stage train

# Просмотреть что изменилось
uv run dvc diff

# Запушить новые версии
uv run dvc push
```

---

## Воспроизводимость

### Фиксированные версии

Воспроизводимость обеспечивается:

| Компонент | Механизм |
|-----------|----------|
| Python зависимости | `uv.lock` — точные версии |
| DVC pipeline | `dvc.lock` — хэши входов/выходов |
| Random seeds | `random_state=42` везде |

### Проверка воспроизводимости

```bash
# 1. Очистить результаты
rm -rf data/processed models/model.pkl dvc.lock

# 2. Загрузить исходные данные
uv run dvc pull

# 3. Переобучить модель
uv run dvc repro

# 4. Проверить что результаты совпадают
# (метрики в models/metrics.json должны быть идентичны)
```

---

## Команды для ежедневной работы

```bash
# Запуск полного pipeline
uv run dvc repro

# Загрузить новые версии данных
uv run dvc pull

# Загрузить/синхронизировать результаты
uv run dvc push

# Проверить статус pipeline
uv run dvc status

# Просмотр DAG
uv run dvc dag

# Запуск только обучения
uv run dvc repro --single-stage train

# Запуск экспериментов через ClearML
uv run python -m src.experiments.run_experiments --models all
```

---

## Дополнительные ресурсы

- [DVC Documentation](https://dvc.org/doc)
- [ClearML Documentation](https://clear.ml/docs/)
- [ClearML интеграция](clearml.md)
- [Воспроизводимость](reproducibility.md)
