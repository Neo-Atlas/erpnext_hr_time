import datetime

import frappe

from hr_time.api.check_in.repository import CheckinRepository
from hr_time.api.check_in.service import State
from hr_time.api.employee.repository import EmployeeRepository, Employee, TimeModel


class PresentEmployee:
    employee: Employee
    status: State
    current_status_since: datetime.time
    work_start_today: datetime.time

    def __init__(self, employee: Employee, status: State, current_status_since: datetime.time,
                 work_start_today: datetime.time):
        super().__init__()

        self.employee = employee
        self.status = status
        self.current_status_since = current_status_since
        self.work_start_today = work_start_today

    # Returns rendered row for "Employee Present" report
    def render(self) -> dict:
        return {
            "employee": self.employee.id,
            "employee_name": self.employee.full_name,
            "status_since": self._render_time(self.current_status_since),
            "work_start_today": self._render_time(self.work_start_today),
            "status": frappe.render_template("templates/navbar/checkin_status.html", self.status.render())
        }

    def _render_time(self, time: datetime.time) -> datetime.time:
        return datetime.time(hour=time.hour, minute=time.minute, second=time.second)


class CheckinReportService:
    employees: EmployeeRepository
    data: CheckinRepository

    def __init__(self, employees: EmployeeRepository, data: CheckinRepository):
        super().__init__()

        self.employees = employees
        self.data = data

    @staticmethod
    def prod():
        return CheckinReportService(EmployeeRepository(), CheckinRepository())

    def get_present(self, filter_status=None) -> [PresentEmployee]:
        employees = self.employees.get_all()
        rows = []

        today = datetime.date.today()

        for employee in employees:
            if employee.time_model is not TimeModel.Flextime:
                continue

            events = self.data.get(today, employee.id)
            latest_event = events.get_latest()

            if latest_event is None:
                continue

            if (not latest_event.is_in) and (not latest_event.is_break):
                continue

            status = State.Break if latest_event.is_break else State.In

            if (filter_status is not None) and (status != filter_status):
                continue

            rows.append(PresentEmployee(
                employee,
                status,
                latest_event.timestamp.time(),
                events.events[0].timestamp.time()
            ))

        return rows
