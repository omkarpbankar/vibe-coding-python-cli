"""
Unit tests for JSONStorage persistence module with error handling and recovery.
"""

import os
import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from habit_tracker.models import Habit, HabitLog, TargetType, Frequency
from habit_tracker.storage import JSONStorage
from habit_tracker.exceptions import (
    HabitTrackerError,
    HabitNotFoundError,
    HabitValidationError,
    StorageError,
    StorageCorruptionError,
)


class TestJSONStorage(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory and JSONStorage instance."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_habits.json"
        self.storage = JSONStorage(filepath=self.db_path)

    def tearDown(self):
        """Clean up temporary test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initial_file_creation(self):
        """Ensure initial JSON file is created with version, habits, logs."""
        self.assertTrue(self.db_path.exists())
        habits = self.storage.get_all_habits()
        self.assertEqual(len(habits), 0)

    def test_add_and_get_habit(self):
        """Test adding habits and retrieving by ID."""
        habit = Habit(name="Read 20 mins", category="Learning")
        saved = self.storage.add_habit(habit)
        self.assertIsNotNone(saved.id)
        self.assertEqual(saved.id, 1)

        fetched = self.storage.get_habit(1)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Read 20 mins")
        self.assertEqual(fetched.category, "Learning")

    def test_habit_not_found_exception(self):
        """Test that HabitNotFoundError is raised when appropriate."""
        # get_habit with raise_if_not_found=True
        with self.assertRaises(HabitNotFoundError) as ctx:
            self.storage.get_habit(999, raise_if_not_found=True)
        self.assertEqual(ctx.exception.habit_id, 999)

        # log_habit on non-existent habit
        with self.assertRaises(HabitNotFoundError):
            self.storage.log_habit(999, log_date=date.today())

        # delete_habit on non-existent habit
        with self.assertRaises(HabitNotFoundError):
            self.storage.delete_habit(999)

    def test_habit_validation_error(self):
        """Test that HabitValidationError is raised for invalid habit definitions."""
        with self.assertRaises(HabitValidationError):
            self.storage.add_habit(Habit(name=""))

        with self.assertRaises(HabitValidationError):
            self.storage.add_habit(Habit(name="  "))

        with self.assertRaises(HabitValidationError):
            self.storage.add_habit(Habit(name="Exercise", target_value=0))

    def test_corrupted_file_recovery(self):
        """Test that corrupted JSON file does not crash and creates a backup."""
        # 1. Add a valid habit first
        self.storage.add_habit(Habit(name="Yoga"))

        # 2. Corrupt the JSON file with garbage data
        with open(self.db_path, "w", encoding="utf-8") as f:
            f.write("{invalid_json: true, corrupt...")

        # 3. Reading should auto-recover, not crash
        recovered_storage = JSONStorage(filepath=self.db_path, auto_recover=True)
        habits = recovered_storage.get_all_habits()
        self.assertEqual(len(habits), 0)

        # Check that backup file was created
        backup_files = list(Path(self.test_dir).glob("test_habits.corrupt_*.bak"))
        self.assertGreaterEqual(len(backup_files), 1)

    def test_corrupted_file_raises_when_no_auto_recover(self):
        """Test that StorageCorruptionError is raised when auto_recover is False."""
        with open(self.db_path, "w", encoding="utf-8") as f:
            f.write("corrupted non json content")

        storage = JSONStorage(filepath=self.db_path, auto_recover=False)
        with self.assertRaises(StorageCorruptionError):
            storage.get_all_habits()

    def test_update_habit(self):
        """Test updating habit properties."""
        habit = self.storage.add_habit(Habit(name="Old Name", category="Misc"))
        habit.name = "New Name"
        habit.category = "Productivity"
        success = self.storage.update_habit(habit)
        self.assertTrue(success)

        reloaded = self.storage.get_habit(habit.id)
        self.assertEqual(reloaded.name, "New Name")
        self.assertEqual(reloaded.category, "Productivity")

    def test_delete_habit(self):
        """Test hard delete and soft delete."""
        h1 = self.storage.add_habit(Habit(name="To Soft Delete"))
        h2 = self.storage.add_habit(Habit(name="To Hard Delete"))

        # Soft delete h1
        self.storage.delete_habit(h1.id, soft_delete=True)
        active_habits = self.storage.get_all_habits(active_only=True)
        self.assertEqual(len(active_habits), 1)
        self.assertEqual(active_habits[0].id, h2.id)

        # Hard delete h2
        self.storage.delete_habit(h2.id, soft_delete=False)
        all_habits = self.storage.get_all_habits(active_only=False)
        self.assertEqual(len(all_habits), 1)

    def test_log_habit_and_retrieve(self):
        """Test logging daily completions and retrieving logs."""
        habit = self.storage.add_habit(
            Habit(name="Water", target_type=TargetType.NUMERIC, target_value=8.0, unit="glasses")
        )
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Log today
        log_today = self.storage.log_habit(habit.id, log_date=today, value=8.0, notes="Hydrated!")
        self.assertTrue(log_today.completed)
        self.assertEqual(log_today.value, 8.0)

        # Log yesterday (partial)
        log_yest = self.storage.log_habit(habit.id, log_date=yesterday, value=5.0)
        self.assertFalse(log_yest.completed)

        # Fetch logs for habit
        logs = self.storage.get_logs(habit_id=habit.id)
        self.assertEqual(len(logs), 2)

        reloaded_habit = self.storage.get_habit(habit.id)
        self.assertTrue(reloaded_habit.is_completed_today)
        self.assertEqual(reloaded_habit.today_progress, 8.0)


if __name__ == "__main__":
    unittest.main()
