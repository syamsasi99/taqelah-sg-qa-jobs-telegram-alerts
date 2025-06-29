"""Logger utility for job_notifier."""

import logging
import sys
from typing import Optional


def get_logger(name: Optional[str] = "job_notifier") -> logging.Logger:
    """
    Create and return a logger instance.

    Args:
        name (Optional[str]): Name of the logger. Defaults to "job_notifier".

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent adding multiple handlers on repeated calls
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
