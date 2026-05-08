import frappe
from frappe import _

from hr_time.api.employee.repository import EmployeeRepository
from hr_time.api.shared.constants.messages import Messages
from hr_time.api.shared.utils.frappe_utils import FrappeUtils


@frappe.whitelist()
def get_current_employee_id() -> str:
    """
    Retrieves the current employee's ID based on the logged-in user.

    Returns:
        str: Employee ID (e.g., "HR-EMP-00003")
    """
    try:
        employee = EmployeeRepository().get_current()
        if employee is None:
            FrappeUtils.throw_error_msg(_(Messages.Employee.NOT_FOUND_EMPLOYEE_ID))
            # frappe.throw(_("No employee found for current user"))
        return employee.id  # Return raw string, not wrapped
    except Exception as e:
        frappe.log_error(f"Error in get_current_employee_id: {str(e)}")
        FrappeUtils.throw_error_msg(_(Messages.Common.ERR_UNKNOWN))


@frappe.whitelist()
def get_current_employee() -> dict:
    """
    Retrieves the current employee's full document as a dict.

    Returns:
        dict: Employee document as dictionary
    """
    try:
        employee = EmployeeRepository().get_current()
        if employee is None:
            FrappeUtils.throw_error_msg(_(Messages.Employee.NOT_FOUND_EMPLOYEE))
        return employee.to_dict()
    except Exception as e:
        frappe.log_error(f"Error in get_current_employee: {str(e)}")
        FrappeUtils.throw_error_msg(_(Messages.Common.ERR_UNKNOWN))
