"""
Custom Exceptions for Habit Tracker.

Provides a structured hierarchy of application-specific exceptions
for error handling, validation, and storage integrity.
"""


class HabitTrackerError(Exception):
    """Base exception for all Habit Tracker application errors."""
    pass


class HabitNotFoundError(HabitTrackerError):
    """Raised when an operation references a habit that does not exist."""
    def __init__(self, habit_id: int, message: str = ""):
        self.habit_id = habit_id
        msg = message or f"Habit with ID #{habit_id} was not found."
        super().__init__(msg)


class HabitValidationError(HabitTrackerError):
    """Raised when habit attributes or log data fail validation."""
    pass


class StorageError(HabitTrackerError):
    """Base exception for persistence and storage failures."""
    pass


class StorageCorruptionError(StorageError):
    """Raised or reported when the storage file is malformed or unreadable."""
    def __init__(self, filepath: str, original_error: Exception):
        self.filepath = filepath
        self.original_error = original_error
        super().__init__(
            f"Corrupted storage file detected at '{filepath}'. Details: {original_error}"
        )
