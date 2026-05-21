import datetime
import enum

import frappe

from hr_time.api.check_in.event import CheckinEvent
from hr_time.api.check_in.repository import CheckinRepository
from hr_time.api.employee.repository import EmployeeRepository
from hr_time.api.check_in.enums import LogType, Action, State
from hr_time.api.flextime.stats import FlextimeStatisticsService


class CheckinStatus:
    """Aggregate check-in status (state + break history)"""
    # Current checkin state
    state: State

    # True if at least one break event exists today
    had_break: bool

    def __init__(self, state: State, had_break: bool):
        self.state = state
        self.had_break = had_break

    def to_dict(self) -> dict:
        """Convert to API response"""
        return {
            "status": self.state.value,
            "had_break": self.had_break
        }


class CheckinService:
    employee: EmployeeRepository
    data: CheckinRepository

    def __init__(self, employee: EmployeeRepository, data: CheckinRepository):
        super().__init__()
        self.employee = employee
        self.data = data

    @staticmethod
    def prod():
        return CheckinService(EmployeeRepository(), CheckinRepository())

    def get_current_status(self) -> CheckinStatus:
        """Get current IN/OUT/BREAK state"""
        employee = self.employee.get_current()

        if employee is None:
            return CheckinStatus(State.UNKNOWN, False)

        events = self.data.get(datetime.date.today(), employee.id)
        state = self._event_to_state(events.get_latest())
        had_break = events.has_break()

        return CheckinStatus(state, had_break)

    def checkin(self, action: Action):
        """Checks in the current employee based on the given action i.e. executes checkin/out/break"""
        employee = self.employee.get_current()

        if employee is None:
            raise RuntimeError("Current employee not found")

        if action == Action.START_WORK or action == Action.RESUME_WORK:
            self.data.checkin(employee.id, LogType.IN, False)
            status_str = "IN"
        elif action == Action.BREAK:
            self.data.checkin(employee.id, LogType.OUT, True)
            status_str = "BREAK"
        elif action == Action.END_WORK:
            self.data.checkin(employee.id, LogType.OUT, False)
            status_str = "OUT"
        else:
            raise ValueError(f"Invalid action: {action}")

        # Get totals for the emitting event
        stats = FlextimeStatisticsService.prod()
        total_worked_seconds = stats.get_todays_worked_seconds(employee.id)
        total_break_seconds = stats.get_todays_break_seconds(employee.id)

        # Emit realtime event for this specific user
        frappe.publish_realtime(
            event="checkin_status_updated",
            message={
                "employee_id": employee.id,
                "status": status_str,  # "IN"/"BREAK"/"OUT"
                "total_worked_seconds": total_worked_seconds,
                "total_break_seconds": total_break_seconds,
                "timestamp": frappe.utils.now_datetime().isoformat()
            },
            # user=frappe.session.user,  # Only send to the user making the checkin request
            #   -> (broadvasting for now since we also want admins to receive the event, can optimize later if needed)
            after_commit=True  # Ensure event fires after DB commit
        )

    @staticmethod
    def _event_to_state(event: CheckinEvent) -> State:
        """Convert checkin event to IN/OUT/BREAK state"""
        if event is None:
            return State.OUT
        if (not event.is_in) and event.is_break:
            return State.BREAK
        if not event.is_in:
            return State.OUT
        return State.IN

    def has_open_session(self, employee_id: str) -> bool:
        """Check if employee has open check-in session"""
        events = self.data.get(datetime.date.today(), employee_id)
        latest = events.get_latest()

        # True only if:
        # 1. There is a latest event AND
        # 2. It's an IN event (checked in) AND
        # 3. It's NOT a break
        return bool(latest and latest.is_in and not latest.is_break)

    def get_available_actions(self) -> dict:
        """Get available check-in actions based on current state"""
        status = self.get_current_status()
        state = status.state
        had_break = status.had_break

        if state == State.IN:
            options = [Action.BREAK.value, Action.END_WORK.value]
            default = Action.END_WORK.value if had_break else Action.BREAK.value
        elif state == State.OUT:
            options = [Action.START_WORK.value]
            default = Action.START_WORK.value
        elif state == State.BREAK:
            options = [Action.RESUME_WORK.value]
            default = Action.RESUME_WORK.value
        else:
            options = [Action.START_WORK.value, Action.BREAK.value, Action.RESUME_WORK.value, Action.END_WORK.value]
            default = ""

        return {
            "options": options,
            "default": default
        }
