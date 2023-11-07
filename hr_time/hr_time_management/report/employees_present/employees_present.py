# Copyright (c) 2023, AtlasAero GmbH and contributors
# For license information, please see license.txt
import datetime

import frappe

from hr_time.api.check_in.report import CheckinReportService
from hr_time.api.check_in.service import State


def execute(filters=None):
    data = []

    filter_status = None

    if filters is not None and "status" in filters:
        if filters["status"] == "Break":
            filter_status = State.Break
        elif filters["status"] == "Work":
            filter_status = State.In

    max_name_length = 0

    for row in CheckinReportService.prod().get_present(filter_status=filter_status):
        row_rendered = row.render()
        data.append(row_rendered)

        if len(row_rendered['employee_name']) > max_name_length:
            max_name_length = len(row_rendered['employee_name'])

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
            'options': '',
            'width': max_name_length * 8
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

    return columns, data
