"""Загрузка и валидация конфигураций через Hydra.

Этот модуль использует Hydra Compose API для загрузки конфигураций
из директории conf/.
"""

import sys
from pathlib import Path
from typing import cast

from omegaconf import OmegaConf
from pydantic import ValidationError
from rich.console import Console

from .hydra_loader import load_hydra_config, load_model_config_hydra, load_pipeline_config_hydra
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


def load_model_config(model_name: str) -> ModelConfig:
    """Загрузить и валидировать конфигурацию модели через Hydra.

    Args:
        model_name: Имя конфигурации модели (например, random_forest_medium)

    Returns:
        Pydantic модель конфигурации

    Raises:
        ValidationError: Если валидация Pydantic не прошла
        ValueError: Если неизвестный model_class
    """
    # Загрузить через Hydra
    config_data = load_model_config_hydra(model_name)
    console.print(f"[green]✓ Loaded {model_name} via Hydra[/green]")

    # Определить тип модели и валидировать
    try:
        model_class = ModelType(config_data.get("model_class"))
        config_class = MODEL_CONFIG_MAP[model_class]
        return cast("ModelConfig", config_class(**config_data))
    except ValidationError as e:
        console.print(f"[red]Validation error in {model_name}:[/red]")
        console.print(e)
        raise
    except KeyError as e:
        raise ValueError(f"Unknown model_class: {config_data.get('model_class')}") from e


def load_pipeline_config() -> PipelineConfig:
    """Загрузить конфигурацию pipeline через Hydra.

    Returns:
        Pydantic модель конфигурации pipeline

    Raises:
        ValidationError: Если валидация Pydantic не прошла
    """
    config_data = load_pipeline_config_hydra()
    try:
        return PipelineConfig(**config_data)
    except ValidationError as e:
        console.print("[red]Validation error in pipeline config:[/red]")
        console.print(e)
        raise


def validate_hydra_configs() -> dict[str, bool]:
    """Валидировать все Hydra конфигурации моделей из conf/model/.

    Returns:
        Словарь {config_name: is_valid}
    """
    conf_dir = Path("conf/model")
    if not conf_dir.exists():
        console.print(f"[yellow]Warning: {conf_dir} not found, skipping validation[/yellow]")
        return {}

    config_files = list(conf_dir.glob("*.yaml"))

    if not config_files:
        console.print(f"[yellow]Warning: No YAML files in {conf_dir}[/yellow]")
        return {}

    results = {}
    for config_file in config_files:
        config_name = config_file.stem
        try:
            cfg = load_hydra_config(overrides=[f"model={config_name}"])
            # Валидация через Pydantic
            model_class = ModelType(cfg.model.model_class)
            config_class = MODEL_CONFIG_MAP[model_class]
            model_dict = OmegaConf.to_container(cfg.model, resolve=True)
            config_class(**model_dict)
            results[config_name] = True
            console.print(f"[green]✓[/green] {config_name}")
        except Exception as e:
            results[config_name] = False
            console.print(f"[red]✗[/red] {config_name}: {e}")

    total = len(results)
    valid = sum(results.values())
    console.print(f"\n[bold]Summary:[/bold] {valid}/{total} configurations valid")

    return results


if __name__ == "__main__":
    """Запуск валидации конфигураций."""
    console.print("[bold cyan]Validating Hydra model configurations (conf/model/)...[/bold cyan]\n")

    results = validate_hydra_configs()

    # Exit code
    all_valid = all(results.values()) if results else False
    sys.exit(0 if all_valid else 1)
