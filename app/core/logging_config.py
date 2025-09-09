import logging
import sys
from logging import Logger
from logging.config import dictConfig

import pythonjsonlogger  # import not required here, but is included to ensure it's included in requirements.txt to

# allow logging setup below to work


# logging config to json format the logs and push to stdout and stderr to allow them to be captured by docker containers
# from the container they will be pushed to cloudwatch
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {

        "standard": {  # A single standard text formatter for all general logs - remove for production
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },

        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelname)s: %(message)s",
            "use_colors": True,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelname)s: %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(process)d %(thread)d %(pathname)s %(lineno)d %(funcName)s %(message)s"
        }

    },

    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "console_json": {
            "formatter": "json",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "console_standard": {  # Standard text logger - remove for production
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,  # Direct to standard output
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "DEBUG", "propagate": False},
        "uvicorn.error": {"level": "DEBUG", "handlers": ["default"], "propagate": False},
        "uvicorn.access": {"handlers": ["access"], "level": "DEBUG", "propagate": False},
        # todo  uncomment next line for deployment in container
        # "app": {"handlers": ["console_json"], "level": "INFO", "propagate": False},
        "app": {
            "handlers": ["console_standard"],
            "level": "DEBUG",
            "propagate": False,
        }

    },
    "root": {
        "handlers": ["console_standard"]  # replace with console_json in production
    }
}

dictConfig(LOGGING_CONFIG)
logger: Logger = logging.getLogger("app")
