import frappe


class BreakTime:
    # break time is just valid if minimal working time (in seconds) is reached
    min_working_time: int

    # Forced break time in seconds
    break_time: int

    def __init__(self, min_working_time: int, break_time: int):
        self.min_working_time = min_working_time
        self.break_time = break_time


class BreakTimeDefinitions:
    # Sorted list of break time definitions
    regular_times: list[BreakTime]

    # Sorted list of break times valid just for minors
    minor_times: list[BreakTime]

    def __init__(self):
        self.regular_times = []
        self.minor_times = []

    def insert(self, definition: BreakTime, is_minor: bool):
        if is_minor:
            self.minor_times.append(definition)
            self.minor_times.sort(key=lambda x: x.min_working_time)
            return

        self.regular_times.append(definition)
        self.regular_times.sort(key=lambda x: x.min_working_time)

    # Returns the break time in seconds based on total working time
    def get_break_time(self, total_working_time: int, is_minor: bool) -> int:
        if is_minor and self.minor_times:
            return self._search_break_time(self.minor_times, total_working_time)

        return self._search_break_time(self.regular_times, total_working_time)

    @staticmethod
    def _search_break_time(definitions: list[BreakTime], total_working_time: int) -> int:
        break_time = 0

        for definition in definitions:
            if total_working_time < definition.min_working_time:
                break

            break_time = definition.break_time

        return break_time


class BreakTimeRepository:
    def get_definitions(self) -> BreakTimeDefinitions:
        definitions = BreakTimeDefinitions()

        for doc in frappe.get_all("Break time definition", fields=['*']):
            definitions.insert(BreakTime(doc.min_working_time, doc.forced_break_time), doc.only_for_minors)

        return definitions

    def create_default(self):
        # Adults: 6h work => 30m break time
        self._create_definition(21_600, 1_800, False)
        # Adults: 9h work => 45m break time
        self._create_definition(32_400, 2_700, False)

        # Minors: 4h 30m work => 30m break time
        self._create_definition(16_200, 1_800, True)
        # Minors: 6h work => 45m break time
        self._create_definition(21_600, 2_700, True)

    def _create_definition(self, min_working_time: int, forced_break_tine: int, only_for_minors: bool):
        doc = frappe.new_doc("Break time definition")
        doc.min_working_time = min_working_time
        doc.forced_break_time = forced_break_tine
        doc.only_for_minors = 1 if only_for_minors else 0

        doc.save()
