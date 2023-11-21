import datetime
from typing import Optional

import frappe


# Flextime definition of a single weekday
class WorkdayDefinition:
    # ISO weekday, 0 = monday, 6 = sunday
    weekday: int

    # Regular working time in seconds
    working_time: int

    # Start of core time
    core_time_start: datetime.timedelta

    # End of core time
    core_time_end: datetime.timedelta

    def __init__(self, weekday: int, working_time: int, core_time_start: datetime.timedelta,
                 core_time_end: datetime.timedelta):
        self.weekday = weekday
        self.working_time = working_time
        self.core_time_start = core_time_start
        self.core_time_end = core_time_end

    @staticmethod
    def create_from_doc(doc, weekday_int: int, weekday_prefix: str):
        working_hours = doc[weekday_prefix + "_working_hours"]

        return WorkdayDefinition(
            weekday_int,
            0 if working_hours is None else working_hours,
            doc[weekday_prefix + "_core_time_start"],
            doc[weekday_prefix + "_core_time_end"],
        )


class FlextimeDefinition:
    days: dict[int, WorkdayDefinition]

    # This amount of time (in seconds) is deducted, if checked working time is insufficient
    forced_insufficient_break_time: int

    def __init__(self, forced_insufficient_break_time: int):
        self.days = {}
        self.forced_insufficient_break_time = forced_insufficient_break_time

    # Returns the workday definition for the given ISO weekday
    def get_for_weekday(self, weekday: int) -> WorkdayDefinition:
        return self.days[weekday]

    def insert(self, day: WorkdayDefinition):
        self.days[day.weekday] = day


DEFAULT_GRADE = "Standard full-time 40 hours"
DEFAULT_WORKING_TIME = 28_800
DEFAULT_CORE_TIME_START = datetime.timedelta(hours=10)
DEFAULT_CORE_TIME_END = datetime.timedelta(hours=15)


class FlextimeDefinitionRepository:
    _doc_type = "Flextime definition"

    # Cache for loaded definitions by employee grade
    definitions: [str, Optional[FlextimeDefinition]]

    def __init__(self):
        self.definitions = {}

    def get_by_grade(self, grade: str) -> Optional[FlextimeDefinition]:
        if grade in self.definitions:
            return self.definitions[grade]

        doc_definitions = frappe.get_all(self._doc_type, fields=["*"], filters={"name": grade})

        if not doc_definitions:
            self.definitions[grade] = None
            return None

        definition = FlextimeDefinition(doc_definitions[0].forced_insufficient_break_time)
        definition.insert(WorkdayDefinition.create_from_doc(doc_definitions[0], 0, "monday"))
        definition.insert(WorkdayDefinition.create_from_doc(doc_definitions[0], 1, "tuesday"))
        definition.insert(WorkdayDefinition.create_from_doc(doc_definitions[0], 2, "wednesday"))
        definition.insert(WorkdayDefinition.create_from_doc(doc_definitions[0], 3, "thursday"))
        definition.insert(WorkdayDefinition.create_from_doc(doc_definitions[0], 4, "friday"))
        definition.insert(WorkdayDefinition.create_from_doc(doc_definitions[0], 5, "saturday"))
        definition.insert(WorkdayDefinition.create_from_doc(doc_definitions[0], 6, "sunday"))

        self.definitions[grade] = definition
        return definition

    def create_default(self):
        if not frappe.get_all("Employee Grade", filters={"name": DEFAULT_GRADE}):
            doc = frappe.new_doc("Employee Grade")
            doc.name = DEFAULT_GRADE
            doc.save()

        doc = frappe.new_doc(self._doc_type)
        doc.employee_grade = DEFAULT_GRADE

        doc.monday_working_hours = DEFAULT_WORKING_TIME
        doc.monday_core_time_start = DEFAULT_CORE_TIME_START
        doc.monday_core_time_end = DEFAULT_CORE_TIME_END

        doc.tuesday_working_hours = DEFAULT_WORKING_TIME
        doc.tuesday_core_time_start = DEFAULT_CORE_TIME_START
        doc.tuesday_core_time_end = DEFAULT_CORE_TIME_END

        doc.wednesday_working_hours = DEFAULT_WORKING_TIME
        doc.wednesday_core_time_start = DEFAULT_CORE_TIME_START
        doc.wednesday_core_time_end = DEFAULT_CORE_TIME_END

        doc.thursday_working_hours = DEFAULT_WORKING_TIME
        doc.thursday_core_time_start = DEFAULT_CORE_TIME_START
        doc.thursday_core_time_end = DEFAULT_CORE_TIME_END

        doc.friday_working_hours = DEFAULT_WORKING_TIME
        doc.friday_core_time_start = DEFAULT_CORE_TIME_START
        doc.friday_core_time_end = DEFAULT_CORE_TIME_END

        doc.save()
