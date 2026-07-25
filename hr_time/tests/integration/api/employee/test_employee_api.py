import unittest
from unittest.mock import patch, MagicMock

import frappe

from hr_time.api.employee.api import get_current_employee_id, get_current_employee
from hr_time.api.shared.constants.messages import Messages


class TestGetCurrentEmployeeId(unittest.TestCase):
    """Essential tests for get_current_employee_id API"""

    @patch('hr_time.api.employee.api.EmployeeRepository')
    def test_returns_employee_id_when_employee_exists(self, MockEmployeeRepo):
        """Should return employee ID when employee record exists"""
        # Arrange
        mock_repo = MockEmployeeRepo.return_value
        mock_employee = MagicMock()
        mock_employee.id = "HR-EMP-001"
        mock_repo.get_current.return_value = mock_employee

        # Act
        result = get_current_employee_id()

        # Assert
        self.assertEqual("HR-EMP-001", result)
        mock_repo.get_current.assert_called_once()

    @patch('hr_time.api.employee.api.EmployeeRepository')
    def test_returns_none_when_no_employee(self, MockEmployeeRepo):
        """Should return None when no employee record exists (admin user)"""
        # Arrange
        mock_repo = MockEmployeeRepo.return_value
        mock_repo.get_current.return_value = None

        # Act
        result = get_current_employee_id()

        # Assert
        self.assertIsNone(result)
        mock_repo.get_current.assert_called_once()

    @patch('hr_time.api.employee.api.EmployeeRepository')
    @patch('hr_time.api.employee.api.frappe.log_error')
    def test_returns_none_and_logs_error_on_exception(self, mock_log_error, MockEmployeeRepo):
        """Should return None and log error when exception occurs"""
        # Arrange
        mock_repo = MockEmployeeRepo.return_value
        mock_repo.get_current.side_effect = Exception("Database error")

        # Act
        result = get_current_employee_id()

        # Assert
        self.assertIsNone(result)
        mock_log_error.assert_called_once()
        self.assertIn("Error in get_current_employee_id", mock_log_error.call_args[0][0])


class TestGetCurrentEmployee(unittest.TestCase):
    """Essential tests for get_current_employee API"""

    @patch('hr_time.api.employee.api.EmployeeRepository')
    def test_returns_employee_dict_when_employee_exists(self, MockEmployeeRepo):
        """Should return employee dictionary when employee exists"""
        # Arrange
        mock_repo = MockEmployeeRepo.return_value
        mock_employee = MagicMock()
        mock_employee.to_dict.return_value = {
            "id": "HR-EMP-001",
            "full_name": "John Doe",
            "time_model": "Flextime",
            "grade": "Standard",
            "date_of_birth": "1990-01-01",
            "date_of_joining": "2020-01-01"
        }
        mock_repo.get_current.return_value = mock_employee

        # Act
        result = get_current_employee()

        # Assert
        self.assertEqual("HR-EMP-001", result["id"])
        self.assertEqual("John Doe", result["full_name"])
        mock_repo.get_current.assert_called_once()
        mock_employee.to_dict.assert_called_once()

    @patch('hr_time.api.employee.api.EmployeeRepository')
    @patch('hr_time.api.employee.api.FrappeUtils.throw_error_msg')
    def test_throws_error_when_no_employee(self, mock_throw_error, MockEmployeeRepo):
        """Should throw NOT_FOUND error when no employee record exists"""
        # Arrange
        mock_repo = MockEmployeeRepo.return_value
        mock_repo.get_current.return_value = None

        mock_throw_error.side_effect = frappe.DoesNotExistError

        # Act
        with self.assertRaises(frappe.DoesNotExistError):
            get_current_employee()

        # Assert - now only called once (no double throw)
        mock_throw_error.assert_called_once()
        # Verify the error message is NOT_FOUND_EMPLOYEE
        self.assertEqual(
            Messages.Employee.NOT_FOUND_EMPLOYEE,
            mock_throw_error.call_args[0][0]
        )
