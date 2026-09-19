"""
CivicMind AI — Structured Logging Setup
"""
import logging
import sys
from typing import Optional


class ColorFormatter(logging.Formatter):
    """ANSI-colored log formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname:<8}{self.RESET}"
        return super().format(record)


def setup_logging(level: Optional[str] = None) -> None:
    """Configure root logger for CivicMind AI."""
    log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)

    formatter = ColorFormatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ["httpx", "httpcore", "urllib3", "filelock"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)
