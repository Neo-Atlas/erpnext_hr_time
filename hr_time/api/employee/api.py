from typing import Optional
import frappe
from frappe import _
from hr_time.api.employee.repository import EmployeeRepository
from hr_time.api.shared.constants.messages import Messages
from hr_time.api.shared.utils.frappe_utils import FrappeUtils


@frappe.whitelist()
def get_current_employee_id() -> Optional[str]:
    """
    Retrieves the current employee's ID based on the logged-in user.

    Returns:
        Optional[str]: The ID of the current employee, or `None` if no employee is found.

    Raises:
        frappe.DoesNotExistError: If no employee is found for the current user.
    """
    employee = EmployeeRepository().get_current()
    if employee is None:
        FrappeUtils.throw_error_msg(Messages.Employee.NOT_FOUND_EMPLOYEE_ID, frappe.DoesNotExistError)
    else:
        return employee.id
