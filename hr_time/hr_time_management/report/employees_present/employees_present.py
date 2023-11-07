# Copyright (c) 2023, AtlasAero GmbH and contributors
# For license information, please see license.txt
import datetime

import frappe

from hr_time.api.check_in.report import CheckinReportService
from hr_time.api.check_in.service import State


def execute(filters=None):
    columns = [
        {
            'fieldname': 'employee',
            'label': frappe._('Employee'),
            'fieldtype': 'data',
            'options': ''
        },
        {
            'fieldname': 'employee_name',
            'label': frappe._('Employee name'),
            'fieldtype': 'data',
            'options': ''
        },
        {
            'fieldname': 'status',
            'label': frappe._('Status'),
            'fieldtype': 'data',
            'options': ''
        },
        {
            'fieldname': 'status_since',
            'label': frappe._('Current status since'),
            'fieldtype': 'time',
            'options': ''
        },
        {
            'fieldname': 'work_start_today',
            'label': frappe._('Work start today'),
            'fieldtype': 'time',
            'options': ''
        }
    ]

    data = []

    filter_status = None

    if filters is not None and "status" in filters:
        if filters["status"] == "Break":
            filter_status = State.Break
        elif filters["status"] == "Work":
            filter_status = State.In

    for row in CheckinReportService.prod().get_present(filter_status=filter_status):
        data.append(row.render())

    return columns, data
