from hr_time.api import logger
from hr_time.api.worklog.domain.task.repository import TaskRepository


class TaskProgressService:
    """
    Domain service for task progress calculations.
    Handles business logic for task progress based on timesheet hours.
    """

    task_repo: TaskRepository

    def __init__(self, task_repo: TaskRepository = None):
        self.task_repo = task_repo or TaskRepository()

    def calculate_progress_increment(self, time_spent: float, expected_time: float) -> float:
        """
        Calculate progress percentage for a single task allocation.

        Args:
            time_spent: Hours spent on the task in this session
            expected_time: Total expected hours for the task

        Returns:
            Progress percentage (0-100)
        """
        if expected_time <= 0:
            return 0.0
        increment = (time_spent / expected_time) * 100
        return round(min(increment, 100), 1)

    def calculate_total_progress_from_timesheets(self, task_name: str) -> float:
        """Calculate total progress percentage from ALL submitted timesheets"""
        total_hours = self.task_repo.get_total_hours_from_timesheets(task_name)
        expected_time = self.task_repo.get_expected_time(task_name)

        if expected_time <= 0:
            return 0.0
        progress = (total_hours / expected_time) * 100
        return min(progress, 100)

    def update_task_progress_from_all_timesheets(self, task_name: str) -> None:
        """Recalculate and update a task's progress based on ALL its timesheets"""
        new_progress = self.calculate_total_progress_from_timesheets(task_name)
        if new_progress <= 0:
            return

        # Get current progress to compare
        task_dict = self.task_repo.get_by_id(task_name)
        if not task_dict:
            return

        current_progress = task_dict.get("progress", 0)

        if abs(new_progress - current_progress) > 0.01:
            self.task_repo.update_progress(task_name, new_progress)
            self.task_repo.add_comment(task_name, f"Progress recalculated: {new_progress:.1f}%")

    def update_worklog_task_progress(self, worklog_doc) -> None:
        """
        Update progress increment for each task in a worklog and recalculate task totals.

        Args:
            worklog_doc: The Worklog document (Frappe doc)
        """
        for task_row in worklog_doc.tasks_entry:
            if not task_row.task or not task_row.time_spent:
                continue

            try:
                self.update_task_progress_from_all_timesheets(task_row.task)

            except Exception as e:
                logger.error(f"Error updating task {task_row.task}: {str(e)}")
                continue

    def calculate_progress_increments_for_worklog(self, worklog_doc):
        """Calculate progress increment for each task row of a given worklog documnt"""
        for row in worklog_doc.tasks_entry:
            if row.task and row.time_spent:
                # Get estimated time if needed
                if not row.expected_time:
                    row.expected_time = self.task_repo.get_expected_time(row.task)

                if row.expected_time and row.expected_time > 0:
                    row.progress_increment = min((row.time_spent / row.expected_time) * 100, 100)
                else:
                    row.progress_increment = 0
