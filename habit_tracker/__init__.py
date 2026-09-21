"""
Habit Tracker Package
A modular, extensible CLI daily habit tracking application.
"""

from habit_tracker.models import Habit, HabitLog, TargetType, Frequency
from habit_tracker.exceptions import (
    HabitTrackerError,
    HabitNotFoundError,
    HabitValidationError,
    StorageError,
    StorageCorruptionError,
)
from habit_tracker.logger import setup_logger, get_logger

__version__ = "1.0.0"

__all__ = [
    "Habit",
    "HabitLog",
    "TargetType",
    "Frequency",
    "HabitTrackerError",
    "HabitNotFoundError",
    "HabitValidationError",
    "StorageError",
    "StorageCorruptionError",
    "setup_logger",
    "get_logger",
]
