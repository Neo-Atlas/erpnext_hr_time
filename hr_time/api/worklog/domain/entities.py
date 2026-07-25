from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

from hr_time.api.shared.domain.document_status import DocumentStatus


class WorklogState(Enum):
    NEW = "new"
    WORKING = "working"
    ON_BREAK = "break"
    COMPLETED = "completed"
    HISTORICAL = "historical"


@dataclass
class TaskAllocation:
    """Value object for task allocation within a worklog"""
    task_id: str
    subject: str
    time_spent: float
    expected_time: float
    progress_increment: float
    status: str
    priority: str
    task_desc: str = ""

    def __post_init__(self):
        # Prevent negative time_spent
        if self.time_spent < 0:
            raise ValueError(f"time_spent cannot be negative: {self.time_spent}")

        if self.expected_time < 0:
            raise ValueError(f"expected_time cannot be negative: {self.expected_time}")

    def calculate_progress(self) -> float:
        if self.expected_time <= 0:
            return 0
        return min((self.time_spent / self.expected_time) * 100, 100)


@dataclass
class WorklogEntity:
    """Domain entity representing a worklog"""
    id: Optional[str]
    employee_id: str
    log_time: datetime
    work_desc: str
    time_saved: float
    is_home_office: bool
    ticket_link: Optional[str]
    docstatus: DocumentStatus
    timesheet_id: Optional[str]
    allocations: List[TaskAllocation] = field(default_factory=list)

    @property
    def total_allocated(self) -> float:
        return sum(a.time_spent for a in self.allocations)
