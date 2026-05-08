from dataclasses import dataclass
from datetime import datetime


@dataclass
class TimesheetLog:
    """Value object for a timesheet time log entry"""
    activity_type: str
    task_id: str
    hours: float
    from_time: datetime
    to_time: datetime
    description: str
    completed: bool = True
    is_billable: bool = True

    def to_dict(self) -> dict:
        """Convert to Frappe-compatible dictionary"""
        return {
            "activity_type": self.activity_type,
            "task": self.task_id,
            "hours": self.hours,
            "from_time": self.from_time,
            "to_time": self.to_time,
            "completed": 1 if self.completed else 0,
            "is_billable": 1 if self.is_billable else 0,
            "description": self.description
        }
