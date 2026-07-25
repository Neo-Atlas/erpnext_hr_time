
from datetime import datetime, date, timedelta
import traceback

import frappe
from frappe import _

from hr_time.api.worklog.repository import WorklogRepository
from hr_time.api.hr_settings.repository import HRSettingsRepository
from hr_time.api.check_in.service import CheckinService
from hr_time.api.worklog.domain.task.repository import TaskRepository
from hr_time.api.worklog.domain.task.task_progress_service import TaskProgressService
from hr_time.api.worklog.infrastructure.timesheet.service import TimesheetService
from hr_time.api.worklog.infrastructure.timesheet.values import TimesheetLog
from hr_time.api.worklog.infrastructure.services.session_service import SessionService
from hr_time.api.shared.constants.messages import Messages
from hr_time.api.shared.utils.frappe_utils import FrappeUtils


class WorklogService:
    """
    Service layer for managing operations related to employee worklogs.
    Provides methods to check for existing worklogs and to create new worklogs using the WorklogRepository.
    """
    worklog_repo: WorklogRepository
    hr_settings: HRSettingsRepository
    task_repo: TaskRepository
    task_progress_service: TaskProgressService
    timesheet_service: TimesheetService
    session_service: SessionService
    checkin_service: CheckinService

    def __init__(
        self,
        worklog_repo: WorklogRepository,
        hr_settings: HRSettingsRepository,
        task_repo: TaskRepository,
        task_progress_service: TaskProgressService,
        timesheet_service: TimesheetService,
        session_service: SessionService,
        checkin_service: CheckinService
    ):
        """
        Initializes the WorklogService with a given WorklogRepository.

        Args:
            worklog_repo (WorklogRepository): Repository for worklog operations.
        """
        super().__init__()
        self.worklog_repo = worklog_repo
        self.hr_settings = hr_settings
        self.task_repo = task_repo
        self.task_progress_service = task_progress_service
        self.timesheet_service = timesheet_service
        self.session_service = session_service
        self.checkin_service = checkin_service

    @staticmethod
    def prod() -> 'WorklogService':
        """
        Creates a production instance of WorklogService with a default WorklogRepository.

        Returns:
            WorklogService: An initialized WorklogService instance for production use.
        """
        worklog_repo = WorklogRepository()
        hr_settings = HRSettingsRepository()
        task_repo = TaskRepository()
        task_progress_service = TaskProgressService(task_repo=task_repo)
        timesheet_service = TimesheetService(task_progress_service=task_progress_service)
        session_service = SessionService()
        checkin_service = CheckinService.prod()

        return WorklogService(
            worklog_repo,
            hr_settings,
            task_repo,
            task_progress_service,
            timesheet_service,
            session_service,
            checkin_service,
        )

    def check_if_employee_has_worklogs_today(self, employee_id) -> bool:
        """
        Checks if the specified employee has created any worklogs today.

        Args:
            employee_id (str): The ID of the employee whose worklogs are being checked.

        Returns:
            bool: True if the employee has worklogs for the current day, False otherwise.
        """
        today = date.today()
        worklogs = self.worklog_repo.get_worklogs_of_employee_on_date(employee_id, today)
        return len(worklogs) > 0

    def process_worklog_save(self, worklog_doc, timesheet_name=None):
        """Process worklog after save - creates/cancels timesheet AND updates task progress"""
        try:
            # If timesheet_name not provided, look up existing timesheet for today
            if timesheet_name is None:
                employee_id = worklog_doc.employee
                timesheet_name = self.timesheet_service.get_todays_timesheet(employee_id)

            timesheet = None

            # Convert log_time to datetime if it's a string
            if isinstance(worklog_doc.log_time, str):
                log_datetime = datetime.strptime(worklog_doc.log_time, '%Y-%m-%d %H:%M:%S.%f')
            else:
                log_datetime = worklog_doc.log_time

            date_to_use = log_datetime.date()

            # Get session times fresh from check-in
            session_start, _ = self.session_service.get_session_times(
                worklog_doc.employee,
                date_to_use
            )

            if not session_start:
                session_start = log_datetime
                # session_end = log_datetime

            # Get configuration
            activity_type = self.hr_settings.get_default_activity_type()
            buffer_task_id = self.hr_settings.get_buffer_task()

            # 1. Handle timesheet
            if not timesheet_name:
                # Create new timesheet with distributed times
                timesheet = self._create_timesheet_from_worklog(
                    worklog_doc, session_start, activity_type, buffer_task_id
                )
            else:
                # Replace existing timesheet
                timesheet = self._replace_old_timesheet_of_worklog(
                    worklog_doc, timesheet_name, session_start, activity_type, buffer_task_id
                )

            # update the linked timesheet in the worklog document if present
            if timesheet:
                worklog_doc.db_set("timesheet", timesheet.name)

            # 2. ALWAYS update task progress (regardless of timesheet)
            self.task_progress_service.update_worklog_task_progress(worklog_doc)

            if timesheet:
                FrappeUtils.success_modal(
                    Messages.Timesheet.SUCCESS_TIMESHEET_PROCESSED, title=Messages.Worklog.SUCCESS_SAVED
                )

            return timesheet or True

        except Exception as e:
            frappe.log_error(f"Worklog processing failed: {str(e)}")
            traceback.print_exc()
            return None

    def _create_timesheet_from_worklog(self, worklog_doc, session_start, activity_type, buffer_task_id):
        """Create Timesheet document with distributed time entries"""

        if not worklog_doc.tasks_entry:
            return None

        # Check if there are any actual time allocations
        has_allocations = any(t.time_spent > 0 for t in worklog_doc.tasks_entry)
        if not has_allocations:
            return None

        try:
            # building Time logs
            time_logs = self._build_time_logs_from_worklog(worklog_doc, session_start, activity_type, buffer_task_id)

            return self.timesheet_service.create_from_worklog(
                worklog_doc.employee, time_logs)

        except Exception as e:
            traceback.print_exc()
            return None

    def _replace_old_timesheet_of_worklog(
        self, worklog_doc, timesheet_name, session_start, activity_type, buffer_task_id
    ):
        """Cancels old timesheet and create fresh one"""
        if not timesheet_name:
            return self._create_timesheet_from_worklog(worklog_doc)
        try:
            time_logs = self._build_time_logs_from_worklog(
                worklog_doc, session_start, activity_type, buffer_task_id
            )

            if not time_logs:
                return None

            # Delegate to TimesheetService for cancel and replace
            return self.timesheet_service.cancel_and_replace(
                employee_id=worklog_doc.employee,
                old_timesheet_name=timesheet_name,
                time_logs=time_logs
            )

        except Exception as e:
            traceback.print_exc()
            return None

    def _build_time_logs_from_worklog(self, worklog_doc, session_start, activity_type, buffer_task_id):
        """Build time logs from worklog document (shared logic)"""
        time_logs = []
        current_total = worklog_doc.time_saved
        total_allocated = sum(float(t.time_spent or 0) for t in worklog_doc.tasks_entry)
        time_unallocated = current_total - total_allocated

        # Add allocated tasks
        task_start_time = session_start
        for task_row in worklog_doc.tasks_entry:
            if task_row.task and task_row.time_spent > 0:
                task_end = task_start_time + timedelta(hours=float(task_row.time_spent))

                log = TimesheetLog(
                    activity_type=activity_type,
                    task_id=task_row.task,
                    hours=float(task_row.time_spent),
                    from_time=task_start_time,
                    to_time=task_end,
                    description=task_row.task_desc or task_row.subject,
                    completed=True,
                    is_billable=True,
                )
                time_logs.append(log)
                task_start_time = task_end

        # Add unallocated time if any
        if time_unallocated > 0.01 and buffer_task_id:
            task_end_time = task_start_time + timedelta(hours=float(time_unallocated))

            log = TimesheetLog(
                activity_type=activity_type,
                task_id=buffer_task_id,
                hours=float(time_unallocated),
                from_time=task_start_time,
                to_time=task_end_time,
                description=Messages.Timesheet.DEFAULT_UNALLOCATED_DESCRIPTION,
                completed=False,
                is_billable=True,
            )

            time_logs.append(log)

        return time_logs

    def calculate_task_progress_increments(self, worklog_doc):
        """Wrapper that calculates progress increment for each task row in a worklog"""
        self.task_progress_service.calculate_progress_increments_for_worklog(worklog_doc)
