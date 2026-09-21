"""
Core Data Models for Habit Tracker.

Defines the entity classes representing habits, daily completion logs,
and associated data structures.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class TargetType(str, Enum):
    """Type of target for a habit."""
    BOOLEAN = "boolean"      # Simple done / not done
    NUMERIC = "numeric"      # Quantifiable target (e.g., 8 glasses, 30 pages)


class Frequency(str, Enum):
    """Tracking frequency cadence."""
    DAILY = "daily"
    WEEKDAYS = "weekdays"
    WEEKENDS = "weekends"
    WEEKLY = "weekly"


@dataclass
class HabitLog:
    """
    Represents a record of progress/completion for a habit on a specific date.
    """
    habit_id: int
    log_date: date = field(default_factory=date.today)
    completed: bool = True
    value: float = 1.0
    notes: str = ""
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert log instance to dictionary format."""
        return {
            "id": self.id,
            "habit_id": self.habit_id,
            "log_date": self.log_date.isoformat(),
            "completed": self.completed,
            "value": self.value,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HabitLog:
        """Construct a HabitLog instance from dictionary data."""
        log_date = (
            date.fromisoformat(data["log_date"])
            if isinstance(data["log_date"], str)
            else data["log_date"]
        )
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if isinstance(data.get("created_at"), str)
            else data.get("created_at", datetime.now())
        )
        return cls(
            id=data.get("id"),
            habit_id=data["habit_id"],
            log_date=log_date,
            completed=bool(data.get("completed", True)),
            value=float(data.get("value", 1.0)),
            notes=data.get("notes", ""),
            created_at=created_at,
        )


@dataclass
class Habit:
    """
    Represents a habit with tracking configuration and completion state.
    """
    name: str
    description: str = ""
    category: str = "General"
    target_type: TargetType = TargetType.BOOLEAN
    target_value: float = 1.0
    unit: str = ""  # e.g., "pages", "mins", "glasses", "steps"
    frequency: Frequency = Frequency.DAILY
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    # In-memory tracking cache (optional, populated when querying logs)
    today_log: Optional[HabitLog] = None
    logs: List[HabitLog] = field(default_factory=list)

    @property
    def is_completed_today(self) -> bool:
        """
        Check if the habit is marked as completed for today.
        Evaluates either the attached `today_log` or matching date in `logs`.
        """
        if self.today_log is not None:
            return self.today_log.completed

        today = date.today()
        for log in self.logs:
            if log.log_date == today:
                return log.completed
        return False

    @property
    def today_progress(self) -> float:
        """
        Get today's progress value (e.g. 5 out of 8 glasses).
        """
        if self.today_log is not None:
            return self.today_log.value

        today = date.today()
        for log in self.logs:
            if log.log_date == today:
                return log.value
        return 0.0

    @property
    def today_status_symbol(self) -> str:
        """Return a visual check indicator for today ([X] or [ ])."""
        return "[X]" if self.is_completed_today else "[ ]"

    def mark_completed_for_date(
        self,
        target_date: Optional[date] = None,
        value: Optional[float] = None,
        notes: str = ""
    ) -> HabitLog:
        """
        Create a completed HabitLog instance for the specified date (defaults to today).
        """
        if target_date is None:
            target_date = date.today()

        val = value if value is not None else self.target_value
        is_done = val >= self.target_value if self.target_type == TargetType.NUMERIC else True

        log = HabitLog(
            habit_id=self.id or 0,
            log_date=target_date,
            completed=is_done,
            value=val,
            notes=notes,
        )

        if target_date == date.today():
            self.today_log = log

        self.logs.append(log)
        return log

    def to_dict(self) -> Dict[str, Any]:
        """Serialize habit to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "target_type": self.target_type.value if isinstance(self.target_type, TargetType) else self.target_type,
            "target_value": self.target_value,
            "unit": self.unit,
            "frequency": self.frequency.value if isinstance(self.frequency, Frequency) else self.frequency,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "is_completed_today": self.is_completed_today,
            "today_progress": self.today_progress,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Habit:
        """Instantiate a Habit from a dictionary."""
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if isinstance(data.get("created_at"), str)
            else data.get("created_at", datetime.now())
        )
        target_type = (
            TargetType(data["target_type"])
            if "target_type" in data
            else TargetType.BOOLEAN
        )
        frequency = (
            Frequency(data["frequency"])
            if "frequency" in data
            else Frequency.DAILY
        )

        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data.get("description", ""),
            category=data.get("category", "General"),
            target_type=target_type,
            target_value=float(data.get("target_value", 1.0)),
            unit=data.get("unit", ""),
            frequency=frequency,
            created_at=created_at,
            is_active=bool(data.get("is_active", True)),
        )

    def __repr__(self) -> str:
        status = "DONE" if self.is_completed_today else "PENDING"
        return f"<Habit id={self.id} name='{self.name}' category='{self.category}' today={status}>"
