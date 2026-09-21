"""
Unit tests for core Habit and HabitLog data models.
"""

import unittest
from datetime import date, timedelta
from habit_tracker.models import Habit, HabitLog, TargetType, Frequency


class TestHabitModels(unittest.TestCase):

    def test_habit_creation_defaults(self):
        """Test default values when creating a Habit."""
        habit = Habit(name="Morning Jog")
        self.assertEqual(habit.name, "Morning Jog")
        self.assertEqual(habit.category, "General")
        self.assertEqual(habit.target_type, TargetType.BOOLEAN)
        self.assertEqual(habit.frequency, Frequency.DAILY)
        self.assertTrue(habit.is_active)
        self.assertFalse(habit.is_completed_today)
        self.assertEqual(habit.today_progress, 0.0)

    def test_habit_mark_completed_today(self):
        """Test marking a boolean habit as completed today."""
        habit = Habit(id=1, name="Read 30 mins")
        self.assertFalse(habit.is_completed_today)
        self.assertEqual(habit.today_status_symbol, "[ ]")

        log = habit.mark_completed_for_date(notes="Finished chapter 2")
        self.assertTrue(habit.is_completed_today)
        self.assertEqual(habit.today_status_symbol, "[X]")
        self.assertEqual(log.notes, "Finished chapter 2")
        self.assertEqual(log.log_date, date.today())

    def test_numeric_habit_completion(self):
        """Test numeric habit progress and completion logic."""
        habit = Habit(
            id=2,
            name="Drink Water",
            target_type=TargetType.NUMERIC,
            target_value=8.0,
            unit="glasses",
        )
        # Partial progress (4 out of 8) -> Not completed
        habit.mark_completed_for_date(value=4.0)
        self.assertFalse(habit.is_completed_today)
        self.assertEqual(habit.today_progress, 4.0)

        # Reaching target (8 out of 8) -> Completed
        habit.mark_completed_for_date(value=8.0)
        self.assertTrue(habit.is_completed_today)
        self.assertEqual(habit.today_progress, 8.0)

    def test_habit_backfill_past_date(self):
        """Test marking completion for a past date."""
        habit = Habit(id=3, name="Yoga")
        yesterday = date.today() - timedelta(days=1)
        log = habit.mark_completed_for_date(target_date=yesterday)

        self.assertEqual(log.log_date, yesterday)
        self.assertTrue(log.completed)
        # Today should still be false
        self.assertFalse(habit.is_completed_today)

    def test_serialization_roundtrip(self):
        """Test to_dict and from_dict serialization."""
        habit = Habit(
            id=5,
            name="Code Python",
            description="Build CLI tools",
            category="Programming",
            target_type=TargetType.NUMERIC,
            target_value=2.0,
            unit="hours",
            frequency=Frequency.DAILY,
        )
        data = habit.to_dict()
        restored = Habit.from_dict(data)

        self.assertEqual(restored.id, habit.id)
        self.assertEqual(restored.name, habit.name)
        self.assertEqual(restored.description, habit.description)
        self.assertEqual(restored.category, habit.category)
        self.assertEqual(restored.target_type, habit.target_type)
        self.assertEqual(restored.target_value, habit.target_value)
        self.assertEqual(restored.unit, habit.unit)
        self.assertEqual(restored.frequency, habit.frequency)


if __name__ == "__main__":
    unittest.main()
