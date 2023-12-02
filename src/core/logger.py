import logging.config

import yaml
from colorlog import ColoredFormatter

from gunicorn import glogging
from src.core.config import BASE_DIR, CONTEXT_ID, LOG_DIR, settings


class CustomFormatter(logging.Formatter):
    def format(self, record):
        # We set request id, so we can use it in the formatter to show it in the log records.
        # Also, this fields will be added to the graylog extra fields and will be searchable.
        context_id = CONTEXT_ID.get()

        if context_id:
            record.context_id = context_id
            record.short_context_id = context_id[:3] + "..." + context_id[-3:]
        else:
            record.context_id = ""
            record.short_context_id = ""

        return super().format(record)


class CustomColoredFormatter(ColoredFormatter, CustomFormatter):
    pass


def setup_logging():
    if settings.SETTINGS_MODULE == "DEV":
        file_name = BASE_DIR / "logging.yml"
    elif settings.SETTINGS_MODULE == "PROD":
        file_name = BASE_DIR / "logging.prod.yml"
    else:
        raise ValueError(f"Unknown settings module: {settings.SETTINGS_MODULE}")

    with open(file_name) as log_file:
        content = log_file.read()

    log_config = content.format(logdir=LOG_DIR)
    logging.config.dictConfig(yaml.safe_load(log_config))


class GunicornLogger(glogging.Logger):
    def setup(self, cfg):
        setup_logging()
