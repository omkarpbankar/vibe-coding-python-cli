# 🌟 Daily Habit Tracker CLI

A modular, extensible, and robust Command-Line Daily Habit Tracker built in Python. Track your daily routines, measure quantifiable goals, maintain streaks, and persist your progress effortlessly with zero external dependencies.

---

## 🚀 Key Features

* **Modular Architecture**: Clean separation of concerns across models, persistence, logging, custom exceptions, and CLI handlers.
* **Flexible Habit Types**:
  * **Boolean Habits**: Simple *done / not done* routines (e.g., *Morning Meditation*, *Yoga*).
  * **Numeric Habits**: Quantifiable targets with customizable units (e.g., *Drink 8 glasses of water*, *Read 20 pages*).
* **Robust JSON Persistence**:
  * Safe file operations with atomic writes via temporary files.
  * Auto-recovery and automatic backup creation (`.corrupt_<timestamp>.bak`) if files are damaged.
* **Comprehensive Error Handling**:
  * Custom exception hierarchy (`HabitTrackerError`, `HabitNotFoundError`, `HabitValidationError`, `StorageCorruptionError`).
  * Protected operations with guaranteed cleanup via `try-except-finally` blocks.
* **Dual-Destination Logging**:
  * Detailed timestamped log entries stored in `app.log`.
  * Real-time formatted status events output to the console stream.
* **Zero External Dependencies**: Powered purely by Python 3.8+ Standard Library.

---

## 📁 Project Structure

```text
vibe-coding-python-cli/
│
├── habit_tracker/                 # Core application package
│   ├── __init__.py                # Package initialization & exports
│   ├── __main__.py                # Module execution entry point (`python -m habit_tracker`)
│   ├── models.py                  # Habit, HabitLog, TargetType, Frequency data models
│   ├── storage.py                 # JSON persistence, CRUD operations & corruption recovery
│   ├── logger.py                  # Dual file (app.log) and console stream logger setup
│   ├── exceptions.py              # Custom application exception hierarchy
│   └── cli.py                     # Argument parsing (argparse) & subcommand routing
│
├── tests/                         # Comprehensive unit test suite
│   ├── test_models.py             # Model creation, serialization, & completion tests
│   ├── test_storage.py            # Persistence, auto-increment, & corruption tests
│   ├── test_logger.py             # File and stream logging tests
│   └── test_cli.py                # Command-line interface & argument parsing tests
│
├── data/                          # Data persistence directory
│   └── habits.json                # Local JSON database file
│
├── app.log                        # Application execution and event logs
├── main.py                        # Root convenience entry point script
├── pyproject.toml                 # Package configuration
├── requirements.txt               # Dependencies file (Standard Library)
└── README.md                      # Documentation & CLI reference
```

---

## 🛠️ Installation & Requirements

### Prerequisites
* Python **3.8 or higher**

### Clone & Setup
```bash
# Clone the repository
git clone https://github.com/omkarpbankar/vibe-coding-python-cli.git
cd vibe-coding-python-cli
```

### Optional: Install as a CLI Command
You can optionally install the package in editable mode:
```bash
pip install -e .
```
This enables the direct `habit` command from any terminal location.

---

## 💻 Usage & Command Reference

You can execute commands via `python main.py`, `python -m habit_tracker`, or `habit` (if installed).

### 1. View Help
```bash
python main.py --help
```

### 2. Add a Habit (`add`)

#### Add a Simple Boolean Habit:
```bash
python main.py add "Morning Meditation" -c "Mindset" -d "15 minutes of mindfulness"
```

#### Add a Numeric Measurable Habit:
```bash
python main.py add "Water Intake" -c "Health" -t numeric -v 8 -u "glasses"
python main.py add "Evening Walk" -c "Fitness" -t numeric -v 5000 -u "steps"
python main.py add "Read Books" -c "Learning" -t numeric -v 20 -u "pages" -f weekdays
```

