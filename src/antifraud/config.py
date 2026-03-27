import os
import re

import yaml

ENV_VAR_PATTERN = re.compile(r"^\$\{([^}]+)\}$")
ENV_DEFAULTS = {
    "POSTGRES_HOST": "postgres",
    "POSTGRES_PORT": 5432,
    "POSTGRES_DB": "fraud",
    "POSTGRES_USER": "fraud",
    "POSTGRES_PASSWORD": "fraud",
}


def resolve_env_placeholders(value):
    """Recursively resolves ${ENV_VAR} placeholders with environment defaults."""
    if isinstance(value, dict):
        resolved = {key: resolve_env_placeholders(item) for key, item in value.items()}
    elif isinstance(value, list):
        resolved = [resolve_env_placeholders(item) for item in value]
    elif not isinstance(value, str):
        resolved = value
    else:
        match = ENV_VAR_PATTERN.match(value)
        if not match:
            resolved = value
        else:
            env_name = match.group(1)
            default = ENV_DEFAULTS.get(env_name, value)
            raw_value = os.getenv(env_name)
            if raw_value is None:
                resolved = default
            elif isinstance(default, int):
                resolved = int(raw_value)
            else:
                resolved = raw_value

    return resolved


def load_config():
    """Загружает конфигурацию из YAML файла."""
    config_path = os.getenv("CONFIG_PATH", "configs/config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return resolve_env_placeholders(yaml.safe_load(f))


config = load_config()
