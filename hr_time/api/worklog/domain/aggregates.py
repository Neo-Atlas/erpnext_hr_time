from dataclasses import dataclass

from hr_time.api.worklog.domain.entities import WorklogEntity


@dataclass
class WorklogAggregate:
    """Aggregate (abstraction) object for our worklog entity"""
    worklog: WorklogEntity

    @property
    def total_allocated(self) -> float:
        return self.worklog.total_allocated

    @property
    def has_allocations(self) -> bool:
        return len(self.worklog.allocations) > 0

    def is_within_tolerance(self, actual_work_hours: float, tolerance_hours: float) -> bool:
        return self.worklog.is_within_tolerance(actual_work_hours, tolerance_hours)

    def adjust_for_tolerance(self, actual_work_hours: float) -> None:
        """Adjust time_saved based on tolerance."""
        self.worklog.time_saved = self.worklog.adjusted_time_saved(actual_work_hours)