**Options for `add`:**
* `-d`, `--description`: Optional description of the habit.
* `-c`, `--category`: Category tag (e.g., `Health`, `Learning`, `Mindset`, default: `General`).
* `-t`, `--type`: Target type (`boolean` or `numeric`, default: `boolean`).
* `-v`, `--target`: Target amount for numeric habits (default: `1.0`).
* `-u`, `--unit`: Unit of measurement (e.g., `glasses`, `pages`, `steps`, `mins`).
* `-f`, `--frequency`: Cadence (`daily`, `weekdays`, `weekends`, `weekly`).

---

### 3. List Habits (`list`)

#### View Today's Status:
```bash
python main.py list
```
*Output:*
```text
======================================================================
  HABIT TRACKER - STATUS FOR 2026-09-22
======================================================================
 STATUS ID   NAME                     CATEGORY     TARGET / PROGRESS
----------------------------------------------------------------------
  [X]   #1   Morning Meditation       Mindset      Completed
  [X]   #2   Water Intake             Health       8/8 glasses
  [ ]   #3   Read Books               Learning     0/20 pages
  [X]   #4   Evening Walk             Fitness      5000/5000 steps
======================================================================
```

#### Filter by Category:
```bash
python main.py list -c Health
```

#### View Historical Dates or Archived Habits:
```bash
# Check status for yesterday or a specific date
python main.py list --date yesterday
python main.py list --date 2026-09-21

# Include archived/inactive habits
python main.py list --all
```

---

### 4. Check Off / Log Progress (`check`)

#### Check Off a Boolean Habit:
```bash
python main.py check 1
```

#### Log Progress for a Numeric Habit:
```bash
# Log partial progress
python main.py check 2 -v 4 -n "Drank morning bottle"

# Log target completion
python main.py check 2 -v 8 -n "Finished 8 glasses target"
```

#### Backfill for Past Dates:
```bash
python main.py check 1 --date yesterday -n "Completed yesterday evening"
python main.py check 2 -v 8 --date 2026-09-20
```

#### Uncheck a Habit:
```bash
python main.py check 1 --uncheck
```

---

### 5. Update a Habit (`update`)
```bash
# Rename habit or change category
python main.py update 1 -n "Deep Morning Meditation" -c "Mindfulness"

# Adjust target amount
python main.py update 2 -v 10 -u "glasses"
```

---

### 6. Delete / Archive a Habit (`delete`)
```bash
# Soft-archive habit (preserves historical logs)
python main.py delete 3

# Permanently delete habit and its history
python main.py delete 3 --hard
```

---

## 🛡️ Error Handling & Reliability

The application incorporates safety measures to prevent crashes:

1. **Custom Exceptions**:
   * `HabitNotFoundError`: Raised and handled cleanly when an invalid habit ID is provided.
   * `HabitValidationError`: Enforces valid input (non-empty names, positive numeric targets).
   * `StorageCorruptionError`: Detects malformed data files.
2. **Auto-Recovery**: If `data/habits.json` is corrupted, the application backs it up to `.corrupt_<timestamp>.bak` and initializes a fresh schema so tracking continues without crashing.
3. **Atomic Writes**: Uses temporary files with filesystem flush before replacement to protect against incomplete write operations.

---

## 📝 Logging System

Application operations and errors are logged to both the terminal and `app.log`.

```text
2026-09-22 00:14:46 | INFO     | habit_tracker | === Habit Tracker Application Started ===
2026-09-22 00:14:46 | INFO     | habit_tracker.storage | Habit created: #1 'Morning Meditation' (Category: Mindset, Target: 1.0 done)
2026-09-22 00:14:46 | INFO     | habit_tracker.storage | Habit completion recorded: #1 'Morning Meditation' on 2026-09-22 [Progress: 1.0/1.0 , Completed: True]
```

To suppress informational logs in the terminal, pass the `--quiet` flag:
```bash
python main.py --quiet list
```

---

## 🧪 Running Automated Tests

Run all unit tests across models, storage, logger, and CLI modules:

```bash
python -m unittest discover tests
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.