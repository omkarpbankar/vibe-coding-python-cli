"""
CLI Module for Habit Tracker.

Provides a robust, modular command-line interface using `argparse`.
Supports subcommands for adding, listing, checking/logging, updating, and deleting habits.
"""

from __future__ import annotations
import argparse
import sys
from datetime import date, datetime
from typing import Optional, List

from habit_tracker.models import Habit, TargetType, Frequency
from habit_tracker.storage import JSONStorage
from habit_tracker.exceptions import (
    HabitTrackerError,
    HabitNotFoundError,
    HabitValidationError,
    StorageError,
)
from habit_tracker.logger import get_logger, setup_logger

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = get_logger("cli")


def parse_date(date_str: Optional[str]) -> date:
    """Parse date from YYYY-MM-DD format or return today's date."""
    if not date_str or date_str.lower() in ("today", "now"):
        return date.today()
    if date_str.lower() == "yesterday":
        from datetime import timedelta
        return date.today() - timedelta(days=1)
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HabitValidationError(f"Invalid date format '{date_str}'. Please use YYYY-MM-DD.")


def create_parser() -> argparse.ArgumentParser:
    """Build and return the argparse argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="habit",
        description="Daily Habit Tracker - Build and maintain lasting routines from your terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--db",
        type=str,
        default="data/habits.json",
        help="Path to the habit database JSON file (default: data/habits.json)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="app.log",
        help="Path to the log output file (default: app.log)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational console logs",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # --- 1. ADD SUBCOMMAND ---
    add_parser = subparsers.add_parser("add", help="Add a new habit to track")
    add_parser.add_argument("name", type=str, help="Name of the habit (e.g. 'Morning Jog')")
    add_parser.add_argument("-d", "--description", type=str, default="", help="Optional detailed description")
    add_parser.add_argument("-c", "--category", type=str, default="General", help="Category (e.g. Health, Learning, Mindset)")
    add_parser.add_argument(
        "-t", "--type",
        choices=["boolean", "numeric"],
        default="boolean",
        help="Habit target type: 'boolean' (yes/no) or 'numeric' (measurable target)",
    )
    add_parser.add_argument("-v", "--target", type=float, default=1.0, help="Target value for numeric habits (e.g. 8.0)")
    add_parser.add_argument("-u", "--unit", type=str, default="", help="Unit of measurement (e.g. 'glasses', 'pages', 'mins')")
    add_parser.add_argument(
        "-f", "--frequency",
        choices=["daily", "weekdays", "weekends", "weekly"],
        default="daily",
        help="Tracking frequency (default: daily)",
    )

    # --- 2. LIST SUBCOMMAND ---
    list_parser = subparsers.add_parser("list", help="List active habits and today's status")
    list_parser.add_argument("-a", "--all", action="store_true", help="Include archived/inactive habits")
    list_parser.add_argument("-c", "--category", type=str, default=None, help="Filter habits by category")
    list_parser.add_argument("--date", type=str, default=None, help="Show status for date (YYYY-MM-DD, 'yesterday', or 'today')")

    # --- 3. CHECK / LOG SUBCOMMAND ---
    check_parser = subparsers.add_parser("check", help="Mark a habit as completed or log progress")
    check_parser.add_argument("habit_id", type=int, help="ID of the habit to check")
    check_parser.add_argument("-v", "--value", type=float, default=None, help="Progress value for numeric habits (e.g. 8.0)")
    check_parser.add_argument("-d", "--date", type=str, default=None, help="Date to log for (YYYY-MM-DD, default today)")
    check_parser.add_argument("-n", "--notes", type=str, default="", help="Optional reflection notes for today")
    check_parser.add_argument("--uncheck", action="store_true", help="Mark habit as incomplete for date")

    # --- 4. UPDATE SUBCOMMAND ---
    update_parser = subparsers.add_parser("update", help="Update habit properties")
    update_parser.add_argument("habit_id", type=int, help="ID of the habit to update")
    update_parser.add_argument("-n", "--name", type=str, default=None, help="New habit name")
    update_parser.add_argument("-d", "--description", type=str, default=None, help="New description")
    update_parser.add_argument("-c", "--category", type=str, default=None, help="New category")
    update_parser.add_argument("-v", "--target", type=float, default=None, help="New target value")
    update_parser.add_argument("-u", "--unit", type=str, default=None, help="New unit")

    # --- 5. DELETE SUBCOMMAND ---
    del_parser = subparsers.add_parser("delete", help="Delete or archive a habit")
    del_parser.add_argument("habit_id", type=int, help="ID of the habit to delete")
    del_parser.add_argument("--hard", action="store_true", help="Permanently delete instead of archiving")

    return parser


# --- Subcommand Handler Functions ---

def handle_add(args: argparse.Namespace, storage: JSONStorage) -> int:
    """Handle 'add' subcommand."""
    habit = Habit(
        name=args.name,
        description=args.description,
        category=args.category,
        target_type=TargetType(args.type),
        target_value=args.target,
        unit=args.unit,
        frequency=Frequency(args.frequency),
    )
    saved = storage.add_habit(habit)
    print(f"[✔] Successfully added habit #{saved.id}: '{saved.name}' [{saved.category}]")
    return 0


def handle_list(args: argparse.Namespace, storage: JSONStorage) -> int:
    """Handle 'list' subcommand."""
    target_date = parse_date(args.date)
    habits = storage.get_all_habits(active_only=not args.all)

    if args.category:
        habits = [h for h in habits if h.category.lower() == args.category.lower()]

    if not habits:
        print("[!] No habits found matching your criteria. Use 'habit add <name>' to create one.")
        return 0

    print("=" * 70)
    print(f"  HABIT TRACKER - STATUS FOR {target_date.isoformat()}")
    print("=" * 70)
    print(f" {'STATUS':<6} {'ID':<4} {'NAME':<24} {'CATEGORY':<12} {'TARGET / PROGRESS'}")
    print("-" * 70)

    for h in habits:
        # Find log for requested date
        log_match = next((l for l in h.logs if l.log_date == target_date), None)
        is_done = log_match.completed if log_match else False
        progress_val = log_match.value if log_match else 0.0

        status_sym = "[X]" if is_done else "[ ]"
        progress_desc = (
            f"{progress_val:.0f}/{h.target_value:.0f} {h.unit}"
            if h.target_type == TargetType.NUMERIC
            else ("Completed" if is_done else "Pending")
        )

        archived_tag = " (archived)" if not h.is_active else ""
        print(f"  {status_sym:<5} #{h.id:<3} {h.name + archived_tag:<24} {h.category:<12} {progress_desc}")

    print("=" * 70)
    return 0


def handle_check(args: argparse.Namespace, storage: JSONStorage) -> int:
    """Handle 'check' subcommand."""
    target_date = parse_date(args.date)
    completed = not args.uncheck

    log = storage.log_habit(
        habit_id=args.habit_id,
        log_date=target_date,
        completed=completed,
        value=args.value,
        notes=args.notes,
    )
    status_text = "completed" if log.completed else "incomplete/in-progress"
    print(f"[✔] Habit #{args.habit_id} marked as {status_text} for {target_date.isoformat()}.")
    return 0


def handle_update(args: argparse.Namespace, storage: JSONStorage) -> int:
    """Handle 'update' subcommand."""
    habit = storage.get_habit(args.habit_id, raise_if_not_found=True)
    if args.name is not None:
        habit.name = args.name
    if args.description is not None:
        habit.description = args.description
    if args.category is not None:
        habit.category = args.category
    if args.target is not None:
        habit.target_value = args.target
    if args.unit is not None:
        habit.unit = args.unit

    storage.update_habit(habit)
    print(f"[✔] Habit #{habit.id} ('{habit.name}') successfully updated.")
    return 0


def handle_delete(args: argparse.Namespace, storage: JSONStorage) -> int:
    """Handle 'delete' subcommand."""
    storage.delete_habit(args.habit_id, soft_delete=not args.hard)
    action = "permanently deleted" if args.hard else "archived"
    print(f"[✔] Habit #{args.habit_id} {action}.")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main CLI entry point.
    Parses arguments, configures logging, and routes commands.
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Initialize logger
    console_level = 100 if args.quiet else 20  # Suppress console if quiet
    setup_logger(log_file=args.log_file, console_output=not args.quiet)

    # If no subcommand is provided, display help and current list
    if not args.command:
        parser.print_help()
        print("\n" + "-" * 70)
        storage = JSONStorage(filepath=args.db, auto_recover=True)
        handle_list(argparse.Namespace(all=False, category=None, date=None), storage)
        return 0

    # Route subcommands
    try:
        storage = JSONStorage(filepath=args.db, auto_recover=True)

        if args.command == "add":
            return handle_add(args, storage)
        elif args.command == "list":
            return handle_list(args, storage)
        elif args.command == "check":
            return handle_check(args, storage)
        elif args.command == "update":
            return handle_update(args, storage)
        elif args.command == "delete":
            return handle_delete(args, storage)
        else:
            parser.print_help()
            return 1

    except HabitTrackerError as err:
        print(f"[ERROR] {err}", file=sys.stderr)
        logger.error(f"CLI command failed: {err}")
        return 1
    except Exception as exc:
        print(f"[UNEXPECTED ERROR] {exc}", file=sys.stderr)
        logger.exception(f"Unexpected CLI error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
