import datetime
import unittest
from unittest.mock import MagicMock

from hr_time.api.check_in.event import CheckinEvent
from hr_time.api.check_in.list import CheckinList
from hr_time.api.check_in.repository import CheckinRepository
from hr_time.api.employee.repository import EmployeeRepository
from hr_time.api.flextime.repository import FlextimeStatusRepository
from hr_time.api.flextime.stats import FlextimeStatisticsService
from hr_time.api.shared.utils.clock import Clock
from hr_time.tests.fixtures import Fixtures


class FlextimeStatisticsServiceTest(unittest.TestCase):
    clock: Clock
    employee: EmployeeRepository
    status: FlextimeStatusRepository
    checkin: CheckinRepository

    service: FlextimeStatisticsService

    def setUp(self):
        super().setUp()

        self.clock = Clock()
        self.employee = EmployeeRepository()
        self.status = FlextimeStatusRepository()
        self.checkin = CheckinRepository()

        self.service = FlextimeStatisticsService(self.clock, self.employee, self.status, self.checkin)

    def test_get_balance_employee_not_found(self):
        self.employee.get_current = MagicMock(return_value=None)
        self.status.get_flextime_balance = MagicMock(return_value=datetime.timedelta())

        balance = self.service.get_balance()
        self.assertEqual(0, balance.balance_hours)
        self.assertEqual(0, balance.balance_minutes)
        self.assertEqual(0, balance.trend_hours)
        self.assertEqual(0, balance.trend_minutes)
        self.assertEqual(0, balance.trend_percent)

        self.employee.get_current.assert_called_once()
        self.status.get_flextime_balance.assert_not_called()

    def test_get_balance_no_previous_month(self):
        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.status.get_flextime_balance = MagicMock(return_value=1.2)
        self.status.get_balance_by_date = MagicMock(return_value=None)

        balance = self.service.get_balance()
        self.assertEqual(1, balance.balance_hours)
        self.assertEqual(12, balance.balance_minutes)
        self.assertEqual(0, balance.trend_hours)
        self.assertEqual(0, balance.trend_minutes)
        self.assertEqual(0, balance.trend_percent)

        self.employee.get_current.assert_called_once()
        self.status.get_flextime_balance.assert_called_once()
        self.status.get_balance_by_date.assert_called_once()

        self.assertEqual("EMP-009", self.status.get_flextime_balance.call_args.args[0])

        self.assertEqual("EMP-009", self.status.get_balance_by_date.call_args.args[0])
        self.assertEqual(datetime.date.today() - datetime.timedelta(days=30),
                         self.status.get_balance_by_date.call_args.args[1])

    def test_get_balance_correct_trend(self):
        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.status.get_flextime_balance = MagicMock(return_value=1.3)
        self.status.get_balance_by_date = MagicMock(return_value=0.8)

        balance = self.service.get_balance()
        self.assertEqual(1, balance.balance_hours)
        self.assertEqual(18, balance.balance_minutes)
        self.assertEqual(0, balance.trend_hours)
        self.assertEqual(30, balance.trend_minutes)
        self.assertEqual(0.38, round(balance.trend_percent, ndigits=2))

        self.employee.get_current.assert_called_once()
        self.status.get_flextime_balance.assert_called_once()
        self.status.get_balance_by_date.assert_called_once()

        self.assertEqual("EMP-009", self.status.get_flextime_balance.call_args.args[0])

        self.assertEqual("EMP-009", self.status.get_balance_by_date.call_args.args[0])
        self.assertEqual(datetime.date.today() - datetime.timedelta(days=30),
                         self.status.get_balance_by_date.call_args.args[1])

    def test_get_current_duration_employee_unknown(self):
        self.employee.get_current = MagicMock(return_value=None)

        self.assertEqual(0, self.service.get_current_duration())
        self.employee.get_current.assert_called_once()

    def test_get_current_duration_no_events_today(self):
        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.checkin.get = MagicMock(return_value=CheckinList([]))

        self.assertEqual(0, self.service.get_current_duration())

        self.employee.get_current.assert_called_once()
        self.checkin.get.assert_called_once()
        self.assertEqual(datetime.date.today(), self.checkin.get.call_args.args[0])
        self.assertEqual("EMP-009", self.checkin.get.call_args.args[1])

    def test_get_current_duration_open_work(self):
        self.clock.now = MagicMock(return_value=datetime.datetime(2023, 1, 1, 8, 30))

        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.checkin.get = MagicMock(return_value=CheckinList([
            CheckinEvent("001", datetime.datetime(2023, 1, 1, 8, 0), True, False),
        ]))

        self.assertEqual(1800, self.service.get_current_duration())

        self.employee.get_current.assert_called_once()
        self.checkin.get.assert_called_once()
        self.assertEqual(datetime.date.today(), self.checkin.get.call_args.args[0])
        self.assertEqual("EMP-009", self.checkin.get.call_args.args[1])

    def test_get_current_duration_closed_work(self):
        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.checkin.get = MagicMock(return_value=CheckinList([
            CheckinEvent("001", datetime.datetime(2023, 1, 1, 8, 0), True, False),
            CheckinEvent("002", datetime.datetime(2023, 1, 1, 8, 15), False, False)
        ]))

        self.assertEqual(900, self.service.get_current_duration())

        self.employee.get_current.assert_called_once()
        self.checkin.get.assert_called_once()
        self.assertEqual(datetime.date.today(), self.checkin.get.call_args.args[0])
        self.assertEqual("EMP-009", self.checkin.get.call_args.args[1])

    def test_get_current_duration_open_break(self):
        self.clock.now = MagicMock(return_value=datetime.datetime(2023, 1, 1, 8, 40))

        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.checkin.get = MagicMock(return_value=CheckinList([
            CheckinEvent("001", datetime.datetime(2023, 1, 1, 8, 0), True, False),
            CheckinEvent("002", datetime.datetime(2023, 1, 1, 8, 30), False, True)
        ]))

        self.assertEqual(600, self.service.get_current_duration())

        self.employee.get_current.assert_called_once()
        self.checkin.get.assert_called_once()
        self.assertEqual(datetime.date.today(), self.checkin.get.call_args.args[0])
        self.assertEqual("EMP-009", self.checkin.get.call_args.args[1])

    def test_get_current_duration_closed_break(self):
        self.clock.now = MagicMock(return_value=datetime.datetime(2023, 1, 1, 8, 45))

        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.checkin.get = MagicMock(return_value=CheckinList([
            CheckinEvent("001", datetime.datetime(2023, 1, 1, 8, 0), True, False),
            CheckinEvent("002", datetime.datetime(2023, 1, 1, 8, 30), False, True),
            CheckinEvent("002", datetime.datetime(2023, 1, 1, 8, 40), True, False)
        ]))

        self.assertEqual(2100, self.service.get_current_duration())

        self.employee.get_current.assert_called_once()
        self.checkin.get.assert_called_once()
        self.assertEqual(datetime.date.today(), self.checkin.get.call_args.args[0])
        self.assertEqual("EMP-009", self.checkin.get.call_args.args[1])

    def test_get_current_duration_double_break(self):
        self.clock.now = MagicMock(return_value=datetime.datetime(2023, 1, 1, 9, 8))

        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.checkin.get = MagicMock(return_value=CheckinList([
            CheckinEvent("001", datetime.datetime(2023, 1, 1, 8, 0), True, False),
            CheckinEvent("002", datetime.datetime(2023, 1, 1, 8, 30), False, True),
            CheckinEvent("002", datetime.datetime(2023, 1, 1, 8, 40), True, False),
            CheckinEvent("002", datetime.datetime(2023, 1, 1, 8, 50), False, True),
        ]))

        self.assertEqual(1680, self.service.get_current_duration())

        self.employee.get_current.assert_called_once()
        self.checkin.get.assert_called_once()
        self.assertEqual(datetime.date.today(), self.checkin.get.call_args.args[0])
        self.assertEqual("EMP-009", self.checkin.get.call_args.args[1])

    def test_get_current_duration_complete_working_day(self):
        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.checkin.get = MagicMock(return_value=CheckinList([
            CheckinEvent("001", datetime.datetime(2023, 1, 1, 8, 0), True, False),
            CheckinEvent("002", datetime.datetime(2023, 1, 1, 8, 30), False, True),
            CheckinEvent("002", datetime.datetime(2023, 1, 1, 8, 40), True, False),
            CheckinEvent("002", datetime.datetime(2023, 1, 1, 10, 2, 21), False, False),
        ]))

        self.assertEqual(6741, self.service.get_current_duration())

        self.employee.get_current.assert_called_once()
        self.checkin.get.assert_called_once()
        self.assertEqual(datetime.date.today(), self.checkin.get.call_args.args[0])
        self.assertEqual("EMP-009", self.checkin.get.call_args.args[1])
