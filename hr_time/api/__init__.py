import frappe

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("hr_time", allow_site=True, file_count=50)