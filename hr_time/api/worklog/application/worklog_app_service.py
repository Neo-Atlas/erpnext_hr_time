"""
Application Service Layer - Orchestrates use cases.
NOTE: pls don't include business rules here - only coordination between domain and infrastructure.
"""
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple

import frappe
from frappe import _

from hr_time.api.worklog.infrastructure.task_progress_updater import TaskProgressUpdater
from hr_time.api.worklog.repository import WorklogRepository
from hr_time.api.worklog.domain.entities import WorklogState
from hr_time.api.worklog.domain.aggregates import WorklogAggregate
from hr_time.api.worklog.domain.services.worklog_state_service import WorklogStateService
from hr_time.api.worklog.infrastructure.timesheet.service import TimesheetService
from hr_time.api.worklog.domain.task.repository import TaskRepository
from hr_time.api.worklog.domain.task.task_progress_service import TaskProgressService
from hr_time.api.hr_settings.repository import HRSettingsRepository
from hr_time.api.check_in.service import CheckinService, Action
from hr_time.api.flextime.repository import DurationType
from hr_time.api.employee.api import get_current_employee_id
from hr_time.api.shared.constants.messages import Messages


class WorklogAppService:
    """
    Application Service for Worklog use cases.

    Responsibilities:
    - Orchestrate use cases (prepare, save, validate, context)
    - Coordinate repositories and domain services
    - Manage transactions
    """

    def __init__(
        self,
        worklog_repo: WorklogRepository = None,
        hr_settings: HRSettingsRepository = None,
        task_repo: TaskRepository = None,
        task_progress_service: TaskProgressService = None,
        timesheet_service: TimesheetService = None,
        checkin_service: CheckinService = None,
        state_service: WorklogStateService = None
    ):
        self.worklog_repo = worklog_repo or WorklogRepository()
        self.hr_settings = hr_settings or HRSettingsRepository()
        self.task_repo = task_repo or TaskRepository()
        self.task_progress_service = task_progress_service or TaskProgressService()
        self.timesheet_service = timesheet_service or TimesheetService()
        self.checkin_service = checkin_service or CheckinService.prod()
        self.state_service = state_service or WorklogStateService()

    # ============ USE CASE: Get worklog context ============

    def get_worklog_context(
        self,
        employee_id: str,
        referred_worklog_name: Optional[str] = None,
        is_dialog_call: bool = False
    ) -> Dict[str, Any]:
        """
        Get worklog context for UI.

        Orchestrates:
        1. Fetch today's worklog
        2. Get check-in events
        3. Determine state (via domain service)
        4. Calculate editability
        5. Return DTO for rendering
        """
        today = date.today()

        # 1. Fetch data (infrastructure)
        today_worklog = self.worklog_repo.get_todays_worklog_entity(employee_id)
        today_worklog_name = today_worklog.id if today_worklog else None

        events = self.checkin_service.data.get(today, employee_id)
        latest = events.get_latest()

        has_open_session = bool(latest and latest.is_in and not latest.is_break)
        on_break = bool(not has_open_session and latest and not latest.is_in and latest.is_break)

        # 2. Determine worklog type (domain rules)
        is_todays, is_new_doc = self._determine_worklog_type(
            referred_worklog_name, today_worklog_name, is_dialog_call
        )

        # 3. Determine state (domain service)
        state = self.state_service.determine_state(
            is_new_doc=is_new_doc,
            is_todays=is_todays,
            has_open_session=has_open_session,
            on_break=on_break
        )

        # 4. Calculate editability (domain service)
        is_editable = self.state_service.is_editable(state, is_new_doc, is_todays)

        # 5. Get worklog hours if exists
        worklog_total_hours = self._get_worklog_total_hours(referred_worklog_name, is_new_doc)

        return {
            "state": state,
            "is_todays": is_todays,
            "is_new_doc": is_new_doc,
            "is_editable": is_editable,
            "has_open_session": has_open_session,
            "on_break": on_break,
            "today_worklog_name": today_worklog_name,
            "worklog_total_hours": worklog_total_hours,
            "tolerance_minutes": self.hr_settings.get_tolerance_minutes(),
        }

    def _determine_worklog_type(self, referred_name, today_name, is_dialog_call):
        """Pure logic - could move to domain service if reused"""
        if is_dialog_call:
            return bool(today_name), not bool(today_name)

        is_todays = referred_name and today_name and today_name == referred_name
        is_new_doc = not referred_name or referred_name.startswith(('new-', 'New '))
        return is_todays, is_new_doc

    def _get_worklog_total_hours(self, worklog_name: Optional[str], is_new_doc: bool) -> float:
        """Get total hours from existing worklog"""
        if not worklog_name or is_new_doc:
            return 0.0
        doc = frappe.get_doc(WorklogRepository.DOCTYPE_NAME, worklog_name)
        return float(doc.time_saved or 0)

    # ============ USE CASE: Prepare for checkout ============

    def prepare_for_checkout(self, employee_id: str) -> Dict[str, Any]:
        """
        Prepare all data needed for checkout dialog.

        Orchestrates:
        1. Get check-in events and calculate work time
        2. Get today's worklog if exists
        3. Determine state
        4. Get prefilled tasks
        5. Return DTO
        """
        today = date.today()

        # 1. Get check-in data
        events = self.checkin_service.data.get(today, employee_id)
        durations = events.get_durations()

        current_work_seconds = self._calculate_work_seconds(durations, events)
        current_work_hours = current_work_seconds / 3600

        # 2. Get existing worklog
        todays_worklog = self.worklog_repo.get_todays_worklog_entity(employee_id)
        is_new_doc = todays_worklog is None

        # 3. Calculate time components
        if todays_worklog:
            saved_hours = todays_worklog.time_saved
            time_since_last_save = max(0, current_work_hours - saved_hours)
            work_duration = saved_hours
        else:
            saved_hours = 0
            time_since_last_save = 0
            work_duration = 0

        # 4. Determine state
        has_open_session = self._has_open_session(events)
        on_break = self._is_on_break(events)
        is_todays = todays_worklog is not None

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

        # 5. Render overview headline
        worklog_overview_headline = frappe.render_template(
            "templates/worklog/worklog_overview_headline.html",
            {
                "state": state.value,
                "total_hours": round(current_work_hours, 2),
                "saved_hours": round(saved_hours, 2),
                "time_since_last_save": round(time_since_last_save, 2),
                "is_editable": True,
                "_": frappe._
            }
        )

        # 5. Build response
        response = {
            "time_saved": round(work_duration, 2),
            "time_since_last_save": round(time_since_last_save, 2),
            "time_total_actual": round(current_work_hours, 2),
            "has_open_session": has_open_session,
            "prefilled_tasks": self.task_repo.get_prefill_tasks(employee_id, 5),
            "tolerance_minutes": self.hr_settings.get_tolerance_minutes(),
            "headline_color": state.display_color(),
            "worklog_overview_headline": worklog_overview_headline,
        }

        if todays_worklog:
            response.update({
                "existing_worklog_name": todays_worklog.id,
                "existing_tasks": self._tasks_to_dict(todays_worklog.allocations),
                "existing_work_desc": todays_worklog.work_desc,
                "existing_ticket_link": todays_worklog.ticket_link,
                "existing_is_home_office": "Yes" if todays_worklog.is_home_office else "No",
            })

        return response

    def _calculate_work_seconds(self, durations, events) -> float:
        """Calculate total work seconds from durations and open session"""
        total = sum(d.total_time for d in durations if d.duration_type == DurationType.WORK)

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

    # ============ USE CASE: Save and checkout ============

    def save_and_checkout(
        self,
        worklog_name: Optional[str],
        employee_id: str,
        worklog_data: dict,
        current_total: float
    ) -> Tuple[str, bool]:
        """
        Save worklog and perform checkout.

        Orchestrates:
        1. Save worklog document
        2. Checkout if session open
        3. Return result
        """
        # Ensure employee_id
        if not worklog_name and not employee_id:
            employee_id = get_current_employee_id()

        # 1. Save worklog
        saved_name = self.worklog_repo.save_from_dict(
            worklog_name=worklog_name,
            worklog_data=worklog_data,
            current_total=current_total,
            employee_id=employee_id
        )

        # 2. Checkout if session open
        checkout_performed = False
        if self.checkin_service.has_open_session(employee_id):
            self.checkin_service.checkin(Action.END_WORK)
            checkout_performed = True

        return saved_name, checkout_performed

    # ============ USE CASE: Validate worklog ============

    def before_save_worklog(self, doc):
        """Orchestrate pre-save operations"""
        # 1. Calculate progress increments
        updater = TaskProgressUpdater()
        updater.calculate_progress_increments_for_worklog(doc)

        # 2. Validate the document
        app = WorklogAppService()
        validation = app.validate_worklog_document(doc)
        if not validation.get("valid"):
            frappe.throw(validation.get("message"))

    def validate_worklog_document(self, doc) -> Dict[str, Any]:
        """
        Validate worklog document before save.

        Delegates business rules to domain layer.
        """
        # 1. Basic field validation
        if not doc.work_desc or not doc.work_desc.strip():
            return {"valid": False, "message": _(Messages.Worklog.NO_WORK_DESC)}

        if not doc.employee:
            return {"valid": False, "message": _(Messages.Worklog.EMPTY_EMPLOYEE)}

        if not doc.is_home_office:
            return {"valid": False, "message": _(Messages.Worklog.NO_HOME_OFFICE)}

        # 2. Work time validation
        current_total = getattr(doc, '__current_total', None)
        if current_total is None:
            current_total = self._calculate_actual_work_hours(doc.employee)

        if current_total <= 0 and doc.time_saved <= 0:
            return {"valid": False, "message": _(Messages.Worklog.ERR_NO_WORK_TIME)}

        # 3. Domain validation via aggregate
        entity = self.worklog_repo._to_entity(doc)
        aggregate = WorklogAggregate(entity)

        if aggregate.total_allocated <= 0:
            return {"valid": False, "message": _(Messages.Worklog.ERR_NO_TASK_ALLOCATIONS)}

        # 4. Tolerance validation (domain rule)
        tolerance_minutes = self.hr_settings.get_tolerance_minutes()
        tolerance_hours = tolerance_minutes / 60

        if not aggregate.is_within_tolerance(current_total, tolerance_hours):
            diff = abs(current_total - aggregate.total_allocated)
            if current_total > aggregate.total_allocated:
                message = _(Messages.Worklog.ERR_ALLOCATION_MISMATCH_EXCEEDS).format(
                    round(diff, 2), round(tolerance_hours, 2)
                )
            else:
                message = _(Messages.Worklog.ERR_ALLOCATION_EXCEEDS_WORKED).format(
                    round(diff, 2), round(tolerance_hours, 2)
                )
            return {"valid": False, "message": message}

        # 5. Adjust time_saved (domain rule)
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
