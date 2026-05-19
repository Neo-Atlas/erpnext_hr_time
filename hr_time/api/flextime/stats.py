import datetime
import math

from hr_time.api.shared.utils.clock import Clock
from hr_time.api.check_in.repository import CheckinRepository
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
    clock: Clock

    employee: EmployeeRepository
    status: FlextimeStatusRepository
    checkin: CheckinRepository

    def __init__(self, clock: Clock, employee: EmployeeRepository, status: FlextimeStatusRepository,
                 checkin: CheckinRepository):
        super().__init__()

        self.clock = clock
        self.employee = employee
        self.status = status
        self.checkin = checkin

    @staticmethod
    def prod():
        return FlextimeStatisticsService(Clock(), EmployeeRepository(), FlextimeStatusRepository(), CheckinRepository())

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

    # Returns the total duration of the current status this day in seconds
    def get_current_duration(self) -> int:
        employee = self.employee.get_current()

        if employee is None:
            return 0

        events = self.checkin.get(self.clock.date_today(), employee.id)
        events.close_current(self.clock)

        durations = events.get_durations()
        if not durations:
            return 0

        current_type = durations[-1].duration_type
        total_seconds = 0

        for duration in durations:
            if duration.duration_type != current_type:
                continue

            total_seconds += duration.total_time

        return total_seconds
    
    # flextime/stats.py
    def get_todays_worked_seconds(self, employee_id: str = None) -> int:
        """Get total worked seconds for today, including current open session"""
        if not employee_id:
            employee = self.employee.get_current()
            if not employee:
                return 0
            employee_id = employee.id
        
        events = self.checkin.get(self.clock.date_today(), employee_id)
        
        total_worked_seconds = 0
        for duration in events.get_durations():
            if duration.duration_type.name == "WORK":
                total_worked_seconds += duration.total_time

        # Add current open session if checked in
        latest = events.get_latest()
        if latest and latest.is_in and not latest.is_break:
            now = self.clock.now()
            current_session = int((now - latest.timestamp).total_seconds())
            total_worked_seconds += current_session

        return total_worked_seconds

    def get_todays_break_seconds(self, employee_id: str = None) -> int:
        """Get total break seconds for today, including current break if active"""
        if not employee_id:
            employee = self.employee.get_current()
            if not employee:
                return 0
            employee_id = employee.id
        
        events = self.checkin.get(self.clock.date_today(), employee_id)
        
        total_break_seconds = 0
        for duration in events.get_durations():
            if duration.duration_type.name != "WORK":  # BREAK
                total_break_seconds += duration.total_time
        
        # Add current break if on break
        latest = events.get_latest()
        if latest and not latest.is_in and latest.is_break:
            now = self.clock.now()
            current_break = int((now - latest.timestamp).total_seconds())
            total_break_seconds += current_break
        
        return total_break_seconds
