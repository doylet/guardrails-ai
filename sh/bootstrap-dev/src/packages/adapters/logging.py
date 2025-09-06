"""Structured logging for the AI Guardrails Bootstrap System.

This module provides consistent logging across all components with support
for both human-readable output and structured JSON logs for CI integration.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from ..domain.constants import CLI_WIDTH


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging in CI environments."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": time.time(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ("name", "msg", "args", "pathname", "filename",
                          "module", "lineno", "funcName", "created", "msecs",
                          "relativeCreated", "thread", "threadName", "processName",
                          "process", "getMessage", "levelname", "levelno"):
                log_data[key] = value

        return json.dumps(log_data, default=str)


class HumanFormatter(logging.Formatter):
    """Human-readable formatter for console output."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
        "RESET": "\033[0m",     # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        # Add color if outputting to terminal
        if hasattr(sys.stderr, "isatty") and sys.stderr.isatty():
            color = self.COLORS.get(record.levelname, "")
            reset = self.COLORS["RESET"]
            level = f"{color}{record.levelname}{reset}"
        else:
            level = record.levelname

        # Format: [LEVEL] module.function: message
        return f"[{level}] {record.module}.{record.funcName}: {record.getMessage()}"


def configure_logging(
    level: str = "INFO",
    structured: bool = False,
    log_file: Optional[Path] = None,
    quiet: bool = False,
) -> None:
    """Configure logging for the bootstrap system.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Use JSON structured logging
        log_file: Optional file to write logs to
        quiet: Suppress console output except errors
    """
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set log level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Console handler (unless quiet mode)
    if not quiet:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(numeric_level)

        if structured:
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(HumanFormatter())

        root_logger.addHandler(console_handler)
    elif level.upper() in ("ERROR", "CRITICAL"):
        # Always show errors even in quiet mode
        error_handler = logging.StreamHandler(sys.stderr)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(HumanFormatter())
        root_logger.addHandler(error_handler)

    # File handler (if specified)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always debug level for files
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class ProgressLogger:
    """Progress tracking for long-running operations."""

    def __init__(self, logger: logging.Logger, total_items: int, description: str = "Processing"):
        self.logger = logger
        self.total_items = total_items
        self.description = description
        self.completed_items = 0
        self.start_time = time.time()

    def update(self, increment: int = 1, item_name: Optional[str] = None) -> None:
        """Update progress counter.

        Args:
            increment: Number of items completed
            item_name: Optional name of current item
        """
        self.completed_items += increment

        if self.total_items > 0:
            percentage = (self.completed_items / self.total_items) * 100
            elapsed = time.time() - self.start_time

            if item_name:
                self.logger.info(
                    f"{self.description}: {self.completed_items}/{self.total_items} "
                    f"({percentage:.1f}%) - {item_name}",
                    extra={
                        "progress_completed": self.completed_items,
                        "progress_total": self.total_items,
                        "progress_percentage": percentage,
                        "elapsed_seconds": elapsed,
                        "current_item": item_name,
                    }
                )
            else:
                self.logger.info(
                    f"{self.description}: {self.completed_items}/{self.total_items} ({percentage:.1f}%)",
                    extra={
                        "progress_completed": self.completed_items,
                        "progress_total": self.total_items,
                        "progress_percentage": percentage,
                        "elapsed_seconds": elapsed,
                    }
                )

    def finish(self) -> None:
        """Mark progress as complete."""
        elapsed = time.time() - self.start_time
        self.logger.info(
            f"{self.description} completed: {self.completed_items} items in {elapsed:.2f}s",
            extra={
                "progress_completed": self.completed_items,
                "progress_total": self.total_items,
                "elapsed_seconds": elapsed,
                "progress_finished": True,
            }
        )


class TimingLogger:
    """Context manager for timing operations."""

    def __init__(self, logger: logging.Logger, operation: str, **extra_fields):
        self.logger = logger
        self.operation = operation
        self.extra_fields = extra_fields
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Starting {self.operation}", extra=self.extra_fields)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time

        if exc_type is None:
            self.logger.debug(
                f"Completed {self.operation} in {elapsed:.3f}s",
                extra={**self.extra_fields, "elapsed_seconds": elapsed}
            )
        else:
            self.logger.error(
                f"Failed {self.operation} after {elapsed:.3f}s: {exc_val}",
                extra={**self.extra_fields, "elapsed_seconds": elapsed, "error": str(exc_val)}
            )
