"""
Daily Habit Tracker - Main Application Entry Point.

Delegates execution to the dedicated CLI module (`habit_tracker.cli`).
"""

import sys
from habit_tracker.cli import main

if __name__ == "__main__":
    sys.exit(main())
