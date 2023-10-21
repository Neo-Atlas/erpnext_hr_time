import datetime
from typing import Optional

import frappe


class HolidayRepository:
    holidays: Optional[set[datetime.date]]

    def __init__(self):
        self.holidays = None

    # Returns true if the given day is a flextime
    def is_holiday(self, day: datetime.date) -> bool:
        if self.holidays is None:
            self._load()

        return day in self.holidays

    def _load(self):
        self.holidays = set()
        lists = frappe.get_all("Holiday List", fields="*")

        for list in lists:
            days = frappe.get_all('Holiday', fields=['*'], filters=[['parent', 'in', list.name]])

            for day in days:
                self.holidays.add(day.holiday_date)
