import datetime
from enum import Enum
from typing import Optional

import frappe


class TimeModel(Enum):
    Undefined = 0
    Flextime = 1


class Employee:
    # Unique employee ID
    id: str

    # Full name of employee
    full_name: str

    # Assigned time model
    time_model: TimeModel

    # Employee class, which links to flextime definition
    grade: str

    date_of_birth: datetime.date

    # Employee joined company at this date
    join_date: datetime.date

    def __init__(self, id: str, full_name: str, time_model: TimeModel, grade: str, date_of_birth: datetime.date,
                 join_date: datetime.date):
        self.id = id
        self.full_name = full_name
        self.time_model = time_model
        self.grade = grade
        self.date_of_birth = date_of_birth
        self.join_date = join_date

    # Returns false if the Employees age is below 18 years
    def is_minor(self, today: Optional[datetime.date] = None) -> bool:
        if today is None:
            today = datetime.date.today()

        try:
            birthday_18 = datetime.date(self.date_of_birth.year + 18, self.date_of_birth.month, self.date_of_birth.day)
        except ValueError:
            # Handle leap year
            birthday_18 = datetime.date(self.date_of_birth.year + 18, self.date_of_birth.month, 28)

        return today < birthday_18

    def get_url(self) -> str:
        return "/app/employee/" + self.id


class EmployeeRepository:
    doc_fields = ["name", "employee_name", "custom_time_model", "grade", "date_of_birth", "date_of_joining"]

    def get_all(self) -> list[Employee]:
        docs_employees = frappe.get_all("Employee", fields=self.doc_fields)
        employees = []

        for doc in docs_employees:
            employees.append(self._build_from_doc(doc))

        return employees

    # Returns the Employee object of the current user
    def get_current(self) -> Optional[Employee]:
        user_id = frappe.get_user().doc.email
        docs = frappe.get_all("Employee", fields=self.doc_fields, filters={"user_id": user_id})

        if not docs:
            return None

        return self._build_from_doc(docs[0])

    @staticmethod
    def _build_from_doc(doc) -> Employee:
        time_model = TimeModel.Flextime if doc.custom_time_model == "Flextime account" else TimeModel.Undefined
        return Employee(doc.name, doc.employee_name, time_model, doc.grade, doc.date_of_birth, doc.date_of_joining)
