import frappe

from hr_time.api.check_in.report import CheckinReportService


@frappe.whitelist()
def render_number_card_employees_present():
    return frappe.render_template("templates/number_card/employees_present.html", {
        "count": len(CheckinReportService.prod().get_present()),
        "button_label": frappe._("Show list")
    })
