import frappe

from hr_time.api.check_in.report import CheckinReportService
from hr_time.api.check_in.service import CheckinService


@frappe.whitelist()
def render_number_card_employees_present():
    return frappe.render_template("templates/number_card/employees_present.html", {
        "count": len(CheckinReportService.prod().get_present()),
        "button_label": frappe._("Show list")
    })

@frappe.whitelist() 
def has_open_session(employee_id: str = None) -> bool:
    """Check-in API - actual implementation"""
    if not employee_id:
        from hr_time.api.employee.api import get_current_employee_id
        employee_id = get_current_employee_id()
    
    from hr_time.api.check_in.service import CheckinService
    return CheckinService.prod().has_open_session(employee_id)