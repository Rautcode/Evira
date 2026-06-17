import os
import json
import logging

from app.utils.crypto import encrypt, decrypt

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/system_config.json'))


def _is_secret(key: str) -> bool:
    """Keys whose values are passwords/secrets (encrypted at rest)."""
    k = key.lower()
    return "pass" in k or "secret" in k


def _transform(obj, fn):
    """Recursively apply fn to secret string values (handles nested dicts/lists)."""
    if isinstance(obj, dict):
        return {k: (fn(v) if _is_secret(k) and isinstance(v, str) else _transform(v, fn)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_transform(i, fn) for i in obj]
    return obj


class ConfigManager:
    """Manages reading and writing dynamic system configuration.

    Secret values (passwords) are encrypted at rest via app.utils.crypto.
    """

    @staticmethod
    def load_config() -> dict:
        """Load the system configuration from JSON (secrets decrypted)."""
        if not os.path.exists(CONFIG_PATH):
            return {}
        try:
            with open(CONFIG_PATH, 'r') as f:
                return _transform(json.load(f), decrypt)
        except Exception as e:
            logger.error(f"Failed to load system config: {e}")
            return {}

    @staticmethod
    def save_config(config: dict):
        """Save the system configuration to JSON (secrets encrypted)."""
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(_transform(config, encrypt), f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save system config: {e}")
            raise e

    @staticmethod
    def update_config(partial: dict) -> dict:
        """Merge partial keys into the existing config (does not overwrite the rest)."""
        config = ConfigManager.load_config()
        config.update(partial)
        ConfigManager.save_config(config)
        return config

config_manager = ConfigManager()
