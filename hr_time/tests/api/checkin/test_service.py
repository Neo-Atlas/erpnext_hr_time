import datetime
import unittest
from unittest.mock import MagicMock

from hr_time.api.check_in.event import CheckinEvent
from hr_time.api.check_in.list import CheckinList
from hr_time.api.check_in.repository import CheckinRepository
from hr_time.api.check_in.service import CheckinService, State
from hr_time.api.employee.repository import EmployeeRepository, Employee, TimeModel


class CheckinServiceTest(unittest.TestCase):
    dummy_employee = Employee("EMP-009", TimeModel.Flextime, "Test", datetime.date.today(), datetime.date.today())

    employee: EmployeeRepository
    data: CheckinRepository

    service: CheckinService

    def setUp(self):
        super().setUp()

        self.employee = EmployeeRepository()
        self.data = CheckinRepository()

        self.service = CheckinService(self.employee, self.data)

    def test_get_current_status_employee_unknown(self):
        self.employee.get_current = MagicMock(return_value=None)

        self.assertEqual(State.Unknown, self.service.get_current_status().state)
        self.employee.get_current.assert_called_once()

    def test_get_current_empty_event_list(self):
        self.employee.get_current = MagicMock(return_value=self.dummy_employee)
        self.data.get = MagicMock(return_value=CheckinList([]))

        self.assertEqual(State.Out, self.service.get_current_status().state)

        self.employee.get_current.assert_called_once()
        self.data.get.assert_called_once()
        self.assertEqual(datetime.date.today(), self.data.get.call_args.args[0])
        self.assertEqual("EMP-009", self.data.get.call_args.args[1])

    def test_get_current_break(self):
        self.employee.get_current = MagicMock(return_value=self.dummy_employee)
        self.data.get = MagicMock(return_value=CheckinList([
            CheckinEvent("E001", datetime.datetime.now(), True, False),
            CheckinEvent("E002", datetime.datetime.now(), False, True),
        ]))

        self.assertEqual(State.Break, self.service.get_current_status().state)

    def test_get_current_work(self):
        self.employee.get_current = MagicMock(return_value=self.dummy_employee)
        self.data.get = MagicMock(return_value=CheckinList([
            CheckinEvent("E001", datetime.datetime.now(), True, False),
        ]))

        self.assertEqual(State.In, self.service.get_current_status().state)

    def test_get_current_out(self):
        self.employee.get_current = MagicMock(return_value=self.dummy_employee)
        self.data.get = MagicMock(return_value=CheckinList([
            CheckinEvent("E001", datetime.datetime.now(), True, False),
            CheckinEvent("E002", datetime.datetime.now(), False, False),
        ]))

        self.assertEqual(State.Out, self.service.get_current_status().state)

    def test_get_current_had_break_false(self):
        self.employee.get_current = MagicMock(return_value=self.dummy_employee)
        self.data.get = MagicMock(return_value=CheckinList([
            CheckinEvent("E001", datetime.datetime.now(), True, False),
            CheckinEvent("E002", datetime.datetime.now(), False, False),
        ]))

        self.assertFalse(self.service.get_current_status().had_break)

    def test_get_current_had_break_true(self):
        self.employee.get_current = MagicMock(return_value=self.dummy_employee)
        self.data.get = MagicMock(return_value=CheckinList([
            CheckinEvent("E001", datetime.datetime.now(), True, False),
            CheckinEvent("E002", datetime.datetime.now(), False, True),
            CheckinEvent("E003", datetime.datetime.now(), True, False),
            CheckinEvent("E004", datetime.datetime.now(), False, False),
        ]))

        self.assertTrue(self.service.get_current_status().had_break)
