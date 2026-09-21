"""
Unit tests for Logger module.
"""

import logging
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from habit_tracker.logger import setup_logger, get_logger, DEFAULT_LOGGER_NAME


class TestLogger(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = Path(self.test_dir) / "test_app.log"

        # Clear and close existing handlers from logger if any
        test_log = logging.getLogger(DEFAULT_LOGGER_NAME)
        for h in test_log.handlers[:]:
            h.close()
            test_log.removeHandler(h)

    def tearDown(self):
        # Clear handlers and release file locks
        test_log = logging.getLogger(DEFAULT_LOGGER_NAME)
        for h in test_log.handlers[:]:
            h.close()
            test_log.removeHandler(h)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_logger_file_and_content(self):
        """Verify that setup_logger writes formatted logs to the specified file."""
        log = setup_logger(log_file=self.log_file, level=logging.INFO, console_output=False)
        log.info("Test habit created event")
        log.error("Test error event occurred")

        self.assertTrue(self.log_file.exists())
        with open(self.log_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Test habit created event", content)
        self.assertIn("INFO", content)
        self.assertIn("Test error event occurred", content)
        self.assertIn("ERROR", content)

    def test_child_logger(self):
        """Verify child logger inherits parent handlers and logs to file."""
        setup_logger(log_file=self.log_file, level=logging.INFO, console_output=False)
        storage_logger = get_logger("storage")
        storage_logger.info("Storage initialized from child logger")

        with open(self.log_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("habit_tracker.storage", content)
        self.assertIn("Storage initialized from child logger", content)


if __name__ == "__main__":
    unittest.main()
