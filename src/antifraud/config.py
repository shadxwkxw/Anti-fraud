import os
import re

import yaml
from dotenv import load_dotenv

load_dotenv()

ENV_VAR_PATTERN = re.compile(r"^\$\{([^}]+)\}$")


def resolve_env_placeholders(value):
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
            expr = match.group(1)
            if ":-" in expr:
                env_name, default = expr.split(":-", 1)
            else:
                env_name, default = expr, None
            raw_value = os.getenv(env_name)
            if raw_value is None:
                if default is not None:
                    raw_value = default
                else:
                    raise KeyError(
                        f"Required environment variable '{env_name}' is not set. "
                        f"Define it in .env or export it before running."
                    )
            resolved = raw_value

    return resolved


def load_config():
    """Загружает конфигурацию из YAML файла."""
    config_path = os.getenv("CONFIG_PATH", "configs/config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return resolve_env_placeholders(yaml.safe_load(f))


config = load_config()
