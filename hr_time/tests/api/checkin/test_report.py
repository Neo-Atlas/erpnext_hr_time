import datetime
import unittest
from copy import copy
from unittest.mock import MagicMock

from hr_time.api.check_in.event import CheckinEvent
from hr_time.api.check_in.list import CheckinList
from hr_time.api.check_in.report import CheckinReportService
from hr_time.api.check_in.repository import CheckinRepository
from hr_time.api.check_in.service import State
from hr_time.api.employee.repository import EmployeeRepository, TimeModel
from hr_time.tests.fixtures import Fixtures


class CheckinReportTest(unittest.TestCase):
    employees: EmployeeRepository
    data: CheckinRepository

    service: CheckinReportService

    def setUp(self):
        super().setUp()

        self.employees = EmployeeRepository()
        self.data = CheckinRepository()

        self.service = CheckinReportService(self.employees, self.data)

    def test_get_present_not_flextime_model(self):
        employee = copy(Fixtures.employee)
        employee.time_model = TimeModel.Undefined

        self.employees.get_all = MagicMock(return_value=[employee])
        rows = self.service.get_present()

        self.employees.get_all.assert_called_once()
        self.assertEqual(0, len(rows))

    def test_get_present_out_of_office(self):
        self.employees.get_all = MagicMock(return_value=[Fixtures.employee])

        self.data.get = MagicMock(return_value=CheckinList([
            CheckinEvent("001", datetime.datetime(year=2023, month=10, day=30, hour=10, minute=30), True, False),
            CheckinEvent("002", datetime.datetime(year=2023, month=10, day=30, hour=12, minute=00), False, True),
            CheckinEvent("003", datetime.datetime(year=2023, month=10, day=30, hour=12, minute=30), True, False),
            CheckinEvent("004", datetime.datetime(year=2023, month=10, day=30, hour=17, minute=00), False, False),
        ]))

        rows = self.service.get_present()
        self.assertEqual(0, len(rows))

        self.employees.get_all.assert_called_once()
        self.data.get.assert_called_once()
        self.data.get.assert_called_with(datetime.date.today(), "EMP-009")

    def test_get_present_break(self):
        self.setup_break_status()

        rows = self.service.get_present()
        self.assertEqual(1, len(rows))
        self.assertEqual("EMP-009", rows[0].employee.id)
        self.assertEqual(State.Break, rows[0].status)
        self.assertEqual(12, rows[0].current_status_since.hour)
        self.assertEqual(47, rows[0].current_status_since.minute)
        self.assertEqual(10, rows[0].work_start_today.hour)
        self.assertEqual(30, rows[0].work_start_today.minute)

        self.employees.get_all.assert_called_once()
        self.data.get.assert_called_once()
        self.data.get.assert_called_with(datetime.date.today(), "EMP-009")

    def test_get_present_work_first_event(self):
        self.employees.get_all = MagicMock(return_value=[Fixtures.employee])

        self.data.get = MagicMock(return_value=CheckinList([
            CheckinEvent("001", datetime.datetime(year=2023, month=10, day=30, hour=10, minute=30), True, False),
        ]))

        rows = self.service.get_present()
        self.assertEqual(1, len(rows))
        self.assertEqual("EMP-009", rows[0].employee.id)
        self.assertEqual(State.In, rows[0].status)
        self.assertEqual(10, rows[0].current_status_since.hour)
        self.assertEqual(30, rows[0].current_status_since.minute)
        self.assertEqual(10, rows[0].work_start_today.hour)
        self.assertEqual(30, rows[0].work_start_today.minute)

        self.employees.get_all.assert_called_once()
        self.data.get.assert_called_once()
        self.data.get.assert_called_with(datetime.date.today(), "EMP-009")

    def test_get_present_work_after_break(self):
        self.employees.get_all = MagicMock(return_value=[Fixtures.employee])

        self.data.get = MagicMock(return_value=CheckinList([
            CheckinEvent("001", datetime.datetime(year=2023, month=10, day=30, hour=10, minute=15), True, False),
            CheckinEvent("002", datetime.datetime(year=2023, month=10, day=30, hour=12, minute=00), False, True),
            CheckinEvent("003", datetime.datetime(year=2023, month=10, day=30, hour=12, minute=30), True, False)
        ]))

        rows = self.service.get_present()
        self.assertEqual(1, len(rows))
        self.assertEqual("EMP-009", rows[0].employee.id)
        self.assertEqual(State.In, rows[0].status)
        self.assertEqual(12, rows[0].current_status_since.hour)
        self.assertEqual(30, rows[0].current_status_since.minute)
        self.assertEqual(10, rows[0].work_start_today.hour)
        self.assertEqual(15, rows[0].work_start_today.minute)

        self.employees.get_all.assert_called_once()
        self.data.get.assert_called_once()
        self.data.get.assert_called_with(datetime.date.today(), "EMP-009")

    def test_get_present_filter_true(self):
        self.setup_break_status()

        rows = self.service.get_present(filter_status=State.Break)
        self.assertEqual(1, len(rows))

    def test_get_present_filter_false(self):
        self.setup_break_status()

        rows = self.service.get_present(filter_status=State.In)
        self.assertEqual(0, len(rows))

    def setup_break_status(self):
        self.employees.get_all = MagicMock(return_value=[Fixtures.employee])

        self.data.get = MagicMock(return_value=CheckinList([
            CheckinEvent("001", datetime.datetime(year=2023, month=10, day=30, hour=10, minute=30), True, False),
            CheckinEvent("002", datetime.datetime(year=2023, month=10, day=30, hour=12, minute=47), False, True),
        ]))
