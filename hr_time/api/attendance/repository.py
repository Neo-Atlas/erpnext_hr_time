import datetime
import enum
from datetime import date
from typing import Optional

import frappe


class Status(enum.Enum):
    Present = 0,
    Absent = 1,
    OnLeave = 2,
    Other = 3

    @staticmethod
    def from_doc(data: str):
        match data:
            case "Present":
                return Status.Present
            case "Absent":
                return Status.Absent
            case "On Leave":
                return Status.OnLeave

        return Status.Other


class LeaveType(enum.Enum):
    Undefined = 0,
    Sick = 1

    @staticmethod
    def from_doc(data: Optional[str]):
        if data == "Sick Leave":
            return LeaveType.Sick

        return LeaveType.Undefined


class Attendance:
    employee_id: str
    status: Status
    date: date

    # Leave type is only used if status = OnLeave
    leave_type: Optional[LeaveType]

    def __init__(self, employee_id: str, date: datetime.date, status: Status, leave_type=Optional[LeaveType]):
        self.leave_type = leave_type
        self.date = date
        self.status = status
        self.employee_id = employee_id


class AttendanceRepository:
    def get(self, employee_id: str, day: datetime.date) -> Optional[Attendance]:
        docs = frappe.get_all("Attendance", fields=["employee", "status", "leave_type", "attendance_date"],
                              filters=[["employee", "=", employee_id], ["attendance_date", "=", day]])

        if not docs:
            return None

        status = Status.from_doc(docs[0].status);

        return Attendance(employee_id,
                          docs[0].attendance_date,
                          status,
                          None if status is not Status.OnLeave else LeaveType.from_doc(docs[0].leave_type)
                          )
