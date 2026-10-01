import logging
import logging.config

from app.config import LOG_LEVEL


def setup_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
                }
            },
            "handlers": {
                "console": {"class": "logging.StreamHandler", "formatter": "default"}
            },
            "root": {"level": LOG_LEVEL, "handlers": ["console"]},
        }
    )
    logging.getLogger(__name__).debug("Logging configured (level=%s)", LOG_LEVEL)
