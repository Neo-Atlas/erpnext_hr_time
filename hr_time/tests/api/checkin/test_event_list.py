import datetime
import unittest

from hr_time.api.check_in.event import CheckinEvent
from hr_time.api.check_in.list import CheckinList
from hr_time.api.flextime.repository import DurationType


class TestCheckinEventList(unittest.TestCase):
    def test_get_durations_day_starts_with_out_event(self):
        event_list = CheckinList([
            CheckinEvent("001", self.timestamp(8, 0), False, False),
            CheckinEvent("002", self.timestamp(9, 0), True, False),
            CheckinEvent("003", self.timestamp(12, 0), False, False),
        ])

        durations = event_list.get_durations()
        self.assertEqual(1, len(durations))

        self.assertEqual(DurationType.WORK, durations[0].duration_type)
        self.assertEqual(10_800, durations[0].total_time)
        self.assertEqual("002", durations[0].event_first)
        self.assertEqual("003", durations[0].event_second)

    def test_get_durations_correct_break_handling(self):
        event_list = CheckinList([
            CheckinEvent("001", self.timestamp(9, 0), True, False),
            CheckinEvent("002", self.timestamp(12, 0), False, True),
            CheckinEvent("003", self.timestamp(12, 30), True, False),
            CheckinEvent("004", self.timestamp(15, 0), False, False),
        ])

        durations = event_list.get_durations()
        self.assertEqual(3, len(durations))

        self.assertEqual(DurationType.WORK, durations[0].duration_type)
        self.assertEqual(10_800, durations[0].total_time)
        self.assertEqual("001", durations[0].event_first)
        self.assertEqual("002", durations[0].event_second)

        self.assertEqual(DurationType.BREAK, durations[1].duration_type)
        self.assertEqual(1800, durations[1].total_time)
        self.assertEqual("002", durations[1].event_first)
        self.assertEqual("003", durations[1].event_second)

        self.assertEqual(DurationType.WORK, durations[2].duration_type)
        self.assertEqual(9000, durations[2].total_time)
        self.assertEqual("003", durations[2].event_first)
        self.assertEqual("004", durations[2].event_second)

    def test_get_durations_double_checkin_ignored(self):
        event_list = CheckinList([
            CheckinEvent("001", self.timestamp(9, 0), True, False),
            CheckinEvent("002", self.timestamp(9, 0), True, False),
            CheckinEvent("003", self.timestamp(12, 0), False, False),
        ])

        durations = event_list.get_durations()
        self.assertEqual(1, len(durations))

        self.assertEqual(DurationType.WORK, durations[0].duration_type)
        self.assertEqual(10_800, durations[0].total_time)
        self.assertEqual("001", durations[0].event_first)
        self.assertEqual("003", durations[0].event_second)

    def test_get_durations_double_break_checkout_ignored(self):
        event_list = CheckinList([
            CheckinEvent("001", self.timestamp(9, 0), True, False),
            CheckinEvent("002", self.timestamp(12, 0), False, True),
            CheckinEvent("003", self.timestamp(12, 15), False, True),
            CheckinEvent("004", self.timestamp(12, 30), True, False),
            CheckinEvent("005", self.timestamp(15, 0), False, False),
        ])

        durations = event_list.get_durations()
        self.assertEqual(3, len(durations))

        self.assertEqual(DurationType.BREAK, durations[1].duration_type)
        self.assertEqual(1800, durations[1].total_time)
        self.assertEqual("002", durations[1].event_first)
        self.assertEqual("004", durations[1].event_second)

    def test_get_durations_day_starts_with_break(self):
        event_list = CheckinList([
            CheckinEvent("001", self.timestamp(9, 0), False, True),
            CheckinEvent("002", self.timestamp(9, 30), True, False),
            CheckinEvent("003", self.timestamp(11, 0, 43), False, False),
        ])

        durations = event_list.get_durations()
        self.assertEqual(2, len(durations))

        self.assertEqual(DurationType.BREAK, durations[0].duration_type)
        self.assertEqual(1800, durations[0].total_time)
        self.assertEqual("001", durations[0].event_first)
        self.assertEqual("002", durations[0].event_second)

        self.assertEqual(DurationType.WORK, durations[1].duration_type)
        self.assertEqual(5443, durations[1].total_time)
        self.assertEqual("002", durations[1].event_first)
        self.assertEqual("003", durations[1].event_second)

    def test_get_durations_missing_checkout(self):
        event_list = CheckinList([
            CheckinEvent("001", self.timestamp(9, 0), True, False),
        ])

        durations = event_list.get_durations()
        self.assertEqual(0, len(durations))

    def timestamp(self, hour: int, minute: int, second: int = 0) -> datetime.datetime:
        return datetime.datetime(year=2023, month=5, day=1, hour=hour, minute=minute, second=second)
