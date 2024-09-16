import frappe
from hr_time.api.employee.service import EmployeeService


@frappe.whitelist()
def get_current_employee_id():
    return EmployeeService.prod().get_current_employee_id()
