import unittest
from unittest.mock import patch, MagicMock
import frappe
from frappe import _
from hr_time.api.employee.api import get_current_employee_id
from hr_time.api.shared.constants.messages import Messages


class TestGetCurrentEmployeeID(unittest.TestCase):

    @patch('hr_time.api.employee.api.EmployeeRepository')
    @patch('frappe.get_user')
    def test_get_current_employee_id_success(self, mock_get_user, mock_employee_repo):
        # Arrange
        mock_user = MagicMock()
        mock_user.doc.email = "test@example.com"
        mock_get_user.return_value = mock_user
        employee = MagicMock()
        employee.id = "EMP001"
        mock_employee_repo.return_value.get_current.return_value = employee

        # Act
        result = get_current_employee_id()

        # Assert
        self.assertEqual(result, "EMP001")
        mock_employee_repo.assert_called_once()

    @patch('hr_time.api.employee.api.EmployeeRepository')
    @patch('frappe.get_user')
    # Mocking the frappe.throw directly
    @patch('frappe.throw', side_effect=frappe.DoesNotExistError(Messages.Employee.NOT_FOUND_EMPLOYEE_ID))
    def test_get_current_employee_id_no_employee(self, mock_throw, mock_get_user, mock_employee_repo):
        # Arrange
        mock_user = MagicMock()
        mock_user.doc.email = "test@example.com"
        mock_get_user.return_value = mock_user
        mock_employee_repo.return_value.get_current.return_value = None

        # Act & Assert
        with self.assertRaises(frappe.DoesNotExistError):
            get_current_employee_id()

        mock_throw.assert_called_once_with(
            Messages.Employee.NOT_FOUND_EMPLOYEE_ID,
            frappe.DoesNotExistError
        )

        mock_employee_repo.assert_called_once()
        mock_employee_repo.return_value.get_current.assert_called_once()
