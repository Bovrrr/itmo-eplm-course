# Установка

Пошаговое руководство по настройке рабочего окружения.

## Требования

### Минимальные требования

| Компонент | Версия | Назначение |
|-----------|--------|------------|
| Python | >= 3.13 | Язык программирования |
| Git | >= 2.30 | Контроль версий |
| UV | >= 0.5 | Пакетный менеджер |

### Опциональные

| Компонент | Версия | Назначение |
|-----------|--------|------------|
| Docker | >= 20.10 | Контейнеризация |
| Docker Compose | >= 2.0 | Оркестрация контейнеров |

### Рекомендуемые ресурсы

- **RAM:** >= 8 GB
- **Свободное место:** >= 5 GB
- **Процессор:** 4+ ядра

---

## Шаг 1: Установка UV

UV — современный, быстрый пакетный менеджер для Python (10-100x быстрее pip).

=== "macOS / Linux"

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows (PowerShell)"

    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

### Проверка установки

```bash
uv --version
# Ожидается: uv 0.5.x или новее
```

!!! tip "Перезапуск терминала"
    После установки UV перезапустите терминал или выполните `source ~/.bashrc` / `source ~/.zshrc`.

---

## Шаг 2: Клонирование репозитория

```bash
# Клонирование репозитория
git clone https://github.com/Bovrrr/itmo-eplm-course.git
cd itmo-eplm-course

# Просмотр доступных веток
git branch -a
```

---

## Шаг 3: Установка зависимостей

### Основные зависимости

```bash
# Синхронизация всех зависимостей из uv.lock
uv sync
```

### Dev-зависимости (для разработки)

```bash
# Установка dev-зависимостей
uv sync --group dev
```

### Зависимости для документации

```bash
# Установка docs-зависимостей
uv sync --group docs
```

### Проверка установленных пакетов

```bash
uv pip list
```

---

## Шаг 4: Настройка pre-commit hooks

Pre-commit hooks автоматически проверяют качество кода перед каждым коммитом.

```bash
# Установка pre-commit hooks
uv run pre-commit install

# Первый запуск (проверка существующего кода)
uv run pre-commit run --all-files
```

!!! note "Автоисправление"
    Некоторые хуки (Ruff) автоматически исправляют проблемы. Просмотрите изменения перед коммитом.

---

## Шаг 5: Проверка установки

### Версии инструментов

```bash
# Python
python --version

# Ruff (линтер)
uv run ruff --version

# MyPy (проверка типов)
uv run mypy --version

# Pytest
uv run pytest --version
```

### Запуск проверок

```bash
# Линтинг
uv run ruff check .

# Проверка типов
uv run mypy src/

# Тесты
uv run pytest
```

### Основное приложение

```bash
uv run python src/main.py
# Ожидаемый вывод: Hello from itmo-eplm-course!
```

---

## Docker (опционально)

### Сборка образа

```bash
docker build -t itmo-eplm-course:latest .
```

### Запуск контейнера

```bash
# Простой запуск
docker run --rm itmo-eplm-course:latest

# Проверка библиотек
docker run --rm itmo-eplm-course:latest python -c "import numpy, pandas, sklearn; print('OK')"
```

### Docker Compose

```bash
# Запуск Jupyter Lab
docker-compose up jupyter
# Доступен на http://localhost:8888

# Для просмотра результатов используйте ClearML Web UI
# https://app.clear.ml → Projects → titanic_classification
```

---

## Следующие шаги

После установки переходите к:

- [Быстрый старт](quickstart.md) — первый запуск pipeline
- [Версионирование](../guides/versioning.md) — работа с DVC и ClearML
- [ClearML](../guides/clearml.md) — облачный трекинг экспериментов
