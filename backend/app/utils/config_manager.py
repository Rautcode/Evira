import os
import json
import logging

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/system_config.json'))

class ConfigManager:
    """Manages reading and writing dynamic system configuration."""

    @staticmethod
    def load_config() -> dict:
        """Load the system configuration from JSON."""
        if not os.path.exists(CONFIG_PATH):
            return {}
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load system config: {e}")
            return {}

    @staticmethod
    def save_config(config: dict):
        """Save the system configuration to JSON. Writes the provided config directly."""
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save system config: {e}")
            raise e

config_manager = ConfigManager()
