# ITMO EPLM Course

Проект курса "Инженерные практики в ML" (ИТМО).

[![Documentation](https://img.shields.io/badge/docs-MkDocs-blue.svg)](https://bovrrr.github.io/itmo-eplm-course/)
[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![ClearML](https://img.shields.io/badge/ClearML-Experiment%20Tracking-brightgreen.svg)](https://clear.ml/)

## О проекте

**Цель:** Демонстрация MLOps практик на примере задачи классификации (Titanic).

Проект создан для изучения и применения современных инженерных подходов к ML-разработке, с акцентом на воспроизводимость, автоматизацию и качество кода.

### Ключевые особенности

- **Воспроизводимый ML Pipeline** — DVC + фиксированные seeds (`random_state=42`)
- **Трекинг экспериментов** — ClearML (18 конфигураций моделей)
- **Версионирование** — данные (DVC), код (Git), модели (ClearML Model Registry)
- **Контейнеризация** — Docker + Docker Compose
- **Качество кода** — Ruff, MyPy (strict), Bandit, pre-commit hooks
- **Документация** — MkDocs Material + автогенерация API

---

## Быстрый старт

```bash
# Клонирование и установка
git clone https://github.com/Bovrrr/itmo-eplm-course.git
cd itmo-eplm-course
uv sync

# Запуск ML pipeline
uv run dvc repro

# Просмотр результатов
uv run dvc metrics show
```

> **Требования:** Python 3.13+, [UV](https://github.com/astral-sh/uv), Git

---

## ML Pipeline

```text
prepare → split → feature_engineering → train → evaluate → validate_model
                      ↑
              validate_data
```

Pipeline управляется через DVC и автоматически:

- Загружает и обрабатывает данные Titanic
- Создаёт признаки и разделяет на train/val/test
- Обучает модель и логирует метрики в ClearML
- Валидирует качество модели

```bash
# Просмотр графа зависимостей
uv run dvc dag

# Принудительное переобучение
uv run dvc repro --force
```

---

## Результаты экспериментов

Проведено **18 экспериментов** с различными алгоритмами:

| Модель | Accuracy | F1-Score | Precision |
|--------|----------|----------|-----------|
| **SVC (RBF, C=1)** | **0.7105** | 0.5417 | 0.7879 |
| CatBoost (deep) | 0.7039 | **0.5946** | 0.6471 |
| RandomForest (small) | 0.7039 | 0.5714 | 0.7059 |
| LogisticRegression (L1) | 0.6908 | 0.5524 | 0.6786 |

**Лучшие результаты:**

- По Accuracy: SVC с RBF ядром
- По F1-Score: CatBoost (лучший баланс precision/recall)

Подробный анализ: [Результаты экспериментов](https://bovrrr.github.io/itmo-eplm-course/experiments/results/)

---

## Структура проекта

```text
itmo-eplm-course/
├── configs/               # Pydantic конфигурации моделей (18 файлов)
├── data/
│   ├── raw/               # Исходные данные (Titanic)
│   ├── processed/         # Обработанные данные
│   └── features/          # Признаки для обучения
├── src/
│   ├── data/              # Загрузка и обработка данных
│   ├── models/            # Обучение и оценка моделей
│   ├── experiments/       # Массовый запуск экспериментов
│   ├── clearml_utils/     # ClearML интеграция
│   └── pipelines/         # ClearML Pipelines
├── docs/                  # Документация (MkDocs)
├── tests/                 # Тесты (pytest)
├── dvc.yaml               # DVC pipeline
└── mkdocs.yml             # Конфигурация документации
```

---

## Технологии

| Категория | Инструменты |
|-----------|-------------|
| **ML** | scikit-learn, CatBoost |
| **MLOps** | DVC, ClearML |
| **Качество кода** | Ruff, MyPy, Bandit, pre-commit |
| **Документация** | MkDocs Material, mkdocstrings |
| **Контейнеризация** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |

---

## Документация

Полная документация доступна на **[GitHub Pages](https://bovrrr.github.io/itmo-eplm-course/)**.

### Разделы

- [Установка](https://bovrrr.github.io/itmo-eplm-course/getting-started/installation/) — настройка окружения
- [Быстрый старт](https://bovrrr.github.io/itmo-eplm-course/getting-started/quickstart/) — первый запуск
- [ClearML](https://bovrrr.github.io/itmo-eplm-course/guides/clearml/) — трекинг экспериментов
- [API Reference](https://bovrrr.github.io/itmo-eplm-course/api/) — документация модулей

### Локальная сборка

```bash
uv sync --group docs
uv run mkdocs serve
# Открыть http://localhost:8000
```

---

## Docker

```bash
# Подготовка данных
docker-compose run --rm dvc

# Запуск всех экспериментов
docker-compose run --rm experiments

# Jupyter Lab
docker-compose up jupyter
# Открыть http://localhost:8888
```

---

## Воспроизведение результатов

Все результаты полностью воспроизводимы благодаря:

| Компонент | Механизм |
|-----------|----------|
| Python зависимости | `uv.lock` (точные версии) |
| Данные | DVC + `dvc.lock` |
| Random seeds | `random_state=42` |
| Контейнеризация | `Dockerfile` |

```bash
# Полное воспроизведение
git clone https://github.com/Bovrrr/itmo-eplm-course.git
cd itmo-eplm-course
uv sync
uv run dvc pull
uv run dvc repro
```
