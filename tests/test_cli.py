"""
Unit tests for CLI module (habit_tracker/cli.py).
"""

import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from habit_tracker.cli import main, parse_date
from habit_tracker.storage import JSONStorage
from habit_tracker.models import Habit


class TestCLI(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.test_dir) / "habits.json")
        self.log_file = str(Path(self.test_dir) / "app.log")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _run_cli(self, args_list):
        """Helper to run CLI main with test db and log configurations."""
        full_args = ["--db", self.db_path, "--log-file", self.log_file, "--quiet"] + args_list
        f_out = io.StringIO()
        f_err = io.StringIO()
        with redirect_stdout(f_out), redirect_stderr(f_err):
            exit_code = main(full_args)
        return exit_code, f_out.getvalue(), f_err.getvalue()

    def test_cli_add_and_list(self):
        """Test adding a habit and listing it."""
        # Add habit
        code, out, _ = self._run_cli(["add", "Morning Jog", "-c", "Fitness", "-d", "30 min jog"])
        self.assertEqual(code, 0)
        self.assertIn("Successfully added habit #1", out)

        # List habits
        code, out, _ = self._run_cli(["list"])
        self.assertEqual(code, 0)
        self.assertIn("Morning Jog", out)
        self.assertIn("Fitness", out)
        self.assertIn("[ ]", out)

    def test_cli_add_numeric_and_check(self):
        """Test adding numeric habit, logging progress, and checking completed state."""
        # Add numeric habit
        code, _, _ = self._run_cli(["add", "Water", "-t", "numeric", "-v", "8", "-u", "glasses", "-c", "Health"])
        self.assertEqual(code, 0)

        # Partial check
        code, out, _ = self._run_cli(["check", "1", "-v", "4"])
        self.assertEqual(code, 0)
        self.assertIn("incomplete/in-progress", out)

        # Verify in list
        code, out, _ = self._run_cli(["list"])
        self.assertIn("4/8 glasses", out)
        self.assertIn("[ ]", out)

        # Full check
        code, out, _ = self._run_cli(["check", "1", "-v", "8"])
        self.assertEqual(code, 0)
        self.assertIn("completed", out)

        # Verify completed in list
        code, out, _ = self._run_cli(["list"])
        self.assertIn("8/8 glasses", out)
        self.assertIn("[X]", out)

    def test_cli_update(self):
        """Test updating habit name and target."""
        self._run_cli(["add", "Reading"])
        code, out, _ = self._run_cli(["update", "1", "-n", "Deep Reading", "-c", "Mindset"])
        self.assertEqual(code, 0)
        self.assertIn("Deep Reading", out)

        code, out, _ = self._run_cli(["list"])
        self.assertIn("Deep Reading", out)
        self.assertIn("Mindset", out)

    def test_cli_delete(self):
        """Test archiving/deleting habit."""
        self._run_cli(["add", "Meditate"])
        code, out, _ = self._run_cli(["delete", "1"])
        self.assertEqual(code, 0)
        self.assertIn("archived", out)

        # Should not show in active list
        code, out, _ = self._run_cli(["list"])
        self.assertIn("No habits found", out)

        # Should show in all list
        code, out, _ = self._run_cli(["list", "-a"])
        self.assertIn("Meditate (archived)", out)

    def test_cli_invalid_habit_id_error(self):
        """Test friendly error message on non-existent habit."""
        code, out, err = self._run_cli(["check", "999"])
        self.assertEqual(code, 1)
        self.assertIn("Habit with ID #999 was not found", err)


if __name__ == "__main__":
    unittest.main()
