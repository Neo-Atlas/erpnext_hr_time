from typing import Optional

import frappe

from hr_time.api.worklog.infrastructure.timesheet.values import TimesheetLog


class TimesheetRepository:
    DOCTYPE_NAME = "Timesheet"

    @staticmethod
    def get_todays_timesheet(employee_id: str) -> Optional[str]:
        """Get today's timesheet name for an employee"""
        return frappe.db.get_value(
            TimesheetRepository.DOCTYPE_NAME,
            {
                "employee": employee_id,
                "start_date": frappe.utils.nowdate()
            },
            "name"
        )

    @staticmethod
    def get_by_name(timesheet_name: str):
        """Get timesheet document by name"""
        if not frappe.db.exists(TimesheetRepository.DOCTYPE_NAME, timesheet_name):
            return None
        return frappe.get_doc(TimesheetRepository.DOCTYPE_NAME, timesheet_name)

    @staticmethod
    def cancel(timesheet_name: str) -> bool:
        """Cancel a timesheet by name (with admin privileges)"""
        original_user = frappe.session.user
        try:
            frappe.set_user("Administrator")

            if not frappe.db.exists(TimesheetRepository.DOCTYPE_NAME, timesheet_name):
                return False
            doc = frappe.get_doc(TimesheetRepository.DOCTYPE_NAME, timesheet_name)
            if doc.docstatus == 1:
                doc.cancel()
                return True
            return False
        finally:
            frappe.set_user(original_user)

    @staticmethod
    def create(employee_id: str, time_logs: list[TimesheetLog]) -> str:
        """Create a new timesheet with TimesheetLog value objects"""
        timesheet = frappe.new_doc(TimesheetRepository.DOCTYPE_NAME)
        timesheet.employee = employee_id

        for log in time_logs:
            timesheet.append("time_logs", log.to_dict())

        timesheet.save()
        timesheet.submit()
        return timesheet
