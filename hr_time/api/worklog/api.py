import frappe
# from frappe import _
from hr_time.api.worklog.service import WorklogService
try:
    from frappe import _
except ImportError:
    # Fallback if frappe._ isn't available (for tests)
    def _(text): return text


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
def create_worklog(employee_id, worklog_text, task=None) -> dict:
    """
    Creates a new worklog for the given employee.

    Args:
        employee_id (str): The ID of the employee creating the worklog.
        worklog_text (str): The content or description of the worklog.
        task (Optional[str]): The task associated with the worklog (if any).

    Returns:
        dict: The response from the WorklogService after creating the worklog, which may include
        information such as success status or the created worklog details.
    """
    return WorklogService.prod().create_worklog(employee_id, worklog_text, task)


@frappe.whitelist()
def render_worklog_header() -> str:
    """
    Renders the HTML template for the worklog textbox's header (label and to full-form page button).

    Returns:
        str: The rendered HTML content for the worklog textbox's header.
    """
    context = {
        "_": frappe._  # Include the translation helper
    }
    return frappe.render_template("templates/worklog/worklog_textbox.html", context)
