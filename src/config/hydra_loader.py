"""Hydra-based configuration loader.

Provides functions for loading configurations using Hydra Compose API.
This module replaces the custom YAML loading logic with Hydra's built-in
configuration management capabilities.
"""

from pathlib import Path
from typing import Any

from hydra import compose, initialize_config_dir
from hydra.core.global_hydra import GlobalHydra
from omegaconf import DictConfig, OmegaConf


def _get_config_dir() -> Path:
    """Get the absolute path to the config directory."""
    # Try to find conf/ relative to the current working directory
    cwd = Path.cwd()
    conf_dir = cwd / "conf"
    if conf_dir.exists():
        return conf_dir.absolute()

    # Fallback: find conf/ relative to this file
    module_dir = Path(__file__).parent.parent.parent
    conf_dir = module_dir / "conf"
    if conf_dir.exists():
        return conf_dir.absolute()

    raise FileNotFoundError(
        f"Config directory not found. Searched: {cwd / 'conf'}, {module_dir / 'conf'}"
    )


def load_hydra_config(
    config_name: str = "config",
    overrides: list[str] | None = None,
) -> DictConfig:
    """Load configuration using Hydra Compose API.

    Args:
        config_name: Name of the config file (without .yaml extension)
        overrides: List of Hydra override strings (e.g., ["model=random_forest_large"])

    Returns:
        DictConfig with loaded and merged configuration

    Example:
        >>> cfg = load_hydra_config()
        >>> print(cfg.random_state)
        42
        >>> cfg = load_hydra_config(overrides=["model=catboost_deep"])
        >>> print(cfg.model.model_class)
        CatBoostClassifier
    """
    config_dir = _get_config_dir()

    # Clear any existing Hydra state to allow reinitialization
    GlobalHydra.instance().clear()

    with initialize_config_dir(config_dir=str(config_dir), version_base="1.3"):
        cfg = compose(config_name=config_name, overrides=overrides or [])
        return cfg


def load_pipeline_config_hydra() -> dict[str, Any]:
    """Load pipeline configuration via Hydra.

    Returns:
        Dictionary with pipeline configuration including:
        - data_split: train/val/test split parameters
        - data_validation: data quality checks
        - model_validation: model quality thresholds
    """
    cfg = load_hydra_config()
    result: dict[str, Any] = OmegaConf.to_container(cfg.pipeline, resolve=True)
    return result


def load_model_config_hydra(model_name: str) -> dict[str, Any]:
    """Load model configuration via Hydra.

    Args:
        model_name: Name of the model config (e.g., "random_forest_medium")

    Returns:
        Dictionary with model configuration including model_class and parameters
    """
    cfg = load_hydra_config(overrides=[f"model={model_name}"])
    result: dict[str, Any] = OmegaConf.to_container(cfg.model, resolve=True)
    return result


def get_full_config(overrides: list[str] | None = None) -> dict[str, Any]:
    """Get the full resolved configuration.

    Args:
        overrides: Optional list of Hydra overrides

    Returns:
        Complete configuration as a dictionary
    """
    cfg = load_hydra_config(overrides=overrides)
    result: dict[str, Any] = OmegaConf.to_container(cfg, resolve=True)
    return result
