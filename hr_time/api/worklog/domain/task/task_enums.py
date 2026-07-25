from enum import Enum
from typing import List


class TaskPriority(Enum):
    """Task priority levels"""
    URGENT = "Urgent"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    NONE = ""

    @classmethod
    def get_priority_order_list(cls) -> List[str]:
        """Return priority values in order from highest to lowest"""
        return [cls.URGENT.value, cls.HIGH.value, cls.MEDIUM.value, cls.LOW.value, cls.NONE.value]


class TaskStatus(Enum):
    """Task workflow status"""
    OPEN = "Open"
    WORKING = "Working"
    PENDING_REVIEW = "Pending Review"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    OVERDUE = "Overdue"
    TEMPLATE = "Template"

    @classmethod
    def active_statuses(cls) -> List[str]:
        """Return statuses that represent active/in-progress tasks"""
        return [cls.OPEN.value, cls.WORKING.value, cls.PENDING_REVIEW.value, cls.OVERDUE.value]

    @classmethod
    def completed_statuses(cls) -> List[str]:
        """Return statuses that represent completed/to be excluded tasks for processing"""
        return [cls.COMPLETED.value, cls.CANCELLED.value]

    def is_active(self) -> bool:
        """Check if task is still active"""
        return self.value in self.active_statuses()

    def is_completed(self) -> bool:
        """Check if task is completed or cancelled"""
        return self.value in self.completed_statuses()


class TaskType(Enum):
    """Task classification type"""
    ASSIGNED = "assigned"  # tasks assigned to user
    GENERIC = "generic"    # Generic tasks like meetings, housework
