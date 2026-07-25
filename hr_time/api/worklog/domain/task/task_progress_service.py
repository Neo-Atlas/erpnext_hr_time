import warnings

from hr_time.api.worklog.domain.task.repository import TaskRepository
from hr_time.api.worklog.domain.task_progress_calculator import TaskProgressCalculator
from hr_time.api.worklog.infrastructure.task_progress_updater import TaskProgressUpdater


class TaskProgressService:
    """
    @deprecated: Use TaskProgressCalculator + TaskProgressUpdater instead.
    (This class is kept for backward compatibility.)

    Thin Domain wrapper service for task progress calculations.
    Handles business logic for task progress based on timesheet hours.
    """

    task_repo: TaskRepository
    _calculator: TaskProgressCalculator
    _updater: TaskProgressUpdater

    def __init__(self, task_repo: TaskRepository = None):
        warnings.warn(
            "TaskProgressService is deprecated. Use TaskProgressCalculator for calculations "
            "and TaskProgressUpdater for persistence.",
            DeprecationWarning,
            stacklevel=2
        )
        self.task_repo = task_repo or TaskRepository()
        self._calculator = TaskProgressCalculator()
        self._updater = TaskProgressUpdater(self.task_repo)

    def calculate_progress_increment(self, time_spent: float, expected_time: float) -> float:
        """
        Calculate progress percentage for a single task allocation.

        Args:
            time_spent: time spent (hrs) for the task
            expected_time: expected time (hrs) for completion of the task

        Deprecated: Use TaskProgressCalculator.calculate_progress_increment()
        """
        return self._calculator.calculate_progress_increment(time_spent, expected_time)

    def calculate_total_progress_from_timesheets(self, task_name: str) -> float:
        """
        Calculate total progress percentage from ALL submitted timesheets
        Args:
            task_name: The name (task id) of the task document

        Deprecated: Use TaskProgressCalculator.calculate_total_progress()
        """
        total_hours = self.task_repo.get_total_hours_from_timesheets(task_name)
        expected_time = self.task_repo.get_expected_time(task_name)
        return self._calculator.calculate_total_progress(total_hours, expected_time)

    def update_task_progress_from_all_timesheets(self, task_name: str) -> None:
        """
        Recalculate and update a task's progress based on ALL its timesheets
        Args:
            task_name: The name (task id) of the task document

        Deprecated: Use TaskProgressUpdater.update_task_progress_from_timesheets()
        """
        self._updater.update_task_progress_from_timesheets(task_name)

    def update_worklog_task_progress(self, worklog_doc) -> None:
        """
        Update progress increment for each task in a worklog and recalculate task totals.
        Deprecated: Use TaskProgressUpdater.update_worklog_task_progress()

        Args:
            worklog_doc: The Worklog document (Frappe doc)
        """
        self._updater.update_worklog_task_progress(worklog_doc)

    def calculate_progress_increments_for_worklog(self, worklog_doc):
        """
        Calculate progress increment for each task row of a given worklog documnt
        Deprecated: Use TaskProgressUpdater.calculate_progress_increments_for_worklog()
        """
        self._updater.calculate_progress_increments_for_worklog(worklog_doc)
