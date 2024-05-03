import datetime
from typing import Optional

import frappe


class Request:
    is_half_day: bool

    def __init__(self, is_half_day: bool):
        self.is_half_day = is_half_day


class VacationRepository:
    # Returns approved requests
    def get_approved_request(self, employee_id: str, date: datetime.date) -> Optional[Request]:
        docs = frappe.get_all("Leave Application", fields=["half_day"],
                              filters=[["employee", "=", employee_id], ["from_date", "<=", date],
                                       ["to_date", ">=", date], ["status", "=", "Approved"]])

        if not docs:
            return None

        return Request(docs[0]["half_day"])
