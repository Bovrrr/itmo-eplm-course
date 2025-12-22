"""Загрузка и валидация конфигураций из YAML файлов."""

import sys
from pathlib import Path
from typing import Any, cast

import yaml
from pydantic import ValidationError
from rich.console import Console

from .schemas import (
    CatBoostConfig,
    GradientBoostingConfig,
    KNNConfig,
    LogisticRegressionConfig,
    ModelConfig,
    ModelType,
    PipelineConfig,
    RandomForestConfig,
    SVCConfig,
)

console = Console()

# Маппинг типов моделей на Pydantic классы
MODEL_CONFIG_MAP = {
    ModelType.LOGISTIC_REGRESSION: LogisticRegressionConfig,
    ModelType.SVC: SVCConfig,
    ModelType.RANDOM_FOREST: RandomForestConfig,
    ModelType.GRADIENT_BOOSTING: GradientBoostingConfig,
    ModelType.CATBOOST: CatBoostConfig,
    ModelType.KNN: KNNConfig,
}


def load_yaml(path: Path) -> dict[str, Any]:
    """Загрузить YAML файл.

    Args:
        path: Путь к YAML файлу

    Returns:
        Словарь с данными из YAML

    Raises:
        FileNotFoundError: Если файл не найден
        yaml.YAMLError: Если ошибка парсинга YAML
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r") as f:
        return cast("dict[str, Any]", yaml.safe_load(f))


def merge_configs(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Композиция конфигураций (наследование от базовой).

    Args:
        base: Базовая конфигурация
        override: Переопределяющая конфигурация

    Returns:
        Объединённая конфигурация
    """
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Рекурсивное слияние для вложенных dict
            merged[key] = merge_configs(merged[key], value)
        else:
            # Простая перезапись
            merged[key] = value
    return merged


def load_model_config(config_path: Path, validate: bool = True) -> ModelConfig | dict[str, Any]:
    """Загрузить и валидировать конфигурацию модели.

    Поддерживает композицию через поле 'base'.

    Example YAML:
        base: ../../base/tree_models.yaml
        model_class: RandomForestClassifier
        description: "Custom RF config"
        n_estimators: 100
        max_depth: 10

    Args:
        config_path: Путь к файлу конфигурации
        validate: Валидировать через Pydantic

    Returns:
        Pydantic модель конфигурации или словарь (если validate=False)

    Raises:
        FileNotFoundError: Если файл не найден
        ValidationError: Если валидация Pydantic не прошла
        ValueError: Если неизвестный model_class
    """
    config_data = load_yaml(config_path)

    # Если есть base - загрузить и смержить
    if "base" in config_data:
        base_path_str = config_data["base"]
        base_path = Path(base_path_str)

        # Если относительный путь - относительно текущего конфига
        if not base_path.is_absolute():
            base_path = config_path.parent / base_path

        base_data = load_yaml(base_path)
        config_data = merge_configs(base_data, config_data)
        config_data.pop("base")  # Удалить поле base

    # Если есть старая структура (params внутри) - преобразовать
    if "params" in config_data:
        params = config_data.pop("params")
        config_data.update(params)

    if not validate:
        return config_data

    # Определить тип модели и валидировать
    try:
        model_class = ModelType(config_data.get("model_class"))
        config_class = MODEL_CONFIG_MAP[model_class]
        return cast("ModelConfig", config_class(**config_data))
    except ValidationError as e:
        console.print(f"[red]Validation error in {config_path}:[/red]")
        console.print(e)
        raise
    except KeyError as e:
        raise ValueError(f"Unknown model_class: {config_data.get('model_class')}") from e


def load_pipeline_config(config_path: Path = Path("configs/pipeline.yaml")) -> PipelineConfig:
    """Загрузить конфигурацию pipeline.

    Args:
        config_path: Путь к файлу конфигурации pipeline

    Returns:
        Pydantic модель конфигурации pipeline

    Raises:
        FileNotFoundError: Если файл не найден
        ValidationError: Если валидация Pydantic не прошла
    """
    config_data = load_yaml(config_path)
    try:
        return PipelineConfig(**config_data)
    except ValidationError as e:
        console.print("[red]Validation error in pipeline config:[/red]")
        console.print(e)
        raise


def validate_all_model_configs(configs_dir: Path = Path("src/models")) -> dict[str, bool]:
    """Валидировать все конфигурации моделей из configs.yaml.

    Загружает старый configs.yaml и валидирует каждую конфигурацию через Pydantic.

    Args:
        configs_dir: Директория с configs.yaml

    Returns:
        Словарь {config_name: is_valid}
    """
    configs_yaml = configs_dir / "configs.yaml"
    if not configs_yaml.exists():
        console.print(f"[yellow]Warning: {configs_yaml} not found, skipping validation[/yellow]")
        return {}

    all_configs = load_yaml(configs_yaml)

    results = {}
    for config_name, config_data in all_configs.items():
        try:
            # Преобразовать старый формат
            processed_config = config_data.copy()
            if "params" in processed_config:
                params = processed_config.pop("params")
                processed_config.update(params)

            model_class = ModelType(processed_config["model_class"])
            config_class = MODEL_CONFIG_MAP[model_class]
            config_class(**processed_config)
            results[config_name] = True
            console.print(f"[green]✓[/green] {config_name}")
        except Exception as e:
            results[config_name] = False
            console.print(f"[red]✗[/red] {config_name}: {e}")

    # Summary
    total = len(results)
    valid = sum(results.values())
    console.print(f"\n[bold]Summary:[/bold] {valid}/{total} configurations valid")

    return results


def validate_new_model_configs(configs_dir: Path = Path("configs/model")) -> dict[str, bool]:
    """Валидировать все конфигурации моделей из configs/model/.

    Args:
        configs_dir: Директория с конфигурациями моделей

    Returns:
        Словарь {config_name: is_valid}
    """
    if not configs_dir.exists():
        console.print(f"[yellow]Warning: {configs_dir} not found, skipping validation[/yellow]")
        return {}

    # Найти все YAML файлы
    config_files = list(configs_dir.glob("*.yaml"))

    if not config_files:
        console.print(f"[yellow]Warning: No YAML files in {configs_dir}[/yellow]")
        return {}

    results = {}
    for config_file in config_files:
        config_name = config_file.stem
        try:
            load_model_config(config_file, validate=True)
            results[config_name] = True
            console.print(f"[green]✓[/green] {config_name}")
        except Exception as e:
            results[config_name] = False
            console.print(f"[red]✗[/red] {config_name}: {e}")

    # Summary
    total = len(results)
    valid = sum(results.values())
    console.print(f"\n[bold]Summary:[/bold] {valid}/{total} configurations valid")

    return results


if __name__ == "__main__":
    """Запуск валидации конфигураций."""
    console.print("[bold cyan]Validating model configurations...[/bold cyan]\n")

    # Валидировать старые конфигурации (src/models/configs.yaml)
    console.print("[bold]Old configurations (src/models/configs.yaml):[/bold]")
    old_results = validate_all_model_configs()

    # Валидировать новые конфигурации (configs/model/)
    console.print("\n[bold]New configurations (configs/model/):[/bold]")
    new_results = validate_new_model_configs()

    # Exit code
    all_valid = all(old_results.values()) and all(new_results.values())
    sys.exit(0 if all_valid else 1)
