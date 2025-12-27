# Воспроизводимость результатов

Руководство по полному воспроизведению результатов проекта.

## Гарантии воспроизводимости

Проект обеспечивает воспроизводимость на нескольких уровнях:

| Уровень | Механизм | Файл |
|---------|----------|------|
| Python зависимости | UV lock file | `uv.lock` |
| Данные | DVC версионирование | `.dvc/`, `*.dvc` |
| Pipeline | DVC lock file | `dvc.lock` |
| Конфигурации | Git + Pydantic | `configs/*.yaml` |
| Random seeds | Фиксированные seeds | `random_state=42` |
| Docker | Containerization | `Dockerfile` |

---

## Предварительные требования

| Компонент | Версия | Проверка |
|-----------|--------|----------|
| Python | >= 3.13 | `python --version` |
| UV | >= 0.5 | `uv --version` |
| Git | >= 2.30 | `git --version` |
| Docker | >= 20.10 | `docker --version` (опционально) |

---

## Полное воспроизведение

### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/Bovrrr/itmo-eplm-course.git
cd itmo-eplm-course
```

### Шаг 2: Установка зависимостей

```bash
# UV установит точные версии из uv.lock
uv sync
```

!!! note "Фиксированные версии"
    `uv.lock` содержит хэши всех зависимостей, гарантируя идентичное окружение.

### Шаг 3: Загрузка данных

```bash
# Загрузить версионированные данные из DVC remote
uv run dvc pull
```

### Шаг 4: Запуск ML pipeline

```bash
# Выполнить все stages
uv run dvc repro
```

### Шаг 5: Проверка результатов

```bash
# Просмотр метрик
uv run dvc metrics show

# Сравнение с эталоном
cat models/metrics.json
```

**Ожидаемые метрики (RandomForest medium):**
```json
{
  "accuracy": 0.6842,
  "precision": 0.6122,
  "recall": 0.6383,
  "f1_score": 0.625,
  "roc_auc": 0.762
}
```

---

## Воспроизведение через Docker

Docker обеспечивает полную изоляцию окружения.

### Сборка образа

```bash
docker build -t itmo-eplm-course:latest .
```

### Запуск pipeline

```bash
# Подготовка данных
docker-compose run --rm dvc

# Запуск экспериментов
docker-compose run --rm experiments

# Или полный pipeline
docker-compose run --rm app uv run dvc repro
```

### Просмотр результатов

```bash
# ClearML Web UI
# Открыть https://app.clear.ml → Projects → titanic_classification
```

---

## Проверка воспроизводимости

### Тест 1: Идентичность метрик

```bash
# 1. Сохранить текущие метрики
cp models/metrics.json metrics_before.json

# 2. Очистить результаты
rm -rf data/processed data/features models/*.pkl models/*.json

# 3. Переобучить
uv run dvc repro

# 4. Сравнить
diff metrics_before.json models/metrics.json
# Результат: нет различий
```

### Тест 2: Кросс-платформенность

```bash
# На другой машине/ОС
git clone <repo>
cd itmo-eplm-course
uv sync
uv run dvc pull
uv run dvc repro
uv run dvc metrics show
# Метрики должны совпадать
```

---

## Random Seeds

Все стохастические операции используют фиксированные seeds:

| Компонент | Seed | Местоположение |
|-----------|------|----------------|
| Train/test split | 42 | `src/data/split_dataset.py` |
| Модели sklearn | 42 | `configs/model/*.yaml` |
| CatBoost | 42 | `configs/model/catboost_*.yaml` |

---

## Возможные причины различий

Если результаты отличаются, проверьте:

1. **Версии зависимостей**
   ```bash
   uv pip list | grep -E "scikit-learn|catboost|numpy"
   ```

2. **Версия Python**
   ```bash
   python --version
   # Должна быть 3.13.x
   ```

3. **Данные**
   ```bash
   uv run dvc status
   # Не должно быть изменений
   ```

4. **Конфигурации**
   ```bash
   git status configs/
   # Не должно быть изменений
   ```

---

## Скрипт очистки

Для полного сброса результатов:

```bash
#!/bin/bash
# scripts/clean_all.sh

echo "Cleaning all pipeline outputs..."

# Удалить обработанные данные
rm -f data/processed/*.csv
rm -f data/features/*.csv

# Удалить модели
rm -f models/*.pkl
rm -rf models/experiments/

# Удалить метрики
find data/processed -name "*.json" -delete 2>/dev/null
find models -name "*.json" -delete 2>/dev/null

# Удалить plots
rm -rf models/plots/

echo "Cleanup completed"
```

Использование:
```bash
bash scripts/clean_all.sh
uv run dvc repro
```

---

## Дополнительные ресурсы

- [DVC Reproducibility](https://dvc.org/doc/use-cases/versioning-data-and-models)
- [UV Lock Files](https://github.com/astral-sh/uv)
- [Версионирование](versioning.md)
