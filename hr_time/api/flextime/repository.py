import datetime
from enum import Enum
from typing import Optional

import frappe

from hr_time.api.check_in.event import CheckinEvent
from hr_time.api.employee.repository import Employee
from hr_time.api.worklog.repository import Worklog
from hr_time.api.flextime.break_time import BreakTimeDefinitions


class DurationType(Enum):
    WORK = 0,
    BREAK = 1


class CheckinDuration:
    # Duration start
    start: datetime.timedelta

    # Duration end
    end: datetime.timedelta

    # Duration type
    duration_type: DurationType

    # Duration in seconds
    total_time: int

    # Checkin event ID
    event_first: str

    # Checkin event ID
    event_second: str

    def __init__(self, start: datetime.timedelta, end: datetime.timedelta, duration_type: DurationType,
                 event_first: str, event_second: str):
        self.start = start
        self.end = end
        self.duration_type = duration_type
        self.event_first = event_first
        self.event_second = event_second

        self.total_time = (self.end - self.start).seconds.numerator

    @staticmethod
    def build_from_events(first: CheckinEvent, second: CheckinEvent):
        return CheckinDuration(
            datetime.timedelta(hours=first.timestamp.time().hour, minutes=first.timestamp.time().minute,
                               seconds=first.timestamp.time().second),
            datetime.timedelta(hours=second.timestamp.time().hour, minutes=second.timestamp.time().minute,
                               seconds=second.timestamp.time().second),
            DurationType.BREAK if first.is_break else DurationType.WORK,
            first.id,
            second.id
        )


class FlextimeDailyStatus:
    # ID of employee
    employee_id: str

    # Corresponding date of daily status
    date: datetime.date

    # Total working time (including break) in seconds
    total_working_hours: int

    # Forced deducted break time in seconds
    break_time_deducted: int

    # Current time balance in hours
    time_balance: float

    # Target working time (based on definition) in seconds
    target_working_time: int

    # Delta = total_working_hours - break_time_deducted - target_working_time
    flextime_delta: float

    # List of single checkin/checkout events
    durations: list[CheckinDuration]

    # List of daily worklogs
    daily_worklogs: list[Worklog]

    def __init__(self, employee_id: str, date: datetime.date, target_working_time: int):
        self.employee_id = employee_id
        self.date = date
        self.total_working_hours = 0
        self.break_time_deducted = 0
        self.time_balance = 0
        self.target_working_time = target_working_time
        self.flextime_delta = 0
        self.durations = []
        self.daily_worklogs = []

    def insert_duration(self, duration: CheckinDuration):
        self.durations.append(duration)

    def insert_worklogs(self, worklog: Worklog):
        self.daily_worklogs.append(worklog)

    # Calculates the status values based on durations
    def calculate(self, break_definition: BreakTimeDefinitions, deducted_time_on_no_break: int, is_minor: bool,
                  previous_flextime_balance: float):
        self.break_time_deducted = 0
        self.total_working_hours = 0
        checked_break_time = 0

        break_found = False

        for duration in self.durations:
            match duration.duration_type:
                case DurationType.BREAK:
                    checked_break_time += duration.total_time
                    break_found = True
                case DurationType.WORK:
                    self.total_working_hours += duration.total_time

        min_break_time = break_definition.get_break_time(
            self.total_working_hours, is_minor)

        if not break_found and (min_break_time > 0):
            self.break_time_deducted = deducted_time_on_no_break
        elif min_break_time > checked_break_time:
            self.break_time_deducted = min_break_time - checked_break_time

        self.flextime_delta = (
            self.total_working_hours - self.break_time_deducted - self.target_working_time) / 3600
        self.time_balance = previous_flextime_balance + self.flextime_delta


class FlextimeStatusRepository:
    # Returns the date of the latest daily status, None in case no status doc is existing at all
    def get_latest_status_date(self, employee: Employee) -> Optional[datetime.date]:
        docs = frappe.get_all("Flextime daily status", fields=["date"], filters={"employee": employee.id},
                              order_by="date desc", limit=1)

        if not docs:
            return None

        return docs[0].date

    # Returns the flextime balance in hours
    def get_flextime_balance(self, employee_id: str) -> float:
        docs = frappe.get_all("Flextime daily status", fields=["time_balance"], filters={"employee": employee_id},
                              order_by="date desc", limit=1)

        if not docs:
            return 0

        return docs[0].time_balance

    # Returns the flextime balance by the given date
    def get_balance_by_date(self, employee_id: str, date: datetime.date) -> Optional[float]:
        docs = frappe.get_all("Flextime daily status", fields=["time_balance"],
                              filters={"employee": employee_id,
                                       "date": date.isoformat()},
                              order_by="date desc", limit=1)

        if not docs:
            return None

        return docs[0].time_balance

    # Saves a new daily status with checkin duration and worklog reports
    def add(self, status: FlextimeDailyStatus):
        parent = frappe.new_doc("Flextime daily status")
        parent.employee = status.employee_id
        parent.date = status.date
        parent.total_working_hours = status.total_working_hours
        parent.break_time_deducted = status.break_time_deducted
        parent.time_balance = status.time_balance
        parent.target_working_time = status.target_working_time
        parent.flextime_delta = status.flextime_delta
        parent.save()

        for duration in status.durations:
            child = frappe.new_doc(
                "Checkin duration", parent_doc=parent, parentfield="checkin_list")
            child.time_checkin = duration.start
            child.time_checkout = duration.end
            child.total_time = duration.total_time
            child.type = "Work time" if duration.duration_type is DurationType.WORK else "Break time"
            child.checkin = duration.event_first
            child.checkout = duration.event_second
            child.save()

        for worklog in status.daily_worklogs:
            child = frappe.new_doc(
                "Worklog Report", parent_doc=parent, parentfield="worklog_report")
            child.employee = worklog.employee_id
            child.log_time = worklog.log_time
            child.task = worklog.task
            child.task_desc = worklog.task_desc
            child.save()

        parent.load_from_db()
        parent.submit()
