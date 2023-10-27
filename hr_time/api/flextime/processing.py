import datetime

from hr_time.api import logger
from hr_time.api.check_in.repository import CheckinRepository
from hr_time.api.employee.repository import EmployeeRepository, TimeModel, Employee
from hr_time.api.flextime.break_time import BreakTimeRepository, BreakTimeDefinitions
from hr_time.api.flextime.definition import FlextimeDefinitionRepository, FlextimeDefinition
from hr_time.api.flextime.repository import FlextimeStatusRepository, FlextimeDailyStatus, CheckinDuration, DurationType
from hr_time.api.holiday.repository import HolidayRepository
from hr_time.api.utils.clock import Clock


# Service for processing flextime account status
class FlexTimeProcessingService:
    clock: Clock

    daily_status: FlextimeStatusRepository
    employee: EmployeeRepository
    definitions: FlextimeDefinitionRepository
    break_times: BreakTimeRepository
    holidays: HolidayRepository
    checkin: CheckinRepository

    def __init__(self, clock: Clock, daily_status: FlextimeStatusRepository, employee: EmployeeRepository,
                 definitions: FlextimeDefinitionRepository, break_times: BreakTimeRepository,
                 holidays: HolidayRepository, checkin: CheckinRepository):
        self.clock = clock
        self.daily_status = daily_status
        self.employee = employee
        self.definitions = definitions
        self.break_times = break_times
        self.holidays = holidays
        self.checkin = checkin

    # Creates an instance for productive usage
    @staticmethod
    def prod():
        return FlexTimeProcessingService(Clock(), FlextimeStatusRepository(), EmployeeRepository(),
                                         FlextimeDefinitionRepository(), BreakTimeRepository(), HolidayRepository(),
                                         CheckinRepository())

    # Starts the processing/generation of daily flextime status documents
    def process_daily_status(self):
        employees = self.employee.get_all()
        break_times = self.break_times.get_definitions()

        for employee in employees:
            logger.info("Starting flextime processing of employee " + employee.id)

            if employee.time_model is not TimeModel.Flextime:
                logger.info("Skipping employee " + employee.id + ", as time model is not flextime")
                continue

            definition = self.definitions.get_by_grade(employee.grade)

            if definition is None:
                logger.info(
                    "Skipping employee " + employee.id + ", as no flextime definition was found for grade " + employee.grade)
                continue

            self._process_employee(employee, break_times, definition)

    def _process_employee(self, employee: Employee, break_time: BreakTimeDefinitions, definitions: FlextimeDefinition):
        current_day = self.daily_status.get_latest_status_date(employee)

        if current_day is None:
            current_day = employee.join_date
        else:
            current_day += datetime.timedelta(days=1)

        flextime_balance = self.daily_status.get_flextime_balance(employee.id)
        logger.info(employee.id + ": Found current flextime balance of " + str(flextime_balance) + " hours")

        while current_day < self.clock.date_today():
            logger.info(employee.id + ": Processing day " + current_day.isoformat())

            if self.holidays.is_holiday(current_day):
                target_working_time = 0
            else:
                target_working_time = definitions.get_for_weekday(current_day.weekday()).working_time
            logger.info("Set target working time to " + str(target_working_time))

            status = FlextimeDailyStatus(
                employee.id,
                current_day,
                target_working_time
            )

            durations = self.checkin.get(current_day, employee.id).get_durations()
            logger.info("Found " + str(len(durations)) + " durations")

            for duration in durations:
                status.insert_duration(duration)

            status.calculate(break_time, definitions.forced_insufficient_break_time, employee.is_minor(),
                             flextime_balance)
            self.daily_status.add(status)

            flextime_balance = status.time_balance
            logger.info("New flextime balance: " + str(flextime_balance))

            current_day += datetime.timedelta(days=1)
