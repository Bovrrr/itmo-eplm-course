# ITMO EPLM Course

Проект для курса "Инженерные практики в ML" (ИТМО).

[![Documentation](https://img.shields.io/badge/docs-MkDocs-blue.svg)](https://bovrrr.github.io/itmo-eplm-course/)
[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![UV](https://img.shields.io/badge/UV-Package%20Manager-blueviolet.svg)](https://github.com/astral-sh/uv)

## Описание

Настройка полнофункционального рабочего места Data Scientist с использованием современных инженерных практик. Проект демонстрирует применение best practices для Machine Learning проектов с фокусом на качество кода, воспроизводимость и автоматизацию.

**Датасет:** Titanic (классификация выживания пассажиров)

**Цель:** Создать ML проект с акцентом на инженерные аспекты, а не на сложность ML задачи.

## Структура проекта

```
itmo-eplm-course/
├── data/
│   ├── raw/              # Исходные данные
│   ├── interim/          # Промежуточные данные
│   ├── processed/        # Обработанные данные
│   └── external/         # Внешние данные
├── models/               # Сохраненные модели
├── notebooks/            # Jupyter notebooks для исследований
├── src/                  # Исходный код проекта
│   ├── data/             # Скрипты для работы с данными
│   ├── features/         # Создание признаков
│   ├── models/           # Код моделей
│   └── visualization/    # Визуализация
├── tests/                # Тесты
├── docs/                 # Документация
├── reports/              # Отчеты и результаты
│   └── figures/          # Графики и визуализации
├── references/           # Справочные материалы
├── .github/
│   └── workflows/        # CI/CD конфигурации
├── pyproject.toml        # Конфигурация проекта и зависимости
├── Dockerfile            # Docker образ
├── docker-compose.yml    # Docker Compose конфигурация
├── .pre-commit-config.yaml # Pre-commit hooks
├── .gitignore            # Git ignore правила
└── README.md             # Этот файл
```

## Требования

- Python 3.14+
- UV 0.8+ (современный пакетный менеджер для Python)
- Docker (опционально, для контейнеризации)
- Git

## Установка

### Быстрый старт

#### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd itmo-eplm-course
git checkout hw01
```

#### 2. Установка UV (если не установлен)

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 3. Установка зависимостей

```bash
# Создание виртуального окружения и установка зависимостей
uv sync

# Установка dev-зависимостей для разработки
uv sync --all-extras
```

#### 4. Активация pre-commit hooks

```bash
uv run pre-commit install
```

#### 5. Проверка установки

```bash
# Проверка версий
uv run python --version
uv run pytest --version

# Запуск тестов
uv run pytest

# Запуск проверок качества кода
uv run pre-commit run --all-files
```

## Документация

Полная документация проекта доступна на [GitHub Pages](https://bovrrr.github.io/itmo-eplm-course/).

### Локальная сборка документации

```bash
# Установка зависимостей для документации
uv sync --group docs

# Запуск локального сервера документации
uv run mkdocs serve
# Открыть http://localhost:8000

# Сборка статических файлов
uv run mkdocs build
```

### Структура документации

- **Начало работы** — установка и быстрый старт
- **Руководства** — DVC, ClearML, воспроизводимость
- **API Reference** — документация модулей
- **Эксперименты** — результаты и сравнение моделей

## Использование

### Разработка

#### Запуск Jupyter Notebook

```bash
uv run jupyter notebook
```

#### Запуск скриптов

```bash
# Пример запуска скрипта препроцессинга
uv run python src/data/make_dataset.py
```

#### Проверка качества кода

```bash
# Линтинг с Ruff
uv run ruff check .

# Форматирование кода
uv run ruff format .

# Проверка типов с MyPy
uv run mypy src/

# Проверка безопасности с Bandit
uv run bandit -r src/
```

#### Запуск тестов

```bash
# Запуск всех тестов
uv run pytest

# Запуск с покрытием кода
uv run pytest --cov=src --cov-report=html

# Просмотр отчета о покрытии
open htmlcov/index.html
```

### Docker

#### Сборка Docker образа

```bash
docker build -t itmo-eplm-course:latest .
```

#### Запуск контейнера

```bash
# Запуск основного контейнера
docker run -it --rm itmo-eplm-course:latest

# Запуск с монтированием данных
docker run -it --rm -v $(pwd)/data:/app/data itmo-eplm-course:latest
```

#### Использование Docker Compose

```bash
# Запуск сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка сервисов
docker-compose down
```

### Управление зависимостями

#### Добавление новой зависимости

```bash
# Основная зависимость
uv add package-name

# Dev зависимость
uv add --dev package-name

# С конкретной версией
uv add "package-name>=1.0.0,<2.0.0"
```

#### Обновление зависимостей

```bash
# Обновить все зависимости
uv lock --upgrade

# Обновить конкретный пакет
uv lock --upgrade-package package-name
```

## Инструменты качества кода

Проект использует следующие инструменты для обеспечения качества кода:

- **Ruff** - быстрый линтер и форматтер (замена Black + isort + flake8)
- **MyPy** - статическая проверка типов
- **Bandit** - проверка безопасности кода
- **pytest** - фреймворк для тестирования
- **pre-commit** - автоматические проверки перед коммитом

Все проверки запускаются автоматически при коммите через pre-commit hooks.

## Стиль кода

Проект следует следующим стандартам:

- Максимальная длина строки: 100 символов
- Стиль импортов: сортировка через isort (встроен в Ruff)
- Стиль кавычек: двойные кавычки
- Проверка типов: обязательна для всего кода в `src/`
- Conventional Commits для сообщений коммитов

## Разработка

### Процесс разработки

1. Создайте feature ветку: `git checkout -b feature/your-feature`
2. Внесите изменения
3. Запустите проверки: `uv run pre-commit run --all-files`
4. Закоммитьте изменения: `git commit -m "feat: описание изменения"`
5. Запушьте ветку: `git push origin feature/your-feature`
6. Создайте Pull Request

### Стиль коммитов

Проект использует [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - новая функциональность
- `fix:` - исправление бага
- `docs:` - изменения в документации
- `style:` - форматирование кода
- `refactor:` - рефакторинг
- `test:` - добавление тестов
- `chore:` - вспомогательные изменения

## Документация

Подробная документация доступна в директории `docs/`:

- [SETUP.md](docs/SETUP.md) - Детальная инструкция по настройке окружения
- [REPORT.md](REPORT.md) - Отчет о выполнении ДЗ 1

## Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## Авторы

- Baurzhan - [GitHub](https://github.com/Bovrrr)

## Благодарности

- [Cookiecutter Data Science](https://drivendata.github.io/cookiecutter-data-science/) - шаблон структуры проекта
- ИТМО - курс "Инженерные практики в ML"
