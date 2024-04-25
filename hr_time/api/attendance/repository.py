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

    def to_doc(self) -> str:
        match self:
            case Status.Present:
                return "Present"
            case Status.Absent:
                return "Absent"
            case Status.OnLeave:
                return "On Leave"

        raise Exception("Unable to convert " + str(self) + " attendance status to doc string")


class LeaveType(enum.Enum):
    Undefined = 0,
    Sick = 1

    @staticmethod
    def from_doc(data: Optional[str]):
        if data == "Sick Leave":
            return LeaveType.Sick

        return LeaveType.Undefined

    def to_doc(self) -> str:
        if self is LeaveType.Sick:
            return "Sick Leave"

        raise Exception("Unable to convert " + str(self) + " attendance leave type to doc string")


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

        status = Status.from_doc(docs[0].status)

        return Attendance(employee_id,
                          docs[0].attendance_date,
                          status,
                          None if status is not Status.OnLeave else LeaveType.from_doc(docs[0].leave_type)
                          )

    # Saves the given attendance record
    def create(self, attendance: Attendance):
        doc = frappe.new_doc("Attendance")
        doc.employee = attendance.employee_id
        doc.status = attendance.status.to_doc()
        doc.attendance_date = attendance.date

        if attendance.leave_type is not None:
            doc.leave_type = attendance.leave_type.to_doc()

        doc.save()
        doc.submit()
