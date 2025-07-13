import yaml
from pathlib import Path


def load_config(config_path: Path | str) -> tuple[Path, dict]:
    config_path = Path(config_path) if isinstance(config_path, str) else config_path
    if not config_path.exists():
        raise FileNotFoundError(f'Configuration file "{config_path}" does not exist')
    config_path = config_path.absolute()

    try:
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
    except yaml.YAMLError as e:
        raise ValueError(f"Error loading configuration: {e}")
    if config is None:
        raise ValueError("Configuration could not be loaded")

    return config_path, config
