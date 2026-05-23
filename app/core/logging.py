import logging.config
import os
from .config import get_settings
import sys

settings = get_settings()

def setup_logging():
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,  # Change to False
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,  # Explicitly set stdout
                'formatter': 'standard',
                'level': log_level
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'app.log',
                'maxBytes': 1024 * 1024 * 5,
                'backupCount': 5,
                'formatter': 'standard',
                'level': log_level
            }
        },
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            }
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': True
            },
            'app.middleware': {  # Add specific logger for middleware
                'handlers': ['console', 'file'],
                'level': logging.DEBUG,
                'propagate': False
            }
        }
    }
    
    logging.config.dictConfig(config)