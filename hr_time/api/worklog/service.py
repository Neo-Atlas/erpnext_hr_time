
from datetime import datetime, date, timedelta
import json
from typing import List, Dict, Any, Optional, Tuple
import traceback

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from hr_time.api.worklog.repository import WorklogRepository
from hr_time.api.hr_settings.repository import HRSettingsRepository
from hr_time.api.check_in.service import CheckinService, Action
from hr_time.api.flextime.repository import DurationType
from hr_time.api.worklog.domain.aggregates import WorklogAggregate
from hr_time.api.worklog.domain.entities import WorklogState
from hr_time.api.worklog.domain.task.repository import TaskRepository
from hr_time.api.worklog.domain.task.task_progress_service import TaskProgressService
from hr_time.api.worklog.infrastructure.timesheet.service import TimesheetService
from hr_time.api.worklog.infrastructure.timesheet.values import TimesheetLog
from hr_time.api.worklog.domain.services.session_service import SessionService
from hr_time.api.check_in.enums import LogType
from hr_time.api.employee.api import get_current_employee_id
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

    def before_save(self, worklog_doc):
        """Calculate progress increments and validate before save"""
        self.task_progress_service.calculate_progress_increments_for_worklog(worklog_doc)

        validation = self.validate_worklog_document(worklog_doc)
        if not validation.get("valid"):
            frappe.throw(validation.get("message"))

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

    def prepare_for_checkout(self, employee_id: str) -> Dict[str, Any]:
        """
        Prepare all data needed for checkout worklog dialog
        """
        today = date.today()

        # 1. Get fresh check-in data
        events = self.checkin_service.data.get(today, employee_id)
        durations = events.get_durations()

        # 2. Calculate CURRENT total work time
        current_work_seconds = self._calculate_work_seconds(durations, events)
        current_work_hours = current_work_seconds / 3600

        # 3. Check for existing worklog (returns WorklogEntity or None)
        worklog = self.worklog_repo.get_todays_worklog_entity(employee_id)
        is_new_doc = worklog is None

        # 4. Calculate time components
        if worklog:
            saved_hours = worklog.time_saved
            time_since_last_save = max(0, current_work_hours - saved_hours)
            work_duration = saved_hours
        else:
            saved_hours = 0
            time_since_last_save = 0
            work_duration = 0
            worklog = None  # Ensure worklog is None for new worklogs

        # 5. Determine state
        has_open_session = self._has_open_session(events)
        on_break = self._is_on_break(events)
        is_todays = worklog is not None

        if is_new_doc:
            state = WorklogState.NEW
        elif not is_todays:
            state = WorklogState.HISTORICAL
        elif has_open_session:
            state = WorklogState.WORKING
        elif on_break:
            state = WorklogState.ON_BREAK
        else:
            state = WorklogState.COMPLETED

        # 6. Render headline
        worklog_overview_headline = frappe.render_template(
            "templates/worklog/worklog_overview_headline.html",
            {
                "state": state.value,   # 'working', 'break', 'new', etc.
                "total_hours": round(current_work_hours, 2),
                "saved_hours": round(saved_hours, 2),
                "time_since_last_save": round(time_since_last_save, 2),
                "is_editable": True,
                "_": frappe._
            }
        )

        # 7. Get prefilled tasks
        prefilled_tasks = self._get_prefill_tasks(employee_id)

        # 8. Build response
        response = {
            "time_saved": round(work_duration, 2),
            "time_since_last_save": round(time_since_last_save, 2),
            "time_total_actual": round(current_work_hours, 2),
            "has_open_session": has_open_session,
            "prefilled_tasks": prefilled_tasks,
            "tolerance_minutes": self.hr_settings.get_tolerance_minutes(),
            "worklog_overview_headline": worklog_overview_headline,
            "headline_color": state.display_color(),
        }

        if worklog:
            response.update({
                "existing_worklog_name": worklog.id,
                "existing_tasks": self._tasks_to_dict(worklog.allocations),
                "existing_work_desc": worklog.work_desc,
                "existing_ticket_link": worklog.ticket_link,
                "existing_is_home_office": "Yes" if worklog.is_home_office else "No",
            })

        return response

    def _tasks_to_dict(self, tasks: List) -> List[dict]:
        """Convert TaskAllocation list to dict for API response"""
        return [{
            "task": t.task_id,
            "subject": t.subject,
            "status": t.status,
            "time_spent": t.time_spent,
            "expected_time": t.expected_time,
            "task_desc": t.task_desc,
            "progress_increment": t.progress_increment,
            "priority": t.priority,
        } for t in tasks]

    def _calculate_work_seconds(self, durations: list, events) -> float:
        """Calculate total work seconds from work durations"""
        total = 0.0

        # Sum all work durations
        for duration in durations:
            if duration.duration_type == DurationType.WORK:
                total += duration.total_time

        # Add open session if exists
        if self._has_open_session(events):
            latest = events.get_latest()
            if latest and latest.is_in and not latest.is_break:
                total += (datetime.now() - latest.timestamp).total_seconds()

        return total

    def _has_open_session(self, events) -> bool:
        """Check if employee is currently checked in"""
        latest = events.get_latest()
        return bool(latest and latest.is_in and not latest.is_break)

    def _is_on_break(self, events) -> bool:
        """Check if employee is currently on break"""
        latest = events.get_latest()
        return bool(latest and not latest.is_in and latest.is_break)

    def _serialize_events(self, events: list) -> str:
        """Convert CheckinEvent objects to JSON string"""
        events_data = [{
            "id": e.id,
            "timestamp": e.timestamp.isoformat(),
            "is_in": e.is_in,
            "is_break": e.is_break,
            "log_type": LogType.IN.to_string() if e.is_in else LogType.OUT.to_string()
        } for e in events]

        return json.dumps(events_data, indent=2)

    def _get_prefill_tasks(self, employee_id: str, limit: int = 5) -> List[Dict]:
        """Get tasks to prefill in worklog - used by both full form and dialog"""
        return self.task_repo.get_prefill_tasks(employee_id, limit)

    def validate_worklog_document(self, doc) -> Dict[str, Any]:
        """
        Single source of Validate for worklog document before saving
        """
        # 1. Basic field validation
        if not doc.work_desc or not doc.work_desc.strip():
            return {
                "valid": False,
                "title": _(Messages.Titles.NO_WORK_DESC),
                "message": _(Messages.Worklog.NO_WORK_DESC)
            }

        if not doc.employee:
            return {
                "valid": False,
                "title": _(Messages.Titles.MISSING_EMPLOYEE),
                "message": _(Messages.Worklog.EMPTY_EMPLOYEE)
            }

        if not doc.is_home_office:
            return {
                "valid": False,
                "title": _(Messages.Titles.MISSING_HOME_OFFICE),
                "message": _(Messages.Worklog.NO_HOME_OFFICE)
            }

        if doc.log_time:
            log_time = get_datetime(doc.log_time)
            if log_time > now_datetime():
                return {
                    "valid": False,
                    "title": _(Messages.Titles.INVALID_TIME),
                    "message": _(Messages.Worklog.ERR_CREATE_WORKLOG_FUTURE_TIME)
                }

        # 2. Work time validation:
        # Get actual work hours from frontend (passed via API) if available
        # otherwise calculate from check-in.
        current_total = getattr(doc, '__current_total', None)

        if current_total is None:
            current_total = self._calculate_actual_work_hours(doc.employee)

        # 2. Validate work time recorded:
        if current_total <= 0 and doc.time_saved <= 0:
            return {
                "valid": False,
                "title": _(Messages.Titles.NO_WORK_TIME),
                "message": _(Messages.Worklog.ERR_NO_WORK_TIME)
            }

        # 3. Validate task allocations
        entity = self.worklog_repo._to_entity(doc)
        aggregate = WorklogAggregate(entity)

        if aggregate.total_allocated <= 0:
            return {
                "valid": False,
                "title": _(Messages.Titles.NO_TASK_ALLOCATIONS),
                "message": _(Messages.Worklog.ERR_NO_TASK_ALLOCATIONS)
            }

        # 4. Tolerance validation
        tolerance_minutes = self.hr_settings.get_tolerance_minutes()
        tolerance_hours = tolerance_minutes / 60

        if not aggregate.is_within_tolerance(current_total, tolerance_hours):
            diff = abs(current_total - aggregate.total_allocated)
            if current_total > aggregate.total_allocated:
                message = _(Messages.Worklog.ERR_ALLOCATION_MISMATCH_EXCEEDS).format(
                    round(diff, 2), round(tolerance_hours, 2)
                )
            else:
                message = _(
                    Messages.Worklog.ERR_ALLOCATION_EXCEEDS_WORKED).format(
                        round(diff, 2),
                        round(tolerance_hours, 2)
                )

            return {"valid": False, "title": _(Messages.Titles.ALLOCATION_MISMATCH), "message": message}

        # 5. Adjust time_saved if needed
        aggregate.adjust_for_tolerance(current_total)
        doc.time_saved = aggregate.worklog.time_saved

        return {"valid": True}

    def _calculate_actual_work_hours(self, employee_id: str) -> float:
        """Calculate actual work hours from check-in events"""
        today = date.today()
        events = self.checkin_service.data.get(today, employee_id)
        durations = events.get_durations()
        work_seconds = self._calculate_work_seconds(durations, events)
        return work_seconds / 3600

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

    def save_worklog_and_checkout(
        self,
        worklog_name: Optional[str],
        employee_id: str,
        worklog_data: dict,
        current_total: float
    ) -> Tuple[str, bool]:
        """
        Save worklog and perform checkout if there's an open session.

        Returns:
            Tuple of (saved_worklog_name, checkout_performed)
        """
        # Ensure employee_id is provided for new worklogs
        if not worklog_name and not employee_id:
            employee_id = get_current_employee_id()

        # 1. Save worklog
        saved_name = self.worklog_repo.save_from_dict(
            worklog_name=worklog_name,
            worklog_data=worklog_data,
            current_total=current_total,
            employee_id=employee_id
        )

        # 2. Checkout status capture
        checkout_performed = False
        has_open_session = self.checkin_service.has_open_session(employee_id)

        if has_open_session:
            self.checkin_service.checkin(Action.endOfWork)
            checkout_performed = True

        return saved_name, checkout_performed
