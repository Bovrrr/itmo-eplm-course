# Версионирование данных и моделей

Этот документ описывает систему версионирования данных и моделей в проекте itmo-eplm-course.

## Обзор

Проект использует два инструмента для версионирования:

- **DVC (Data Version Control)** - для версионирования данных и воспроизводимого pipeline
- **MLflow** - для отслеживания экспериментов и версионирования моделей

## 1. DVC (Data Version Control)

### 1.1 Инициализация DVC

DVC уже инициализирован в проекте (`.dvc/` директория). Для повторной инициализации:

```bash
uv run dvc init
```

### 1.2 Remote Storage

Remote storage настроено для локального хранилища:

```bash
# Текущая конфигурация
uv run dvc remote list

# Пересконфигурирование (если необходимо)
uv run dvc remote add -d myremote /tmp/dvc_storage
```

**Опции для remote storage:**
- **Локально** (текущая): `/tmp/dvc_storage`
- **В проекте**: `./dvc_storage` (для версионирования вместе с проектом)
- **S3/AWS**: `s3://bucket-name/path` (требуется AWS учетная запись)
- **MinIO**: `s3://minio:9000/bucket` (локальный S3-совместимый сервис)

### 1.3 Pipeline с DVC

Pipeline определен в `dvc.yaml`:

```bash
# Просмотр структуры pipeline
uv run dvc dag

# Запуск pipeline (выполнит все stage если входные данные изменились)
uv run dvc repro

# Принудительное переобучение всех stages
uv run dvc repro --force
```

#### Stages в pipeline:

1. **prepare** - загрузка и обработка raw данных
   - Входные данные: `data/raw/titanic.csv`
   - Выходные данные: `data/processed/titanic_processed.csv`
   - Скрипт: `src/data/make_dataset.py`

2. **train** - обучение модели
   - Входные данные: `data/processed/titanic_processed.csv`
   - Выходные модели: `models/model.pkl`
   - Метрики: `models/metrics.json`
   - Скрипт: `src/models/train_model.py`

### 1.4 Работа с версиями данных

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

## 2. MLflow (Model Tracking)

### 2.1 Структура MLflow

MLflow использует локальное file-based хранилище в директории `mlruns/`:

```
mlruns/
├── 0/                        # Experiment ID
│   ├── meta.yaml            # Metadata эксперимента
│   └── <run_id>/            # Каждый запуск обучения
│       ├── meta.yaml        # Metadata запуска
│       ├── params/          # Параметры модели
│       ├── metrics/         # Метрики тренировки
│       └── artifacts/       # Сохраненные артефакты (модель, графики)
```

### 2.2 Web UI

MLflow предоставляет веб-интерфейс для просмотра экспериментов и сравнения моделей:

```bash
# Запуск MLflow UI (локально)
mlflow ui --port 5000
# Открыть http://localhost:5000

# Или через Docker
docker-compose up mlflow
# Доступна на http://localhost:5000
```

### 2.3 Логирование экспериментов

При запуске `src/models/train_model.py`, модель автоматически логирует:

**Параметры:**
- `model_type` - тип модели (RandomForest)
- `n_estimators` - количество деревьев
- `test_size` - размер test set
- `random_state` - seed для воспроизводимости
- `n_features` - количество признаков

**Метрики:**
- `accuracy` - точность модели
- `precision` - precision score
- `recall` - recall score
- `f1_score` - F1-мера

**Артефакты:**
- `model/` - сохраненная модель (sklearn format)
- `metrics.json` - файл с метриками

### 2.4 Сравнение версий моделей

В веб-интерфейсе MLflow можно:

1. Просмотреть все запуски эксперимента
2. Сравнить две или более версии модели по метрикам
3. Просмотреть параметры каждой версии
4. Скачать артефакты (модель, метрики)

## 3. Полный workflow: запуск и воспроизведение

### 3.1 Первый запуск

