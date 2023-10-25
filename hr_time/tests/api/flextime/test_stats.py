import datetime
import unittest
from unittest.mock import MagicMock

from hr_time.api.employee.repository import EmployeeRepository, Employee, TimeModel
from hr_time.api.flextime.repository import FlextimeStatusRepository
from hr_time.api.flextime.stats import FlextimeStatisticsService


class FlextimeStatisticsServiceTest(unittest.TestCase):
    dummy_employee = Employee("EMP-002", TimeModel.Flextime, "Test", datetime.date.today(), datetime.date.today())

    employee: EmployeeRepository
    status: FlextimeStatusRepository

    service: FlextimeStatisticsService

    def setUp(self):
        super().setUp()

        self.employee = EmployeeRepository()
        self.status = FlextimeStatusRepository()

        self.service = FlextimeStatisticsService(self.employee, self.status)

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
        self.employee.get_current = MagicMock(return_value=self.dummy_employee)
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

        self.assertEqual("EMP-002", self.status.get_flextime_balance.call_args.args[0])

        self.assertEqual("EMP-002", self.status.get_balance_by_date.call_args.args[0])
        self.assertEqual(datetime.date.today() - datetime.timedelta(days=30),
                         self.status.get_balance_by_date.call_args.args[1])

    def test_get_balance_correct_trend(self):
        self.employee.get_current = MagicMock(return_value=self.dummy_employee)
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

        self.assertEqual("EMP-002", self.status.get_flextime_balance.call_args.args[0])

        self.assertEqual("EMP-002", self.status.get_balance_by_date.call_args.args[0])
        self.assertEqual(datetime.date.today() - datetime.timedelta(days=30),
                         self.status.get_balance_by_date.call_args.args[1])
