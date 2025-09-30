import os
import logging


GECKO_DRIVER_PATH = 'webdrivers/gecko/geckodriver'

LOGS_PATH = os.getenv('LOGS_PATH', 'logs')
if os.path.exists(LOGS_PATH) and os.path.isdir(LOGS_PATH):
    pass
else:
    os.makedirs(LOGS_PATH)

LOG_CONFIG = \
{
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(thread)d - %(name)s - [%(levelname)s] %(message)s"
        },
        'json': {
            'format': "%(asctime)s - %(thread)d - %(name)s - %(levelname)s - %(message)s",
            'class': 'aip.jsonlogger.JsonFormatter',
        }
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },

        "info_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": f"{LOGS_PATH}/info.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },

        "error_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "simple",
            "filename": f"{LOGS_PATH}/errors.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },

        "access_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": f"{LOGS_PATH}/access.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },
        "consumer_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": f"{LOGS_PATH}/consumer.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },
        "application_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": f"{LOGS_PATH}/application.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },
        'json': {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": f"{LOGS_PATH}/struct.json",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        }
    },

    "loggers": {
        "access": {
            "level": "INFO",
            "handlers": ["access_file_handler"],
            "propagate": False
        },
        "werkzeug": {
            "level": "INFO",
            "handlers": ["access_file_handler"],
            "propagate": False
        },
        "consumer": {
            "level": "INFO",
            "handlers": ["consumer_file_handler"],
            "propagate": False
        },
        "app": {
            "level": "INFO",
            "handlers": ["application_file_handler"],
            "propagate": False
        },
        'struct': {
            'handlers': ['json'],
            'level': logging.INFO,
            "propagate": False
        },
        "apscheduler": {
        "level": "INFO",
        "handlers": ["console"],
        "propagate": False
        }
    },

    "root": {
        "level": "INFO",
        "handlers": ["console", "info_file_handler", "error_file_handler"]
    }
}