```bash
# 1. Установить зависимости
uv sync

# 2. Инициализировать DVC (если еще не инициализирован)
uv run dvc init

# 3. Запустить полный pipeline
uv run dvc repro

# 4. Запушить данные в DVC remote
uv run dvc push

# 5. Коммитить изменения в Git
git add dvc.yaml dvc.lock .dvc/config
git commit -m "feat: инициализирован DVC pipeline"
```

### 3.2 Воспроизведение результатов (после clone)

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd itmo-eplm-course

# 2. Установить зависимости
uv sync

# 3. Загрузить версионированные данные из DVC remote
uv run dvc pull

# 4. Воспроизвести pipeline (если необходимо переобучение)
uv run dvc repro

# 5. Просмотреть результаты в MLflow UI
mlflow ui
# Открыть http://localhost:5000
```

### 3.3 После обновления кода или данных

```bash
# Если изменились исходные данные
uv run dvc repro

# Если изменился только код модели
uv run dvc repro --single-stage train

# Просмотреть что изменилось в pipeline
uv run dvc diff

# Запушить новые версии данных и моделей
uv run dvc push
```

## 4. Воспроизводимость

### 4.1 Фиксированные версии

Воспроизводимость обеспечивается:

1. **Python зависимости**: зафиксированы в `uv.lock`
   ```bash
   uv sync  # Всегда устанавливает точные версии
   ```

2. **DVC pipeline**: версионируется через `dvc.lock`
   ```bash
   git log -- dvc.lock  # История изменений pipeline
   ```

3. **Seed для моделей**: установлен `random_state=42` в train_model.py

### 4.2 Проверка воспроизводимости

```bash
# 1. Очистить результаты
rm -rf data/processed models/model.pkl dvc.lock mlruns

# 2. Загрузить исходные данные
uv run dvc pull

# 3. Переобучить модель
uv run dvc repro

# 4. Проверить что результаты совпадают
# (метрики в models/metrics.json должны быть идентичны)
```

## 5. Docker и контейнеризация

### 5.1 Запуск pipeline в Docker

```bash
# Собрать образ
docker-compose build

# Запустить обучение в контейнере
docker-compose run --rm app uv run dvc repro

# Или с Jupyter для интерактивной работы
docker-compose up jupyter
# Jupyter доступен на http://localhost:8888
```

### 5.2 MLflow UI в Docker

```bash
# Запустить MLflow UI сервис
docker-compose up mlflow

# Доступен на http://localhost:5000
# mlruns/ директория монтирована как volume
```

## 6. Команды для ежедневной работы

```bash
# Запуск полного pipeline
make train
# или
uv run dvc repro

# Просмотр MLflow экспериментов
make mlflow
# или
mlflow ui

# Загрузить новые версии данных
uv run dvc pull

# Загрузить/синхронизировать результаты
uv run dvc push

# Проверить статус pipeline
uv run dvc status

# Просмотр DAG
uv run dvc dag

# Запуск только обучения (без подготовки данных)
uv run dvc repro --single-stage train
```

## 7. Решение проблем

### DVC problems

**Проблема:** `ERROR: cannot commit lock file` при `dvc repro`
**Решение:** Убедиться что `data/raw/titanic.csv` существует
```bash
uv run python src/data/make_dataset.py  # Создаст sample данные
```

**Проблема:** `ERROR: failed to fetch` при `dvc pull`
**Решение:** Проверить что remote storage доступен
```bash
ls /tmp/dvc_storage  # Должна существовать директория
```

### MLflow problems

**Проблема:** MLflow UI не показывает эксперименты
**Решение:** Убедиться что `mlruns/` директория существует и не gitignored
```bash
ls -la mlruns/
git status mlruns/  # Должны быть untracked или в .gitignore
```

**Проблема:** Model Registry не регистрирует модели
**Решение:** Убедиться что модель логируется правильно в train_model.py
```python
mlflow.sklearn.log_model(model, "model", registered_model_name="titanic_classifier")
```

## 8. Дополнительные ресурсы

- [DVC Documentation](https://dvc.org/doc)
- [MLflow Documentation](https://mlflow.org/docs/latest)
- [Project Structure](../README.md)
- [Setup Instructions](./SETUP.md)
