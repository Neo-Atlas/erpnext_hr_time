from typing import Any

import frappe
from frappe import _

from hr_time.api.employee.repository import EmployeeRepository
from hr_time.api.shared.constants.messages import Messages
from hr_time.api.shared.utils.frappe_utils import FrappeUtils


@frappe.whitelist()
def get_current_employee_id() -> dict[str, Any]:
    """
    Retrieves the current employee's ID based on the logged-in user.

    Returns:
        str: Employee ID (e.g., "HR-EMP-00003") or None
    """
    try:
        repo = EmployeeRepository()
        employee = repo.get_current()
        return employee.id if employee else None
    except Exception as e:
        frappe.log_error(f"Error in get_current_employee_id: {str(e)}")
        return None


@frappe.whitelist()
def get_current_employee() -> dict[str, Any]:
    """
    Retrieves the current employee's full document as a dict.

    Returns:
        dict: Employee document as dictionary
    """
    repo = EmployeeRepository()
    employee = repo.get_current()

    if employee is None:
        FrappeUtils.throw_error_msg(
            _(Messages.Employee.NOT_FOUND_EMPLOYEE),
            frappe.DoesNotExistError
        )
    return employee.to_dict()
