import datetime

import frappe

from hr_time.api.check_in.event import CheckinEvent
from hr_time.api.check_in.list import CheckinList


class CheckinRepository:
    # Returns all checkin events of the given date for the given employee
    def get(self, date: datetime.date, employee_id: str) -> CheckinList:
        time_min = date.isoformat() + " 00:00:00"
        time_max = date.isoformat() + " 23:59:59"

        docs = frappe.get_all("Employee Checkin", fields=["name", "employee", "log_type", "time", "custom_is_brake"],
                              filters=[["employee", "=", employee_id], ["time", ">=", time_min],
                                       ["time", "<=", time_max]], order_by="time asc")

        events = []

        for doc in docs:
            events.append(CheckinEvent(doc.name, doc.time, doc.log_type == "IN", doc.custom_is_brake))

        return CheckinList(events)

    def checkin(self, employee_id: str, log_type: str, is_break: bool):
        doc = frappe.new_doc("Employee Checkin")
        doc.time = datetime.datetime.now()
        doc.employee = employee_id
        doc.log_type = log_type
        doc.custom_is_break = is_break

        doc.save()
