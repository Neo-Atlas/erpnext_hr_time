import datetime
import unittest

from hr_time.api.flextime.break_time import BreakTimeDefinitions, BreakTime
from hr_time.api.flextime.repository import FlextimeDailyStatus, CheckinDuration, DurationType


class TestDailyFlextimeStatus(unittest.TestCase):
    break_time_def = BreakTimeDefinitions()

    def setUp(self):
        self.break_time_def = BreakTimeDefinitions()
        self.break_time_def.insert(BreakTime(21600, 1800), False)
        self.break_time_def.insert(BreakTime(32400, 2700), False)
        self.break_time_def.insert(BreakTime(16200, 1800), True)
        self.break_time_def.insert(BreakTime(21600, 2700), True)

    def test_calculate(self):
        status = FlextimeDailyStatus("", datetime.date.today(), 28_800)
        status.insert_duration(self.get_duration([8, 0], [12, 0], DurationType.WORK))
        status.insert_duration(self.get_duration([12, 0], [12, 30], DurationType.BREAK))
        status.insert_duration(self.get_duration([12, 30], [17, 0], DurationType.WORK))

        status.calculate(self.break_time_def, 3600, False, 1.3)

        self.assertEqual(30600, status.total_working_hours)
        self.assertEqual(0, status.break_time_deducted)
        self.assertEqual(0.5, status.flextime_delta)
        self.assertEqual(1.8, status.time_balance)

    def test_calculate_no_checked_break(self):
        status = FlextimeDailyStatus("", datetime.date.today(), 28_800)
        status.insert_duration(self.get_duration([8, 0], [18, 0], DurationType.WORK))

        status.calculate(self.break_time_def, 3600, False, 1.3)

        self.assertEqual(36_000, status.total_working_hours)
        self.assertEqual(3600, status.break_time_deducted)
        self.assertEqual(1.0, status.flextime_delta)
        self.assertEqual(2.3, status.time_balance)

    def test_calculate_break_time_below_minium(self):
        status = FlextimeDailyStatus("", datetime.date.today(), 28_800)
        status.insert_duration(self.get_duration([8, 0], [12, 0], DurationType.WORK))
        status.insert_duration(self.get_duration([12, 0], [12, 20], DurationType.BREAK))
        status.insert_duration(self.get_duration([12, 20], [17, 0], DurationType.WORK))

        status.calculate(self.break_time_def, 3600, False, 1.3)

        self.assertEqual(31200, status.total_working_hours)
        self.assertEqual(600, status.break_time_deducted)
        self.assertEqual(0.5, status.flextime_delta)
        self.assertEqual(1.8, status.time_balance)

    def test_calculate_break_time_above_minium(self):
        status = FlextimeDailyStatus("", datetime.date.today(), 28_800)
        status.insert_duration(self.get_duration([8, 0], [12, 0], DurationType.WORK))
        status.insert_duration(self.get_duration([12, 0], [12, 50], DurationType.BREAK))
        status.insert_duration(self.get_duration([12, 50], [17, 0], DurationType.WORK))

        status.calculate(self.break_time_def, 3600, False, 1.3)

        self.assertEqual(29400, status.total_working_hours)
        self.assertEqual(0, status.break_time_deducted)
        self.assertEqual(0.17, round(status.flextime_delta, ndigits=2))
        self.assertEqual(1.47, round(status.time_balance, ndigits=2))

    def test_calculate_negative_delta(self):
        status = FlextimeDailyStatus("", datetime.date.today(), 28_800)
        status.insert_duration(self.get_duration([8, 0], [10, 0], DurationType.WORK))

        status.calculate(self.break_time_def, 3600, False, 1.3)

        self.assertEqual(7_200, status.total_working_hours)
        self.assertEqual(0, status.break_time_deducted)
        self.assertEqual(-6.0, status.flextime_delta)
        self.assertEqual(-4.7, status.time_balance)

    def test_calculate_no_checkins(self):
        status = FlextimeDailyStatus("", datetime.date.today(), 28_800)

        status.calculate(self.break_time_def, 3600, False, 1.3)

        self.assertEqual(0, status.total_working_hours)
        self.assertEqual(0, status.break_time_deducted)
        self.assertEqual(-8.0, status.flextime_delta)
        self.assertEqual(-6.7, status.time_balance)

    def test_calculate_minor_break_times(self):
        status = FlextimeDailyStatus("", datetime.date.today(), 28_800)
        status.insert_duration(self.get_duration([8, 0], [13, 0], DurationType.WORK))
        status.insert_duration(self.get_duration([13, 0], [13, 30], DurationType.BREAK))

        status.calculate(self.break_time_def, 3600, True, 1.3)

        self.assertEqual(18_000, status.total_working_hours)
        self.assertEqual(0, status.break_time_deducted)
        self.assertEqual(-3.0, status.flextime_delta)
        self.assertEqual(-1.7, status.time_balance)

    def get_duration(self, start: list[int], end: list[int], type: DurationType) -> CheckinDuration:
        return CheckinDuration(datetime.timedelta(hours=start[0], minutes=start[1]),
                               datetime.timedelta(hours=end[0], minutes=end[1]), type, "", "")
