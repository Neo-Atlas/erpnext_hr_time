import datetime
import enum

import frappe

from hr_time.api.check_in.event import CheckinEvent
from hr_time.api.check_in.repository import CheckinRepository
from hr_time.api.employee.repository import EmployeeRepository


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
        employee = self.employee.get_current()

        if employee is None:
            return CheckinStatus(State.Unknown, False)

        events = self.data.get(datetime.date.today(), employee.id)
        state = self._event_to_state(events.get_latest())
        had_break = events.has_break()

        return CheckinStatus(state, had_break)

    # Checks in the current employee based on the given action
    def checkin(self, action: Action):
        employee = self.employee.get_current()

        if employee is None:
            raise RuntimeError("Current employee not found")

        match action:
            case Action.startOfWork:
                self.data.checkin(employee.id, "IN", False)
            case Action.breakTime:
                self.data.checkin(employee.id, "OUT", True)
            case Action.endOfWork:
                self.data.checkin(employee.id, "OUT", False)

    @staticmethod
    def _event_to_state(event: CheckinEvent) -> State:
        if event is None:
            return State.Out

        if (not event.is_in) and event.is_break:
            return State.Break

        if not event.is_in:
            return State.Out

        return State.In
