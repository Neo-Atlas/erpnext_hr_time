from dataclasses import dataclass

from hr_time.api.worklog.domain.entities import WorklogEntity

_EPSILON = 0.0001  # 0.36 seconds — absorbs floating-point drift in hour calculations


@dataclass
class WorklogAggregate:
    """Aggregate root for Worklog — owns tolerance and time-adjustment invariants."""
    worklog: WorklogEntity

    @property
    def total_allocated(self) -> float:
        return self.worklog.total_allocated

    @property
    def has_allocations(self) -> bool:
        return len(self.worklog.allocations) > 0

    def is_within_tolerance(self, actual_work_hours: float, tolerance_hours: float) -> bool:
        diff = abs(actual_work_hours - self.total_allocated)
        return diff <= tolerance_hours + _EPSILON

    def adjust_for_tolerance(self, actual_work_hours: float) -> None:
        """Set time_saved: stretch to allocation if over-allocated, else keep actual hours."""
        if self.total_allocated > actual_work_hours:
            self.worklog.time_saved = self.total_allocated
        else:
            self.worklog.time_saved = actual_work_hours
