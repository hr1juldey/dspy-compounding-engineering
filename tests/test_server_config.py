"""
Unit tests for server configuration.
"""

from server.config.logging import configure_logging
from server.config.settings import ServerSettings, get_settings


def test_server_settings_from_env(monkeypatch):
    """Test settings loaded from environment variables."""
    # Set specific env vars
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "8000")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379")

    settings = ServerSettings()
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.redis_url == "redis://redis:6379"


def test_server_settings_required_fields():
    """Test that settings can be instantiated."""
    settings = ServerSettings()
    assert settings.host is not None
    assert settings.port is not None
    assert settings.redis_url is not None
    assert settings.qdrant_url is not None


def test_get_settings_singleton():
    """Test settings singleton pattern."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_configure_logging_default():
    """Test logging configuration."""
    configure_logging(level="INFO", json_logs=False)
    # Should not raise


def test_configure_logging_json():
    """Test JSON logging configuration."""
    configure_logging(level="DEBUG", json_logs=True)
    # Should not raise
