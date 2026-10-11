"""
utils/logging.py

A small, dependency-free logging helper used across the project so
console output (Streamlit terminal, or a background sweep script) is
consistently timestamped and leveled, without pulling in a heavier
logging framework for what is fundamentally a research prototype.
"""

from __future__ import annotations

import sys
import time


LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}


class ExperimentLogger:
    def __init__(self, name: str = "synth_data_project", level: str = "INFO"):
        self.name = name
        self.level = LEVELS.get(level.upper(), 20)

    def _log(self, level: str, message: str):
        if LEVELS[level] < self.level:
            return
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level:7s}] [{self.name}] {message}", file=sys.stderr, flush=True)

    def debug(self, message: str):
        self._log("DEBUG", message)

    def info(self, message: str):
        self._log("INFO", message)

    def warning(self, message: str):
        self._log("WARNING", message)

    def error(self, message: str):
        self._log("ERROR", message)


default_logger = ExperimentLogger()
