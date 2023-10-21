import frappe

from hr_time.api.flextime.processing import FlexTimeProcessingService


@frappe.whitelist()
def generate_daily_flextime_status():
    return FlexTimeProcessingService.prod().process_daily_status()
