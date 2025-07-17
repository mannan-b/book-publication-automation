
import os
import yaml
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'app': {
        'name': 'Smart Book Publisher',
        'version': '2.0',
        'debug': False
    },
    'scraper': {
        'default_url': 'https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1',
        'screenshot_dir': 'screenshots',
        'timeout': 30
    },
    'ai': {
        'provider': 'gemini',
        'temperature': 0.7,
        'max_tokens': 2048
    },
    'rewrite_strategies': [
        'dramatize',
        'summarize',
        'formalize',
        'expand',
        'simplify'
    ]
}

class ConfigManager:
    def __init__(self, path: str = 'config.yaml'):
        self.path = path
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info(f'Loaded config from {self.path}')
            except Exception as e:
                logger.error(f'Error loading config: {e}. Using default config.')
                config = DEFAULT_CONFIG
        else:
            logger.warning('config.yaml not found. Creating default config.')
            config = DEFAULT_CONFIG
            self.save_config(config)
        return config

    def save_config(self, config=None):
        if config is None:
            config = self.config
        try:
            with open(self.path, 'w') as f:
                yaml.safe_dump(config, f)
            logger.info(f'Config saved to {self.path}')
        except Exception as e:
            logger.error(f'Error saving config: {e}')

    def get(self, key_path, default=None):
        keys = key_path.split('.')
        node = self.config
        for k in keys:
            node = node.get(k, {})
        return node or default
