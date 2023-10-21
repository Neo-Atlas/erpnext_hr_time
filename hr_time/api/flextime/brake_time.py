import frappe


class BrakeTime:
    # Brake time is just valid if minimal working time (in seconds) is reached
    min_working_time: int

    # Forced brake time in seconds
    brake_time: int

    def __init__(self, min_working_time: int, brake_time: int):
        self.min_working_time = min_working_time
        self.brake_time = brake_time


class BrakeTimeDefinitions:
    # Sorted list of brake time definitions
    regular_times: list[BrakeTime]

    # Sorted list of brake times valid just for minors
    minor_times: list[BrakeTime]

    def __init__(self):
        self.regular_times = [];
        self.minor_times = []

    def insert(self, definition: BrakeTime, is_minor: bool):
        if is_minor:
            self.minor_times.append(definition)
            self.minor_times.sort(key=lambda x: x.min_working_time)
            return

        self.regular_times.append(definition)
        self.regular_times.sort(key=lambda x: x.min_working_time)

    # Returns the brake time in seconds based on total working time
    def get_brake_time(self, total_working_time: int, is_minor: bool) -> int:
        if is_minor and self.minor_times:
            return self._search_brake_time(self.minor_times, total_working_time)

        return self._search_brake_time(self.regular_times, total_working_time)

    @staticmethod
    def _search_brake_time(definitions: list[BrakeTime], total_working_time: int) -> int:
        brake_time = 0

        for definition in definitions:
            if total_working_time < definition.min_working_time:
                break

            brake_time = definition.brake_time

        return brake_time


class BreakTimeRepository:
    def get_definitions(self) -> BrakeTimeDefinitions:
        definitions = BrakeTimeDefinitions()

        for doc in frappe.get_all("Brake time definition", fields=['*']):
            definitions.insert(BrakeTime(doc.min_working_time, doc.forced_brake_time), doc.only_for_minors)

        return definitions
