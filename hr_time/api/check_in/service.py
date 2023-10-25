import datetime
import enum

from hr_time.api.check_in.repository import CheckinRepository
from hr_time.api.employee.repository import EmployeeRepository


class CheckinStatus(enum.Enum):
    Unknown = 1
    In = 2
    Break = 3
    Out = 4


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
            return CheckinStatus.Unknown

        event = self.data.get(datetime.date.today(), employee.id).get_latest()

        if event is None:
            return CheckinStatus.Out

        if (not event.is_in) and event.is_brake:
            return CheckinStatus.Break

        if not event.is_in:
            return CheckinStatus.Out

        return CheckinStatus.In
