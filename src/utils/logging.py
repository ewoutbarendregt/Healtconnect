"""
Structured logging utilities for HealthConnect automation.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import Config


class HealthConnectLogger:
    """Custom logger for HealthConnect automation with structured output."""

    def __init__(self, name: str, document_id: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.document_id = document_id

        # Remove existing handlers
        self.logger.handlers = []

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler
        if document_id:
            log_file = Config.LOG_DIR / f"{document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        else:
            log_file = Config.LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def step_start(self, step: str, **kwargs):
        """Log the start of a workflow step."""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{step} | START"
        if extra_info:
            msg += f" | {extra_info}"
        if self.document_id:
            msg += f" | document_id={self.document_id}"
        self.logger.info(msg)

    def step_action(self, step: str, action: str, **kwargs):
        """Log an action within a workflow step."""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{step} | ACTION | {action}"
        if extra_info:
            msg += f" | {extra_info}"
        self.logger.info(msg)

    def step_verify(self, step: str, verification: str, result: bool, **kwargs):
        """Log a verification result."""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{step} | VERIFY | {verification} | {'PASS' if result else 'FAIL'}"
        if extra_info:
            msg += f" | {extra_info}"
        self.logger.info(msg)

    def step_complete(self, step: str, success: bool = True, **kwargs):
        """Log the completion of a workflow step."""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{step} | COMPLETE | success={success}"
        if extra_info:
            msg += f" | {extra_info}"
        self.logger.info(msg)

    def step_error(self, step: str, error: str, **kwargs):
        """Log an error in a workflow step."""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{step} | ERROR | {error}"
        if extra_info:
            msg += f" | {extra_info}"
        self.logger.error(msg)

    def info(self, msg: str):
        """Log an info message."""
        self.logger.info(msg)

    def warning(self, msg: str):
        """Log a warning message."""
        self.logger.warning(msg)

    def error(self, msg: str):
        """Log an error message."""
        self.logger.error(msg)

    def debug(self, msg: str):
        """Log a debug message."""
        self.logger.debug(msg)


def get_logger(name: str, document_id: Optional[str] = None) -> HealthConnectLogger:
    """Get a logger instance."""
    return HealthConnectLogger(name, document_id)
