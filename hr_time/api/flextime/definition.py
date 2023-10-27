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
        return WorkdayDefinition(
            weekday_int,
            doc[weekday_prefix + "_working_hours"],
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


class FlextimeDefinitionRepository:
    # Cache for loaded definitions by employee grade
    definitions: [str, Optional[FlextimeDefinition]]

    def __init__(self):
        self.definitions = {}

    def get_by_grade(self, grade: str) -> Optional[FlextimeDefinition]:
        if grade in self.definitions:
            return self.definitions[grade]

        doc_definitions = frappe.get_all("Flextime definition", fields=["*"], filters={"name": grade})

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
