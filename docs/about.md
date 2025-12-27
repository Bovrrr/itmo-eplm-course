# О проекте

## ITMO EPLM Course

**Инженерные практики машинного обучения** — учебный проект курса ИТМО, демонстрирующий современные подходы к разработке ML-систем.

---

## Цели проекта

Проект создан для изучения и практического применения:

- **MLOps практик** — автоматизация ML pipeline
- **Версионирования** — данных, моделей, экспериментов
- **Качества кода** — линтинг, типизация, тестирование
- **Документирования** — код, API, процессы

---

## Выполненные домашние задания

| ДЗ | Тема | Баллы | Статус |
|----|------|-------|--------|
| 1 | Настройка рабочего места | 10 | ✅ |
| 2 | Версионирование данных и моделей | 10 | ✅ |
| 3 | Трекинг экспериментов | 10 | ✅ |
| 4 | Автоматизация ML пайплайнов | 10 | ✅ |
| 5 | ClearML интеграция | 10 | ✅ |
| 6 | Документация и отчёты | 8 | ✅ |

---

## Технологии

### Язык и окружение

- **Python 3.13+** — основной язык
- **UV** — пакетный менеджер (10-100x быстрее pip)

### ML и Data Science

- **scikit-learn** — базовые ML алгоритмы
- **CatBoost** — градиентный бустинг
- **pandas** — работа с данными
- **numpy** — численные вычисления

### MLOps

- **DVC** — версионирование данных и pipeline
- **ClearML** — облачный трекинг экспериментов, Model Registry, pipelines

### Качество кода

- **Ruff** — линтер и форматтер
- **MyPy** — статическая типизация (strict mode)
- **Bandit** — проверка безопасности
- **pre-commit** — автоматические проверки

### Документация

- **MkDocs** — генератор документации
- **Material for MkDocs** — современная тема
- **mkdocstrings** — автогенерация API docs

### Инфраструктура

- **Docker** — контейнеризация
- **Docker Compose** — оркестрация
- **GitHub Actions** — CI/CD

---

## Структура проекта

```
itmo-eplm-course/
├── configs/               # Pydantic конфигурации моделей
│   ├── base/              # Базовые конфигурации
│   ├── model/             # 18 конфигураций моделей
│   └── pipeline.yaml      # Конфигурация pipeline
├── data/                  # Данные
│   ├── raw/               # Исходные данные
│   ├── processed/         # Обработанные данные
│   └── features/          # Признаки для обучения
├── docs/                  # Документация (MkDocs)
├── models/                # Обученные модели
├── reports/               # Отчёты и визуализации
├── scripts/               # Вспомогательные скрипты
├── src/                   # Исходный код
│   ├── clearml_utils/     # ClearML интеграция
│   ├── config/            # Pydantic схемы
│   ├── data/              # Обработка данных
│   ├── experiments/       # Запуск экспериментов
│   ├── features/          # Feature engineering
│   ├── mlflow_utils/      # MLflow утилиты (legacy, не используется)
│   ├── models/            # ML модели
│   ├── pipelines/         # ClearML pipelines
│   └── utils/             # Вспомогательные утилиты
├── tests/                 # Тесты
├── dvc.yaml               # DVC pipeline
├── mkdocs.yml             # Конфигурация документации
└── pyproject.toml         # Конфигурация проекта
```

---

## Автор

**Baurzhan**

- Email: baurzhanonbaev@gmail.com
- GitHub: [Bovrrr](https://github.com/Bovrrr)

---

## Лицензия

MIT License

```
MIT License

Copyright (c) 2025 ITMO EPLM Course

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Благодарности

- Курс ИТМО "Инженерные практики машинного обучения"
- Сообщества open-source проектов: DVC, ClearML, MkDocs
