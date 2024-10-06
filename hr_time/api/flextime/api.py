import datetime
import frappe
from frappe import _
from typing import Union
from hr_time.api.check_in.service import CheckinService, State, Action
from hr_time.api.employee.repository import EmployeeRepository, TimeModel
from hr_time.api.flextime.processing import FlexTimeProcessingService
from hr_time.api.flextime.stats import FlextimeStatisticsService
from hr_time.api.worklog.service import WorklogService
from hr_time.api.shared.utils.frappe_utils import warn_user
from hr_time.api.shared.constants.messages import Messages


@frappe.whitelist()
def generate_daily_flextime_status() -> None:
    """
    Triggers the daily flex time status processing.
    """
    return FlexTimeProcessingService.prod().process_daily_status()


@frappe.whitelist()
def render_number_card_flextime_time_balance() -> str:
    """
    Renders the HTML template for the flex time account balance number card.

    Returns:
        str: The rendered HTML content for the flex time balance number card.
    """
    balance = FlextimeStatisticsService.prod().get_balance()

    return frappe.render_template("templates/number_card/flextime_account_balance.html", {
        "time_balance_hours": frappe._('{0} hour(s)').format(balance.balance_hours),
        "time_balance_minutes": frappe._('{0} minute(s)').format(balance.balance_minutes),
        "trend_value": "{}H, {}m ({} %)".format(abs(balance.trend_hours), abs(balance.trend_minutes),
                                                round(balance.trend_percent * 100)),
        "trend_meta": frappe._("Within last month"),
        "is_trend_positive": balance.trend_percent > 0,
        "color": "" if balance.is_zero() else ("positive" if balance.balance_minutes > 0 else "negative")
    })


@frappe.whitelist()
def render_number_card_checkin_status() -> str:
    """
    Renders the HTML template for the check-in status number card.

    Returns:
        str: The rendered HTML content for the check-in status number card.
    """
    return frappe.render_template("templates/number_card/checkin_status.html", get_checkin_status_template_data())


@frappe.whitelist()
def render_navbar_checkin_status() -> str:
    """
    Renders the check-in status in the navigation bar.

    Returns:
        str: The rendered HTML content for the check-in status in the navigation bar,
            or an empty string if conditions are not met.
    """
    employee = EmployeeRepository().get_current()

    if employee is None:
        return ""

    if employee.time_model is not TimeModel.Flextime:
        return ""

    return frappe.render_template("templates/navbar/checkin_status.html", get_checkin_status_template_data())


@frappe.whitelist()
def get_easy_checkin_options() -> dict:
    """
    Retrieves available check-in options based on the employee's current status.

    Returns:
        dict: containing the available check-in options and the default option.
    """
    status = CheckinService.prod().get_current_status()

    match status.state:
        case State.In:
            options = ["Break", "End of work"]
            default = "End of work" if status.had_break else "Break"
        case State.Out | State.Break:
            options = ["Start of work"]
            default = "Start of work"
        case _:
            options = ["Start of work", "Break", "End of work"]
            default = ""

    return {
        "options": options,
        "default": default
    }


@frappe.whitelist()
def submit_easy_checkin(action: str) -> Union[None, dict]:
    """
    Submits the employee's check-in action (e.g., start work, break, end work)
    and triggers appropriate checkin processes for the employee. If "End of work"
    is selected and no worklogs are present for the day, a warning is displayed.

    Args:
        action (str): The selected check-in action ("Start of work", "Break", "End of work").

    Returns:
        Union[None, dict]: Returns None when the action is successfully processed.
                           Returns a dict with an error message if "End of work"
                           is selected and no worklogs exist for the day.
    """
    employee = EmployeeRepository().get_current()
    match action:
        case "Start of work":
            CheckinService.prod().checkin(Action.startOfWork)
        case "Break":
            CheckinService.prod().checkin(Action.breakTime)
        case "End of work":
            # Check if the employee has any worklogs
            if not WorklogService.prod().check_if_employee_has_worklogs_today(employee.id):
                return {
                    'status': 'error',
                    'message': Messages.Checkin.FAILED_CHECKOUT_DUE_TO_NO_WORKLOGS
                }
            CheckinService.prod().checkin(Action.endOfWork)
        case _:
            warn_user(Messages.Common.UNKNOWN_ACTION)


def get_checkin_status_template_data() -> dict:
    """
    Retrieves the template data for the check-in status including duration.

    Returns:
        dict: A dictionary containing the check-in status label and formatted duration.
    """
    data = CheckinService.prod().get_current_status().state.render()
    duration = str(datetime.timedelta(seconds=FlextimeStatisticsService.prod().get_current_duration())).split(":")
    data["label"] = data["label"] + ' (' + duration[0] + ':' + duration[1] + ')'
    return data
