# utils/logger.py

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


_LOGGERS: dict[str, logging.Logger] = {}


def get_logger(
    name: str = "Doktorat_Kod",
    level: int = logging.INFO,
    log_file: Optional[str | Path] = None,
) -> logging.Logger:
    """
    Create or return a configured project logger.

    Parameters
    ----------
    name:
        Logger name.
    level:
        Logging level.
    log_file:
        Optional file where logs should also be written.

    Returns
    -------
    logging.Logger
    """

    if name in _LOGGERS:
        return _LOGGERS[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file is not None:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(
                log_path,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    _LOGGERS[name] = logger

    return logger


def configure_logger(
    name: str = "Doktorat_Kod",
    level: int = logging.INFO,
    log_file: Optional[str | Path] = None,
) -> logging.Logger:
    """
    Explicitly configure a project logger.

    Existing handlers are removed before configuration.
    """

    logger = logging.getLogger(name)

    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            log_path,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _LOGGERS[name] = logger

    return logger


def set_log_level(
    logger: logging.Logger,
    level: int,
) -> None:
    """
    Change logger and handler levels.
    """

    logger.setLevel(level)

    for handler in logger.handlers:
        handler.setLevel(level)


def log_section(
    logger: logging.Logger,
    title: str,
) -> None:
    """
    Print a visually separated section in the log.
    """

    separator = "=" * 70

    logger.info(separator)
    logger.info(title)
    logger.info(separator)


def log_model_info(
    logger: logging.Logger,
    model_name: str,
    parameters: int,
    trainable_parameters: Optional[int] = None,
) -> None:
    """
    Log basic model information.
    """

    logger.info("Model: %s", model_name)
    logger.info("Parameters: %d", parameters)

    if trainable_parameters is not None:
        logger.info(
            "Trainable parameters: %d",
            trainable_parameters,
        )