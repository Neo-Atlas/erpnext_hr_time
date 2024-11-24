import frappe
from frappe import _
from hr_time.api.worklog.service import WorklogService


@frappe.whitelist()
def has_employee_made_worklogs_today(employee_id) -> bool:
    """
    Checks if an employee has made any worklogs today.

    Args:
        employee_id (str): The ID of the employee.

    Returns:
        bool: True if the employee has made worklogs today, False otherwise.
    """
    return WorklogService.prod().check_if_employee_has_worklogs_today(employee_id)


@frappe.whitelist()
def create_worklog_now(employee_id, worklog_text, task=None, ticket_link=None) -> dict:
    """
    Creates a new worklog for the given employee.

    Args:
        employee_id (str): The ID of the employee creating the worklog.
        worklog_text (str): The content or description of the worklog.
        task (Optional[str]): The task associated with the worklog (if any).
        ticket_link (Optional[str]): The external reference URL associated with the worklog (if any).

    Returns:
        dict:
            The response from the WorklogService as JSON string after creating the worklog
            which include information such as success status, message and (optionally) data.
    """
    return WorklogService.prod().create_worklog_now(employee_id, worklog_text, task, ticket_link).to_json()


@frappe.whitelist()
def render_worklog_header() -> str:
    """
    Renders the HTML template for the worklog textbox's header (label and worklog-status-alert).

    Returns:
        str: The rendered HTML content for the worklog textbox's header.
    """
    context = {
        "_": frappe._  # Including the translation helper
    }
    return frappe.render_template("templates/worklog/worklog_textbox_header.html", context)


@frappe.whitelist()
def render_worklog_full_form_link() -> str:
    """
    Renders the HTML template for link to the full form of worklog entry ("Enter complete detail button").

    Returns:
        str: The rendered HTML content for the link's template.
    """
    context = {
        "_": frappe._  # Including the translation helper
    }
    return frappe.render_template("templates/worklog/worklog_btn_full_page.html", context)
