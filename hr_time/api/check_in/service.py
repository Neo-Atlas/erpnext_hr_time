import datetime
import enum

from hr_time.api.check_in.event import CheckinEvent
from hr_time.api.check_in.repository import CheckinRepository
from hr_time.api.employee.repository import EmployeeRepository


class State(enum.Enum):
    Unknown = 1
    In = 2
    Break = 3
    Out = 4


class CheckinStatus:
    # Current checkin state
    state: State

    # True if at least one break event exists today
    had_break: bool

    def __init__(self, state: State, had_break: bool):
        super().__init__()

        self.state = state
        self.had_break = had_break


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

    @staticmethod
    def _event_to_state(event: CheckinEvent) -> State:
        if event is None:
            return State.Out

        if (not event.is_in) and event.is_brake:
            return State.Break

        if not event.is_in:
            return State.Out

        return State.In
