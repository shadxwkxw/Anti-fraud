from src.antifraud.config import config


def test_config_loaded():
    assert config is not None
    assert "project" in config
    assert "model" in config
    assert "postgres" in config


def test_config_values():
    assert config["project"]["name"] == "antifraud-ml"
    assert config["postgres"]["port"].isdigit()
