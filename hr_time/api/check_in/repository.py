import datetime

import frappe

from hr_time.api.check_in.event import CheckinEvent
from hr_time.api.check_in.list import CheckinList
from hr_time.api.check_in.enums import LogType


class CheckinRepository:
    def get(self, date: datetime.date, employee_id: str) -> CheckinList:
        """Returns all checkin events of the given date for the given employee"""
        time_min = date.isoformat() + " 00:00:00"
        time_max = date.isoformat() + " 23:59:59"

        docs = frappe.get_all("Employee Checkin", fields=["name", "employee", "log_type", "time", "custom_is_break"],
                              filters=[["employee", "=", employee_id], ["time", ">=", time_min],
                                       ["time", "<=", time_max]], order_by="time asc")

        events = []

        for doc in docs:
            events.append(CheckinEvent(doc.name, doc.time, doc.log_type == LogType.IN.value, doc.custom_is_break))

        return CheckinList(events)

    def checkin(self, employee_id: str, log_type: LogType, is_break: bool):
        """Create new checkin record"""
        doc = frappe.new_doc("Employee Checkin")
        doc.time = datetime.datetime.now()
        doc.employee = employee_id
        doc.log_type = log_type.value
        doc.custom_is_break = is_break
        doc.save()
