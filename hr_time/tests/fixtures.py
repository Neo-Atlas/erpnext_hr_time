import datetime

from hr_time.api.employee.repository import Employee, TimeModel


class Fixtures:
    employee = Employee("EMP-009", "Elon Musk", TimeModel.Flextime, "Test", datetime.date.today(), datetime.date.today())
