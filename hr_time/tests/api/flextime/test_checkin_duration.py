import datetime
import unittest

from hr_time.api.flextime.repository import CheckinDuration, DurationType


class TestCheckinDuration(unittest.TestCase):
    def test_init_correct_total_time(self):
        duration = CheckinDuration(datetime.timedelta(seconds=3600), datetime.timedelta(seconds=7000), DurationType.WORK, "", "")
        self.assertEqual(3400, duration.total_time)
