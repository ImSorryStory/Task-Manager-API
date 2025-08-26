from __future__ import annotations

import logging
from logging.config import dictConfig


def setup_logging(debug: bool = False) -> None:
    level = "DEBUG" if debug else "INFO"
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                }
            },
            "handlers": {
                "console": {"class": "logging.StreamHandler", "formatter": "default"}
            },
            "root": {"level": level, "handlers": ["console"]},
        }
    )
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
