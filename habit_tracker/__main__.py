"""
Package entry point for running habit_tracker via `python -m habit_tracker`.
"""

import sys
from habit_tracker.cli import main

if __name__ == "__main__":
    sys.exit(main())
