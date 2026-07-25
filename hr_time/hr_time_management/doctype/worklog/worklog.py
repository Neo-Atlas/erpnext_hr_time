# Copyright (c) 2024, AtlasAero GmbH and contributors
# For license information, please see license.txt

from datetime import datetime

import frappe
from frappe import _
from frappe.model.document import Document

from hr_time.api.shared.utils.frappe_utils import FrappeUtils
from hr_time.api.shared.constants.messages import Messages
from hr_time.api.worklog.service import WorklogService
from hr_time.api.employee.repository import EmployeeRepository
from hr_time.api.worklog.application.worklog_app_service import WorklogAppService


class Worklog(Document):
    def before_save(self):
        """Set defaults and calculate totals before save"""
        if not self.log_time:
            self.log_time = datetime.now()

        if not self.employee:
            self.set_employee_from_user()

        app = WorklogAppService()
        app.before_save_worklog(doc=self)

    def on_update(self):
        if self.time_saved > 0:
            # delegate to service to handle timesheet lookup + processing
            service = WorklogService.prod()
            service.process_worklog_save(self)

    def set_employee_from_user(self):
        """Set employee field from current user"""
        employee_name = EmployeeRepository.get_name_by_user_id(frappe.session.user)
        if employee_name:
            self.employee = employee_name
        else:
            FrappeUtils.throw_error_msg(Messages.Employee.NOT_FOUND_EMPLOYEE)
