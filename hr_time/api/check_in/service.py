import datetime
import enum

import frappe

from hr_time.api.check_in.event import CheckinEvent
from hr_time.api.check_in.repository import CheckinRepository
from hr_time.api.employee.repository import EmployeeRepository
from hr_time.api.check_in.enums import LogType


class State(enum.Enum):
    Unknown = 1
    In = 2
    Break = 3
    Out = 4

    # Renders status to checkin status template parameters
    def render(self) -> dict:
        match self:
            case State.In:
                label = "Checked in"
                status = "work"
                icon = "check"
            case State.Out:
                label = "Checked out"
                status = "out"
                icon = "remove"
            case State.Break:
                label = "Break"
                status = "break"
                icon = "coffee"
            case _:
                label = "Unknown"
                status = "out"
                icon = "question"

        return {
            "label": frappe._(label),
            "status": status,
            "icon": icon
        }


class CheckinStatus:
    # Current checkin state
    state: State

    # True if at least one break event exists today
    had_break: bool

    def __init__(self, state: State, had_break: bool):
        super().__init__()

        self.state = state
        self.had_break = had_break


class Action(enum.Enum):
    startOfWork = 1,
    breakTime = 2,
    endOfWork = 3


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
            return CheckinStatus(State.Unknown, False)

        events = self.data.get(datetime.date.today(), employee.id)
        state = self._event_to_state(events.get_latest())
        had_break = events.has_break()

        return CheckinStatus(state, had_break)

    def checkin(self, action: Action):
        """Checks in the current employee based on the given action i.e. executes checkin/out/break"""
        employee = self.employee.get_current()

        if employee is None:
            raise RuntimeError("Current employee not found")

        match action:
            case Action.startOfWork:
                self.data.checkin(employee.id, LogType.IN, False)
            case Action.breakTime:
                self.data.checkin(employee.id, LogType.OUT, True)
            case Action.endOfWork:
                self.data.checkin(employee.id, LogType.OUT, False)

    @staticmethod
    def _event_to_state(event: CheckinEvent) -> State:
        """Convert checkin event to IN/OUT/BREAK state"""
        if event is None:
            return State.Out

        if (not event.is_in) and event.is_break:
            return State.Break

        if not event.is_in:
            return State.Out

        return State.In

    def has_open_session(self, employee_id: str) -> bool:
        """Check if employee has open check-in session"""
        events = self.data.get(datetime.date.today(), employee_id)
        latest = events.get_latest()

        # True only if:
        # 1. There is a latest event AND
        # 2. It's an IN event (checked in) AND
        # 3. It's NOT a break
        return bool(latest and latest.is_in and not latest.is_break)
