# =============================================================================
# Multi-Stage Dockerfile для ITMO EPLM Course
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - установка UV и зависимостей
# -----------------------------------------------------------------------------
FROM python:3.13-slim AS builder

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Установка UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Создание рабочей директории
WORKDIR /app

# Копирование файлов проекта для установки зависимостей
COPY pyproject.toml uv.lock ./
COPY README.md ./

# Установка зависимостей через UV
# --no-dev для исключения dev-зависимостей в production
RUN uv sync --frozen --no-dev

# Копирование остальных файлов проекта
COPY . .

# -----------------------------------------------------------------------------
# Stage 2: Final - минимальный production образ
# -----------------------------------------------------------------------------
FROM python:3.13-slim

# Метаданные образа
LABEL maintainer="baurzhanonbaev@gmail.com"
LABEL description="ITMO Engineering Practices in ML - Data Science Workspace"
LABEL version="0.1.0"

# Установка минимальных системных зависимостей
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Создание непривилегированного пользователя
RUN useradd -m -u 1000 -s /bin/bash mluser

# Установка рабочей директории
WORKDIR /app

# Копирование виртуального окружения из builder stage
COPY --from=builder --chown=mluser:mluser /app/.venv /app/.venv
COPY --from=builder --chown=mluser:mluser /app /app

# Добавление .venv/bin в PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Создание директорий для данных и моделей
RUN mkdir -p /app/data/raw /app/data/processed /app/models \
    && chown -R mluser:mluser /app

# Переключение на непривилегированного пользователя
USER mluser

# Открытие порта для Jupyter
EXPOSE 8888

# Команда по умолчанию
CMD ["python", "main.py"]
