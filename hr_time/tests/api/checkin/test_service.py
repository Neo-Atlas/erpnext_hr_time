import datetime
import unittest
from unittest.mock import MagicMock, patch

from hr_time.api.check_in.event import CheckinEvent
from hr_time.api.check_in.list import CheckinList
from hr_time.api.check_in.repository import CheckinRepository
from hr_time.api.check_in.service import CheckinService, State, Action
from hr_time.api.check_in.enums import LogType
from hr_time.api.employee.repository import EmployeeRepository
from hr_time.tests.fixtures import Fixtures


class TestCheckinService(unittest.TestCase):
    employee: EmployeeRepository
    data: CheckinRepository
    service: CheckinService

    def setUp(self):
        self.employee = EmployeeRepository()
        self.data = CheckinRepository()
        self.service = CheckinService(self.employee, self.data)

    @patch('hr_time.api.employee.repository.frappe.get_user')
    @patch('hr_time.api.employee.repository.frappe.get_all')
    def test_get_current_status_employee_unknown(self, mock_emp_get_all, mock_get_user):
        # Mock frappe.get_user()
        mock_user = MagicMock()
        mock_user.doc.email = "test@example.com"
        mock_get_user.return_value = mock_user
        mock_emp_get_all.return_value = []  # No employee found
        self.assertEqual(State.UNKNOWN, self.service.get_current_status().state)

    @patch('hr_time.api.employee.repository.frappe.get_user')
    @patch('hr_time.api.check_in.repository.frappe.get_all')
    @patch('hr_time.api.employee.repository.frappe.get_all')
    def test_get_current_empty_event_list(self, mock_emp_get_all, mock_checkin_get_all, mock_get_user):
        # Mock frappe.get_user()
        mock_user = MagicMock()
        mock_user.doc.email = "test@example.com"
        mock_get_user.return_value = mock_user

        self.employee.get_current = MagicMock(return_value=Fixtures.employee)

        mock_emp_get_all.return_value = [MagicMock(
            name="EMP-009",
            employee_name="Test Employee",
            custom_time_model="Flextime account",
            grade="Standard",
            date_of_birth=datetime.date(1990, 1, 1),
            date_of_joining=datetime.date(2020, 1, 1)
        )]
        mock_checkin_get_all.return_value = []  # No checkin events

        status = self.service.get_current_status()
        self.assertEqual(State.OUT, status.state)

    def test_get_current_break(self):
        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.data.get = MagicMock(return_value=CheckinList([
            CheckinEvent("E001", datetime.datetime.now(), True, False),
            CheckinEvent("E002", datetime.datetime.now(), False, True),
        ]))

        self.assertEqual(State.BREAK, self.service.get_current_status().state)

    def test_get_current_work(self):
        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.data.get = MagicMock(return_value=CheckinList([
            CheckinEvent("E001", datetime.datetime.now(), True, False),
        ]))

        self.assertEqual(State.IN, self.service.get_current_status().state)

    def test_get_current_out(self):
        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.data.get = MagicMock(return_value=CheckinList([
            CheckinEvent("E001", datetime.datetime.now(), True, False),
            CheckinEvent("E002", datetime.datetime.now(), False, False),
        ]))

        self.assertEqual(State.OUT, self.service.get_current_status().state)

    def test_get_current_had_break_false(self):
        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.data.get = MagicMock(return_value=CheckinList([
            CheckinEvent("E001", datetime.datetime.now(), True, False),
            CheckinEvent("E002", datetime.datetime.now(), False, False),
        ]))

        self.assertFalse(self.service.get_current_status().had_break)

    def test_get_current_had_break_true(self):
        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.data.get = MagicMock(return_value=CheckinList([
            CheckinEvent("E001", datetime.datetime.now(), True, False),
            CheckinEvent("E002", datetime.datetime.now(), False, True),
            CheckinEvent("E003", datetime.datetime.now(), True, False),
            CheckinEvent("E004", datetime.datetime.now(), False, False),
        ]))

        self.assertTrue(self.service.get_current_status().had_break)

    def test_checkin_employee_not_found(self):
        self.employee.get_current = MagicMock(return_value=None)
        self.assertRaises(RuntimeError, self.service.checkin, Action.START_WORK)

    @patch('hr_time.api.employee.repository.frappe.get_user')
    @patch('hr_time.api.check_in.repository.frappe.get_all')
    @patch('hr_time.api.employee.repository.frappe.get_all')
    def test_checkin_start_of_work(self, mock_emp_get_all, mock_checkin_get_all, mock_get_user):
        # Mock frappe.get_user()
        mock_user = MagicMock()
        mock_user.doc.email = "test@example.com"
        mock_get_user.return_value = mock_user

        # Mock the get_current method directly on the instance
        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        mock_emp_get_all.return_value = [MagicMock(name="EMP-009")]
        mock_checkin_get_all.return_value = []  # No existing checkins

        with patch('hr_time.api.check_in.repository.frappe.new_doc') as mock_new_doc:
            mock_doc = MagicMock()
            mock_new_doc.return_value = mock_doc
            self.service.checkin(Action.START_WORK)
            mock_new_doc.assert_called_once()
            mock_doc.save.assert_called_once()

    def test_checkin_break(self):
        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.data.checkin = MagicMock()
        self.service.checkin(Action.BREAK)

        self.assertEqual("EMP-009", self.data.checkin.call_args.args[0])
        # Compare with enum, not string
        self.assertEqual(LogType.OUT, self.data.checkin.call_args.args[1])
        self.assertTrue(self.data.checkin.call_args.args[2])

    def test_checkin_endOfWork(self):
        self.employee.get_current = MagicMock(return_value=Fixtures.employee)
        self.data.checkin = MagicMock()

        self.service.checkin(Action.END_WORK)

        self.assertEqual("EMP-009", self.data.checkin.call_args.args[0])
        # Compare with enum, not string
        self.assertEqual(LogType.OUT, self.data.checkin.call_args.args[1])
        self.assertFalse(self.data.checkin.call_args.args[2])
