from typing import Optional, List

from frappe import _

from hr_time.api.worklog.domain.task.task_progress_service import TaskProgressService
from hr_time.api.worklog.infrastructure.timesheet.repository import TimesheetRepository
from hr_time.api.worklog.infrastructure.timesheet.values import TimesheetLog


class TimesheetService:
    """
    Infrastructure service for Timesheet operations.
    Handles creation, cancellation, and submission of Timesheet documents.
    """

    timesheet_repo: TimesheetRepository
    task_progress_service: TaskProgressService

    def __init__(self, timesheet_repo: TimesheetRepository = None, task_progress_service: TaskProgressService = None):
        self.timesheet_repo = timesheet_repo or TimesheetRepository()
        self.task_progress_service = task_progress_service or TaskProgressService()

    def get_todays_timesheet(self, employee_id: str) -> Optional[str]:
        """Get today's timesheet name for an employee"""
        return self.timesheet_repo.get_todays_timesheet(employee_id)

    def cancel_timesheet(self, timesheet_name: str) -> bool:
        """Cancel a timesheet by name"""
        return self.timesheet_repo.cancel(timesheet_name)

    def create_from_worklog(
        self,
        employee_id: str,
        time_logs: List[TimesheetLog],
    ):
        """
        Create and submit a timesheet from pre-built time logs.

        Args:
            employee_id: Employee ID
            time_logs: List of TimesheetLog value objects
            buffer_task_id: Buffer task ID for unallocated time (not needed here, already in logs)

        Returns:
            Submitted Timesheet document
        """
        if not time_logs:
            return None

        return self.timesheet_repo.create(employee_id, time_logs)

    def cancel_and_replace(
        self,
        employee_id: str,
        old_timesheet_name: str,
        time_logs: List[TimesheetLog],
    ):
        """
        Cancel old timesheet and create a new one.

        Args:
            employee_id: Employee ID
            old_timesheet_name: Name of the timesheet to cancel
            time_logs: List of TimesheetLog value objects for the new timesheet
        """

        # Cancel old timesheet
        self.timesheet_repo.cancel(old_timesheet_name)

        # Create new timesheet with pre-built logs
        return self.create_from_worklog(employee_id, time_logs)
