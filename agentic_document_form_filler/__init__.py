import logging

from .libs.config import default_config as config

__version__ = '1.0.0'

logging.basicConfig(level=config.log_level)
logger = logging.getLogger(config.name)
