# ITMO EPLM Course

**Инженерные практики машинного обучения** — учебный проект курса ИТМО.

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![UV](https://img.shields.io/badge/UV-Package%20Manager-blueviolet.svg)](https://github.com/astral-sh/uv)
[![MkDocs](https://img.shields.io/badge/docs-MkDocs-blue.svg)](https://www.mkdocs.org/)

---

## О проекте

Этот проект демонстрирует лучшие практики разработки ML-систем:

- **Версионирование данных** с DVC
- **Трекинг экспериментов** с ClearML
- **Автоматизация pipeline** с DVC Pipelines
- **Управление конфигурациями** с Pydantic
- **Качество кода** с Ruff, MyPy, Bandit
- **Контейнеризация** с Docker

## Быстрый старт

```bash
# Клонирование репозитория
git clone https://github.com/Bovrrr/itmo-eplm-course.git
cd itmo-eplm-course

# Установка зависимостей
uv sync

# Запуск pipeline
uv run dvc repro

# Просмотр результатов
# Откройте https://app.clear.ml → Projects → titanic_classification
```

Подробнее в разделе [Установка](getting-started/installation.md).

## Структура проекта

```
itmo-eplm-course/
├── data/                  # Данные (raw, processed, features)
├── src/                   # Исходный код
│   ├── data/              # Обработка данных
│   ├── models/            # ML модели
│   ├── experiments/       # Эксперименты
│   └── clearml_utils/     # ClearML интеграция
├── configs/               # Конфигурации моделей (Pydantic)
├── docs/                  # Документация
├── tests/                 # Тесты
└── reports/               # Отчёты и визуализации
```

## Ключевые возможности

### Воспроизводимый ML Pipeline

```bash
# DVC pipeline из 7 stages
uv run dvc dag

# Полное воспроизведение
uv run dvc repro
```

### 18 конфигураций моделей

- RandomForest, GradientBoosting, CatBoost
- LogisticRegression, SVC, KNN
- Все с валидацией через Pydantic

### Трекинг экспериментов

- **ClearML**: облачный трекинг экспериментов, Model Registry, pipelines

## Навигация

<div class="grid cards" markdown>

-   :material-rocket-launch: **Начало работы**

    ---

    Установка, настройка окружения, первый запуск

    [:octicons-arrow-right-24: Установка](getting-started/installation.md)

-   :material-book-open-variant: **Руководства**

    ---

    DVC, ClearML, воспроизводимость

    [:octicons-arrow-right-24: Руководства](guides/setup.md)

-   :material-api: **API Reference**

    ---

    Документация модулей и функций

    [:octicons-arrow-right-24: API](api/index.md)

-   :material-chart-line: **Эксперименты**

    ---

    Результаты и сравнение моделей

    [:octicons-arrow-right-24: Результаты](experiments/results.md)

</div>

## Технологии

| Категория | Инструменты |
|-----------|-------------|
| Язык | Python 3.13+ |
| Пакетный менеджер | UV |
| ML | scikit-learn, CatBoost, XGBoost |
| Трекинг | ClearML |
| Версионирование | DVC, Git |
| Качество кода | Ruff, MyPy, Bandit |
| Документация | MkDocs Material |
| Контейнеризация | Docker, Docker Compose |

## Лицензия

MIT License. Подробнее в [LICENSE](https://github.com/Bovrrr/itmo-eplm-course/blob/main/LICENSE).
