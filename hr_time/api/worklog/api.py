import frappe
import datetime
from hr_time.api.utils.clock import Clock
from hr_time.api.worklog.service import WorklogService


@frappe.whitelist()
def get_all_worklogs():
    # Call the service to fetch worklogs
    return WorklogService.prod().get_all_worklogs()


@frappe.whitelist()
def get_worklogs_for_employee(employee_id):
    return WorklogService.prod().get_worklogs_for_employee(employee_id)


@frappe.whitelist()
def has_employee_made_worklogs_today(employee_id):
    return WorklogService.prod().check_if_employee_has_worklogs_today(employee_id)


@frappe.whitelist()
def employee_worklogs_today(employee_id):
    today = datetime.date.today()
    return WorklogService.prod().get_worklogs_for_employee_on_date(employee_id, today)


@frappe.whitelist()
def get_worklogs_table_html(employee_id, date):
    worklogs = WorklogService.prod().get_worklogs_for_employee_on_date(employee_id, date)

    # Table DOM formatting
    worklog_html = """
    <label class="control-label">Daily Worklogs</label>
    <table class="table table-bordered table-striped">
        <thead>
            <tr>
                <th>Log ID</th>
                <th>Log Time</th>
                <th>Task Description</th>
                <th>Task</th>
            </tr>
        </thead>
        <tbody>
    """

    # Add table rows with data
    for worklog in worklogs:
        log_id = worklog.get("name", "No ID")
        log_time = worklog.get("log_time", "No log time")
        if log_time is not "No log time":
            log_time = Clock.format_time_am_pm(worklog.get("log_time"))
        task_desc = worklog.get("task_desc", "No task description")
        task = worklog.get("task", "No task")

        # Create each row with fetched data
        worklog_html += f"""
            <tr>
                <td>{log_id}</td>
                <td>{log_time}</td>
                <td>{task_desc}</td>
                <td>{task}</td>
            </tr>
        """

    worklog_html += """
        </tbody>
    </table>
    """

    return worklog_html
