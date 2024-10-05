from typing import Optional
import frappe
from hr_time.api.employee.repository import EmployeeRepository
try:
    from frappe import _
except ImportError:
    # Fallback if frappe._ isn't available (for tests)
    def _(text): return text


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
        frappe.throw(_("No employee ID found for the current user : Please ensure you are logged in."),
                     frappe.DoesNotExistError)
    else:
        return employee.id
