import datetime
import math

from hr_time.api.employee.repository import EmployeeRepository
from hr_time.api.flextime.repository import FlextimeStatusRepository


class FlextimeBalance:
    # Current account balance in hours
    balance_hours: int

    # Current account balance in minutes
    balance_minutes: int

    # Monthly growth in hours
    trend_hours: int

    # Monthly growth in minutes
    trend_minutes: int

    # Monthly growth in percent (0-1)
    trend_percent: float

    def __init__(self, balance: float, monthly_growth: float):
        super().__init__()

        if balance != 0:
            self.trend_percent = abs(monthly_growth / balance)
            if monthly_growth < 0:
                self.trend_percent *= -1
        else:
            self.trend_percent = 0

        balance = self._float_to_time(balance)
        self.balance_hours = balance[0]
        self.balance_minutes = balance[1]

        trend = self._float_to_time(monthly_growth)
        self.trend_hours = trend[0]
        self.trend_minutes = trend[1]

    def is_zero(self) -> bool:
        return (self.balance_hours == 0) and (self.balance_minutes == 0)

    @staticmethod
    def _float_to_time(time: float) -> list[int]:
        sign = -1 if time < 0 else 1

        hours = int(math.floor(math.fabs(time)) * sign)
        minutes = round((time - hours) * 60)

        return [hours, minutes]


class FlextimeStatisticsService:
    employee: EmployeeRepository
    status: FlextimeStatusRepository

    def __init__(self, employee: EmployeeRepository, status: FlextimeStatusRepository):
        super().__init__()

        self.employee = employee
        self.status = status

    @staticmethod
    def prod():
        return FlextimeStatisticsService(EmployeeRepository(), FlextimeStatusRepository())

    def get_balance(self) -> FlextimeBalance:
        employee = self.employee.get_current()

        if employee is None:
            return FlextimeBalance(0, 0)

        current = self.status.get_flextime_balance(employee.id)
        last_month = self.status.get_balance_by_date(employee.id, datetime.date.today() - datetime.timedelta(days=30))

        if last_month is None:
            trend = 0
        else:
            trend = current - last_month

        return FlextimeBalance(current, trend)
