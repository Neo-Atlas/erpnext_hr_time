"""
Infrastructure service for task progress persistence.
Handles database operations and Frappe-specific logic.
"""
from hr_time.api import logger
from hr_time.api.worklog.domain.task.repository import TaskRepository
from hr_time.api.worklog.domain.task_progress_calculator import TaskProgressCalculator


class TaskProgressUpdater:
    """
    Infrastructure service for updating task progress in the database.

    Responsibilities:
    - Fetch task data from repository
    - Calculate progress using domain calculator
    - Persist updates to database
    - Add audit comments
    """

    def __init__(self, task_repo: TaskRepository = None):
        self.task_repo = task_repo or TaskRepository()
        self.calculator = TaskProgressCalculator()

    def update_task_progress_from_timesheets(self, task_name: str) -> None:
        """
        Recalculate and update a task's progress based on ALL its timesheets.

        Args:
            task_name: The task ID to update
        """
        # Get data from repository
        total_hours = self.task_repo.get_total_hours_from_timesheets(task_name)
        expected_time = self.task_repo.get_expected_time(task_name)

        # Calculate new progress (pure domain)
        new_progress = self.calculator.calculate_total_progress(total_hours, expected_time)

        if new_progress <= 0:
            return

        # Get current progress
        task_dict = self.task_repo.get_by_id(task_name)
        if not task_dict:
            return

        current_progress = task_dict.get("progress", 0)

        # Check if update is needed (pure domain)
        if self.calculator.should_update_progress(current_progress, new_progress):
            self.task_repo.update_progress(task_name, new_progress)
            self.task_repo.add_comment(task_name, f"Progress recalculated: {new_progress:.1f}%")
            logger.info(f"Task {task_name} progress updated from {current_progress}% to {new_progress}%")

    def update_worklog_task_progress(self, worklog_doc) -> None:
        """
        Update progress for each task in a worklog.

        Args:
            worklog_doc: The Worklog document (Frappe doc)
        """
        for task_row in worklog_doc.tasks_entry:
            if not task_row.task or not task_row.time_spent:
                continue

            try:
                self.update_task_progress_from_timesheets(task_row.task)
            except Exception as e:
                logger.error(f"Error updating task {task_row.task}: {str(e)}")
                continue

    def calculate_and_set_row_progress(self, row) -> None:
        """
        Calculate progress increment for a single worklog task row and set it.

        Args:
            row: The task row in a worklog (Frappe child doc)
        """
        if not row.task or not row.time_spent:
            row.progress_increment = 0
            return

        # Get expected time if not already set
        if not row.expected_time:
            row.expected_time = self.task_repo.get_expected_time(row.task)

        # Calculate using pure domain logic
        row.progress_increment = self.calculator.calculate_row_progress_increment(
            row.time_spent,
            row.expected_time
        )

    def calculate_progress_increments_for_worklog(self, worklog_doc) -> None:
        """
        Calculate progress increment for each task row of a given worklog document.

        Args:
            worklog_doc: The Worklog document (Frappe doc)
        """
        for row in worklog_doc.tasks_entry:
            self.calculate_and_set_row_progress(row)
