# Copyright (c) 2024, AtlasAero GmbH and contributors
# For license information, please see license.txt

from datetime import datetime
import frappe
from frappe import _
from frappe.model.document import Document
from hr_time.api.shared.utils.frappe_utils import FrappeUtils
from hr_time.api.shared.constants.messages import Messages
from hr_time.api.worklog.service import WorklogService


class Worklog(Document):
    def before_save(self):
        """Set defaults and calculate totals before save"""
        print('999 before_save')
        if not self.log_time:
            self.log_time = datetime.now()

        if not self.employee:
            self.set_employee_from_user()

        # Calculate progress increment for each task
        self._calculate_progress_increments()

        # Validate and/or readjust time allocation and time saved
        validation = WorklogService.prod().validate_worklog_document(self)
        if not validation.get("valid"):
            frappe.throw(validation.get("message"))

    def on_update(self):
        if self.time_saved > 0 and self.docstatus == 0:
            print('BBBBB')
            today = frappe.utils.nowdate()
            print(today)
            print('self.employee')
            print(self.employee)

            existing_timesheet = frappe.db.get_value(
                "Timesheet",
                {
                    "employee": self.employee,
                    "start_date": today,
                    # "docstatus": 1
                },
                "name"
            )

            print('existing_timesheet3')
            print(existing_timesheet)

            # Let service handle both cases
            result = WorklogService.prod().process_worklog_save(
                self,
                timesheet_name=existing_timesheet  # Pass if exists, None if not
            )

            if result and self.timesheet:
                frappe.msgprint(_(f"Timesheet {self.timesheet} processed successfully"))

    def _calculate_progress_increments(self):
        """Calculate progress increment for each task row"""
        if not self.tasks_entry:
            return

        for row in self.tasks_entry:
            if row.task and row.time_spent:
                # Get estimated time if not already fetched
                if not row.expected_time:
                    row.expected_time = frappe.db.get_value(
                        "Task", row.task, "expected_time"
                    ) or 0

                # Calculate progress
                if row.expected_time and row.expected_time > 0:
                    increment = (row.time_spent / row.expected_time) * 100
                    row.progress_increment = min(increment, 100)
                else:
                    row.progress_increment = 0

    def _calculate_totals(self):
        """Calculate total allocated hours and unallocated hours"""
        total = 0
        for row in self.tasks_entry:
            total += float(row.time_spent or 0)

    def set_employee_from_user(self):
        """Set employee field from current user"""
        user_id = frappe.session.user
        employee = frappe.get_value("Employee", {"user_id": user_id}, "name")
        
        if employee:
            self.employee = employee
        else:
            FrappeUtils.throw_error_msg(Messages.Employee.NOT_FOUND_EMPLOYEE)