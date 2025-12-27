# Руководство по развёртыванию

Подробное руководство по развёртыванию рабочего окружения для проекта ITMO EPLM Course.

## Требования

### Минимальные требования

- **Операционная система:** macOS, Linux или Windows (WSL2)
- **Python:** >= 3.13
- **Git:** >= 2.30
- **Docker:** >= 20.10 (опционально, для контейнеризации)
- **Docker Compose:** >= 2.0 (опционально)

### Рекомендуемые требования

- **RAM:** >= 8 GB
- **Свободное место на диске:** >= 5 GB
- **Процессор:** 4+ ядра

---

## Установка UV

UV - это современный, быстрый пакетный менеджер для Python (10-100x быстрее pip).

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

---

## Клонирование репозитория

```bash
# Клонирование репозитория
git clone https://github.com/Bovrrr/itmo-eplm-course.git
cd itmo-eplm-course

# Переключение на рабочую ветку (если требуется)
git checkout hw06
```

---

## Установка зависимостей

### Основные зависимости

```bash
# Синхронизация всех зависимостей из uv.lock
uv sync

# Или, если нужны только production зависимости (без dev)
uv sync --no-dev
```

### Dev-зависимости (для разработки)

```bash
# Установка dev-зависимостей
uv sync --group dev
```

### Проверка установленных пакетов

```bash
uv pip list
```

---

## Настройка pre-commit hooks

Pre-commit hooks автоматически проверяют качество кода перед каждым коммитом.

### Установка hooks

```bash
# Установка pre-commit hooks
uv run pre-commit install
```

### Первый запуск (для проверки существующего кода)

```bash
# Запуск на всех файлах
uv run pre-commit run --all-files
```

!!! note "Автоисправление"
    Некоторые хуки (например, Ruff) могут автоматически исправлять проблемы. Просмотрите изменения перед коммитом.

---

## Проверка установки

### Проверка Python версии

```bash
python --version
# Ожидается: Python 3.13.x или новее
```

### Проверка установленных инструментов

```bash
# Ruff (линтер и форматтер)
uv run ruff --version

# MyPy (проверка типов)
uv run mypy --version

# Bandit (проверка безопасности)
uv run bandit --version

# Pytest (тестирование)
uv run pytest --version
```

### Запуск тестов качества кода

```bash
# Линтинг
uv run ruff check .

# Форматирование (проверка)
uv run ruff format . --check

# Проверка типов
uv run mypy src/

# Проверка безопасности
uv run bandit -r src/

# Запуск тестов
uv run pytest
```

### Запуск основного приложения

```bash
# Простой запуск
python src/main.py

# Или через UV
uv run python src/main.py
```

**Ожидаемый вывод:**
```
Hello from itmo-eplm-course!
```

---

## Docker

### Сборка образа

```bash
# Сборка Docker образа
docker build -t itmo-eplm-course:latest .

# Проверка размера образа
docker images | grep itmo-eplm-course
```

### Запуск контейнера

```bash
# Простой запуск
docker run --rm itmo-eplm-course:latest

# Проверка установленных библиотек
docker run --rm itmo-eplm-course:latest python -c "import numpy, pandas, sklearn, catboost; print('OK')"
```

### Docker Compose

```bash
# Запуск основного приложения
docker-compose up app

# Запуск Jupyter Notebook сервера
docker-compose up jupyter

# Запуск в фоновом режиме
docker-compose up -d

# Проверка статуса
docker-compose ps

# Остановка
docker-compose down

# Остановка с удалением volumes
docker-compose down -v
```

### Доступ к Jupyter

После запуска `docker-compose up jupyter` откройте браузер:

```
http://localhost:8888
```

!!! warning "Безопасность"
    В конфигурации отключена аутентификация для разработки. Для production обязательно настройте пароль!

---

## Troubleshooting

### UV не найден после установки

**Проблема:** `command not found: uv`

**Решение:**
```bash
# Перезапустите терминал или выполните:
source ~/.bashrc  # для bash
source ~/.zshrc   # для zsh

# Или добавьте путь вручную:
export PATH="$HOME/.local/bin:$PATH"
```

### Ошибка "Unable to determine which files to ship"

**Проблема:** Hatchling не может найти пакеты для сборки.

**Решение:** Убедитесь, что в `pyproject.toml` есть:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src"]
```

### Pre-commit hooks не проходят

**Проблема:** MyPy или Ruff находят ошибки в коде.

**Решение:**
1. Просмотрите ошибки
2. Исправьте вручную или запустите автоисправление:
```bash
# Автоисправление Ruff
uv run ruff check . --fix
uv run ruff format .
```

### Docker build очень медленный

**Проблема:** Сборка Docker образа занимает много времени.

**Решение:**
1. Убедитесь, что `.dockerignore` настроен правильно
2. Используйте BuildKit:
```bash
DOCKER_BUILDKIT=1 docker build -t itmo-eplm-course:latest .
```

### Jupyter не запускается в Docker

**Проблема:** Jupyter Notebook не доступен на `localhost:8888`.

**Решение:**
1. Проверьте логи:
```bash
docker-compose logs jupyter
```
2. Убедитесь, что порт не занят:
```bash
lsof -i :8888
```

---

## Полезные команды

```bash
# Обновление всех зависимостей
uv lock --upgrade

# Добавление новой зависимости
uv add package-name

# Удаление зависимости
uv remove package-name

# Экспорт requirements.txt (для совместимости)
uv pip compile pyproject.toml -o requirements.txt

# Очистка кэша
uv cache clean

# Проверка актуальности зависимостей
uv lock --check
```

---

## Дополнительные ресурсы

- [UV Documentation](https://github.com/astral-sh/uv)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Docker Documentation](https://docs.docker.com/)
