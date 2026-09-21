"""
Storage Module for Habit Tracker with Robust Error Handling and Logging.

Provides JSON-based file persistence with comprehensive try-except-finally blocks,
safe fallback on corrupted files, backup creation, custom exception handling,
and structured event logging.
"""

from __future__ import annotations
import json
import os
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from habit_tracker.models import Habit, HabitLog
from habit_tracker.exceptions import (
    HabitTrackerError,
    HabitNotFoundError,
    HabitValidationError,
    StorageError,
    StorageCorruptionError,
)
from habit_tracker.logger import get_logger

logger = get_logger("storage")


class JSONStorage:
    """
    Handles persisting and loading Habit and HabitLog entities to/from a JSON file
    with robust error handling, corruption recovery, and event logging.
    """

    def __init__(self, filepath: str | Path = "data/habits.json", auto_recover: bool = True):
        self.filepath = Path(filepath)
        self.auto_recover = auto_recover
        self._ensure_file_exists()

    def _get_default_schema(self) -> Dict[str, Any]:
        """Returns the default clean database schema."""
        return {
            "version": "1.0",
            "habits": [],
            "logs": [],
        }

    def _ensure_file_exists(self) -> None:
        """Create parent directory and initial JSON structure if not existing."""
        file_handle = None
        try:
            if not self.filepath.parent.exists():
                self.filepath.parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created storage directory: {self.filepath.parent}")

            if not self.filepath.exists() or self.filepath.stat().st_size == 0:
                self._save_raw(self._get_default_schema())
                logger.info(f"Initialized new storage file at: {self.filepath}")
        except OSError as exc:
            logger.error(f"Failed to create storage at '{self.filepath}': {exc}")
            raise StorageError(f"Failed to create storage directory or file at '{self.filepath}': {exc}") from exc
        finally:
            if file_handle is not None and not file_handle.closed:
                file_handle.close()

    def _load_raw(self) -> Dict[str, Any]:
        """
        Load raw dictionary data from JSON file with try-except-finally handling.
        Recovers gracefully if the file is corrupted.
        """
        if not self.filepath.exists():
            return self._get_default_schema()

        file_obj = None
        data = None
        try:
            file_obj = open(self.filepath, "r", encoding="utf-8")
            content = file_obj.read().strip()
            if not content:
                return self._get_default_schema()
            data = json.loads(content)

            # Validate basic schema integrity
            if not isinstance(data, dict) or "habits" not in data or "logs" not in data:
                raise ValueError("JSON schema missing required 'habits' or 'logs' keys.")

            return data

        except (json.JSONDecodeError, ValueError) as err:
            logger.warning(f"Corrupted storage file detected at {self.filepath}: {err}")
            if self.auto_recover:
                self._handle_corrupted_file(err)
                return self._get_default_schema()
            else:
                raise StorageCorruptionError(str(self.filepath), err) from err

        except OSError as io_err:
            logger.error(f"I/O error reading storage '{self.filepath}': {io_err}")
            raise StorageError(f"I/O error reading from '{self.filepath}': {io_err}") from io_err

        finally:
            if file_obj is not None and not file_obj.closed:
                file_obj.close()

    def _save_raw(self, data: Dict[str, Any]) -> None:
        """
        Write raw dictionary data to JSON file with try-except-finally handling.
        """
        temp_file = self.filepath.with_suffix(".tmp")
        file_obj = None
        success = False

        try:
            file_obj = open(temp_file, "w", encoding="utf-8")
            json.dump(data, file_obj, indent=2, ensure_ascii=False)
            file_obj.flush()
            os.fsync(file_obj.fileno())
            file_obj.close()

            shutil.move(str(temp_file), str(self.filepath))
            success = True

        except OSError as exc:
            logger.error(f"Failed to write storage file '{self.filepath}': {exc}")
            raise StorageError(f"Failed to write data to '{self.filepath}': {exc}") from exc

        finally:
            if file_obj is not None and not file_obj.closed:
                file_obj.close()
            if not success and temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass

    def _handle_corrupted_file(self, error: Exception) -> None:
        """
        Backup the corrupted file to a `.corrupt.bak` copy and initialize a fresh database.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.filepath.with_suffix(f".corrupt_{timestamp}.bak")
        try:
            if self.filepath.exists():
                shutil.copy2(self.filepath, backup_path)
                logger.info(f"Corrupted data successfully backed up to: {backup_path}")
        except OSError as e:
            logger.error(f"Could not create backup of corrupted file: {e}")
        finally:
            self._save_raw(self._get_default_schema())

    def _next_habit_id(self, habits: List[Dict[str, Any]]) -> int:
        """Generate the next auto-incrementing ID for a habit."""
        if not habits:
            return 1
        return max(h.get("id", 0) for h in habits) + 1

    def _next_log_id(self, logs: List[Dict[str, Any]]) -> int:
        """Generate the next auto-incrementing ID for a log."""
        if not logs:
            return 1
        return max(l.get("id", 0) for l in logs) + 1

    # --- Habit CRUD Operations ---

    def add_habit(self, habit: Habit) -> Habit:
        """
        Save a new habit to the JSON storage with validation and logging.
        """
        if not habit.name or not habit.name.strip():
            logger.error("Habit creation failed: Empty habit name provided.")
            raise HabitValidationError("Habit name cannot be empty.")

        if habit.target_value <= 0:
            logger.error(f"Habit creation failed: Invalid target value ({habit.target_value}).")
            raise HabitValidationError("Habit target value must be greater than 0.")

        data = self._load_raw()
        if habit.id is None:
            habit.id = self._next_habit_id(data["habits"])

        data["habits"] = [h for h in data["habits"] if h.get("id") != habit.id]
        data["habits"].append(habit.to_dict())
        self._save_raw(data)

        logger.info(
            f"Habit created: #{habit.id} '{habit.name}' (Category: {habit.category}, Target: {habit.target_value} {habit.unit or 'done'})"
        )
        return habit

    def get_habit(self, habit_id: int, raise_if_not_found: bool = False) -> Optional[Habit]:
        """
        Retrieve a specific habit by its ID.
        Raises HabitNotFoundError if not found and raise_if_not_found=True.
        """
        data = self._load_raw()
        for h_dict in data.get("habits", []):
            if h_dict.get("id") == habit_id:
                habit = Habit.from_dict(h_dict)
                habit.logs = self.get_logs(habit_id=habit.id)
                today = date.today()
                for log in habit.logs:
                    if log.log_date == today:
                        habit.today_log = log
                        break
                return habit

        if raise_if_not_found:
            logger.error(f"Habit lookup failed: Habit #{habit_id} does not exist.")
            raise HabitNotFoundError(habit_id)
        return None

    def get_all_habits(self, active_only: bool = True) -> List[Habit]:
        """
        Retrieve all habits, attaching their logs.
        """
        data = self._load_raw()
        all_logs = [HabitLog.from_dict(l) for l in data.get("logs", [])]
        today = date.today()

        habits: List[Habit] = []
        for h_dict in data.get("habits", []):
            habit = Habit.from_dict(h_dict)
            if active_only and not habit.is_active:
                continue

            habit_logs = [l for l in all_logs if l.habit_id == habit.id]
            habit.logs = habit_logs
            for log in habit_logs:
                if log.log_date == today:
                    habit.today_log = log
                    break

            habits.append(habit)

        return habits

    def update_habit(self, habit: Habit) -> bool:
        """Update an existing habit in JSON storage with logging."""
        if habit.id is None:
            logger.error("Habit update failed: Habit ID missing.")
            raise HabitValidationError("Cannot update habit without an ID.")

        if not habit.name or not habit.name.strip():
            logger.error(f"Habit update failed: Empty habit name for habit #{habit.id}.")
            raise HabitValidationError("Habit name cannot be empty.")

        data = self._load_raw()
        updated = False
        new_habits = []
        for h_dict in data.get("habits", []):
            if h_dict.get("id") == habit.id:
                new_habits.append(habit.to_dict())
                updated = True
            else:
                new_habits.append(h_dict)

        if not updated:
            logger.error(f"Habit update failed: Habit #{habit.id} not found.")
            raise HabitNotFoundError(habit.id)

        data["habits"] = new_habits
        self._save_raw(data)
        logger.info(f"Habit updated: #{habit.id} '{habit.name}'")
        return True

    def delete_habit(self, habit_id: int, soft_delete: bool = False) -> bool:
        """
        Delete a habit by ID. Raises HabitNotFoundError if habit does not exist.
        """
        data = self._load_raw()
        habit_exists = any(h.get("id") == habit_id for h in data.get("habits", []))
        if not habit_exists:
            logger.error(f"Habit deletion failed: Habit #{habit_id} not found.")
            raise HabitNotFoundError(habit_id)

        if soft_delete:
            for h in data.get("habits", []):
                if h.get("id") == habit_id:
                    h["is_active"] = False
                    self._save_raw(data)
                    logger.info(f"Habit #{habit_id} archived (soft deleted).")
                    return True
            return False
        else:
            data["habits"] = [h for h in data.get("habits", []) if h.get("id") != habit_id]
            data["logs"] = [l for l in data.get("logs", []) if l.get("habit_id") != habit_id]
            self._save_raw(data)
            logger.info(f"Habit #{habit_id} permanently deleted.")
            return True

    # --- Habit Log Operations ---

    def log_habit(
        self,
        habit_id: int,
        log_date: Optional[date] = None,
        completed: bool = True,
        value: Optional[float] = None,
        notes: str = "",
    ) -> HabitLog:
        """
        Record or update a completion log for a habit with logging.
        Raises HabitNotFoundError if habit does not exist.
        """
        habit = self.get_habit(habit_id, raise_if_not_found=True)

        if log_date is None:
            log_date = date.today()

        val = value if value is not None else habit.target_value
        is_completed = (
            completed
            if habit.target_type != "numeric"
            else val >= habit.target_value
        )

        data = self._load_raw()
        target_iso = log_date.isoformat()

        existing_log_idx = None
        for i, l_dict in enumerate(data.get("logs", [])):
            if l_dict.get("habit_id") == habit_id and l_dict.get("log_date") == target_iso:
                existing_log_idx = i
                break

        if existing_log_idx is not None:
            log_id = data["logs"][existing_log_idx].get("id")
            log = HabitLog(
                id=log_id,
                habit_id=habit_id,
                log_date=log_date,
                completed=is_completed,
                value=val,
                notes=notes or data["logs"][existing_log_idx].get("notes", ""),
            )
            data["logs"][existing_log_idx] = log.to_dict()
            action_desc = "updated"
        else:
            log_id = self._next_log_id(data.get("logs", []))
            log = HabitLog(
                id=log_id,
                habit_id=habit_id,
                log_date=log_date,
                completed=is_completed,
                value=val,
                notes=notes,
            )
            data.setdefault("logs", []).append(log.to_dict())
            action_desc = "recorded"

        self._save_raw(data)
        logger.info(
            f"Habit completion {action_desc}: #{habit.id} '{habit.name}' on {log_date.isoformat()} "
            f"[Progress: {val}/{habit.target_value} {habit.unit}, Completed: {is_completed}]"
        )
        return log

    def get_logs(
        self,
        habit_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[HabitLog]:
        """Retrieve logs filtered by habit_id and/or date range."""
        data = self._load_raw()
        logs: List[HabitLog] = []

        for l_dict in data.get("logs", []):
            if habit_id is not None and l_dict.get("habit_id") != habit_id:
                continue

            log = HabitLog.from_dict(l_dict)
            if start_date and log.log_date < start_date:
                continue
            if end_date and log.log_date > end_date:
                continue

            logs.append(log)

        logs.sort(key=lambda x: x.log_date)
        return logs
