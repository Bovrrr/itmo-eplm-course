"""Конфигурации моделей для экспериментов.

Этот модуль загружает предопределённые конфигурации для различных ML алгоритмов из YAML файла.
Каждая конфигурация включает название класса модели и её гиперпараметры.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Путь к YAML файлу с конфигурациями
_CONFIG_FILE = Path(__file__).parent / "configs.yaml"


@lru_cache(maxsize=1)
def get_all_configs() -> dict[str, dict[str, Any]]:
    """Получить все конфигурации моделей.

    Конфигурации загружаются один раз и кэшируются.

    Returns:
        Словарь со всеми конфигурациями.

    Raises:
        FileNotFoundError: Если файл конфигурации не найден.
        ValueError: Если файл имеет неверный формат.

    Example:
        >>> configs = get_all_configs()
        >>> print(f"Total configs: {len(configs)}")
    """
    if not _CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file not found: {_CONFIG_FILE}")

    with _CONFIG_FILE.open("r", encoding="utf-8") as f:
        configs = yaml.safe_load(f)

    if not isinstance(configs, dict):
        raise ValueError(f"Invalid config format in {_CONFIG_FILE}: expected dict")

    return configs


def get_model_config(config_name: str) -> dict[str, Any]:
    """Получить конфигурацию модели по имени.

    Args:
        config_name: Имя конфигурации из configs.yaml.

    Returns:
        Словарь с конфигурацией модели.

    Raises:
        KeyError: Если конфигурация не найдена.

    Example:
        >>> config = get_model_config("random_forest_medium")
        >>> print(config["model_class"])
        RandomForestClassifier
    """
    configs = get_all_configs()

    if config_name not in configs:
        available = ", ".join(configs.keys())
        raise KeyError(f"Model config '{config_name}' not found. Available: {available}")

    return configs[config_name]


def list_model_configs() -> list[str]:
    """Получить список всех доступных конфигураций.

    Returns:
        Список имён конфигураций.

    Example:
        >>> configs = list_model_configs()
        >>> print(f"Total configs: {len(configs)}")
    """
    return list(get_all_configs().keys())


def get_configs_by_model_class(model_class: str) -> dict[str, dict[str, Any]]:
    """Получить все конфигурации для определённого класса модели.

    Args:
        model_class: Название класса модели (например, "RandomForestClassifier").

    Returns:
        Словарь с конфигурациями для данного класса.

    Example:
        >>> rf_configs = get_configs_by_model_class("RandomForestClassifier")
        >>> print(f"Found {len(rf_configs)} RandomForest configs")
    """
    configs = get_all_configs()
    return {
        name: config for name, config in configs.items() if config["model_class"] == model_class
    }


# Для обратной совместимости: экспортируем MODEL_CONFIGS как ленивое свойство
def __getattr__(name: str) -> Any:
    """Обеспечить обратную совместимость для MODEL_CONFIGS."""
    if name == "MODEL_CONFIGS":
        return get_all_configs()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
