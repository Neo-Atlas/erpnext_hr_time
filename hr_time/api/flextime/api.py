import datetime
from typing import Union

import frappe
from frappe import _

from hr_time.api.check_in.report import CheckinReportService
from hr_time.api.check_in.service import CheckinService, Action, State
from hr_time.api.check_in.display_service import CheckinDisplayService
from hr_time.api.employee.repository import EmployeeRepository, TimeModel
from hr_time.api.flextime.processing import FlexTimeProcessingService
from hr_time.api.flextime.stats import FlextimeStatisticsService
from hr_time.api.worklog.service import WorklogService
from hr_time.api.shared.constants.messages import Messages
from hr_time.api.shared.utils.response import Response
from hr_time.api.employee.api import get_current_employee_id


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
    return CheckinService.prod().get_available_actions()


@frappe.whitelist()
def submit_easy_checkin(action: str) -> Union[None, dict]:
    """
    Submits the employee's check-in action (e.g., start work, break, end work)
    and triggers appropriate checkin processes for the employee. If "End of work"
    is selected and no worklogs are present for the day, a warning is displayed.

    Args:
        action (str): The selected check-in action ("Start of work", "Break", "End of work").

    Returns:
        Response object with success/error status and appropriate message
    """
    try:
        employee = EmployeeRepository().get_current()
        if employee is None:
            return Response.error(Messages.Employee.NOT_FOUND_EMPLOYEE).to_dict()

        action_enum = Action.from_string(action)
        if action_enum is None:
            return Response.error(Messages.Common.UNKNOWN_ACTION).to_dict()

        # Handle 'End of Work' special case
        if action_enum == Action.END_WORK:
            if not WorklogService.prod().check_if_employee_has_worklogs_today(employee.id):
                return Response.error(Messages.Checkin.FAILED_CHECKOUT_DUE_TO_NO_WORKLOGS).to_dict()

        # Convert to Action enum and execute
        CheckinService.prod().checkin(action_enum)

        message_map = {
            Action.START_WORK: Messages.Checkin.SUCCESS_CHECKIN,
            Action.RESUME_WORK: Messages.Checkin.SUCCESS_RESUME,
            Action.BREAK: Messages.Checkin.SUCCESS_BREAK,
            Action.END_WORK: Messages.Checkin.SUCCESS_CHECKOUT,
        }

        return Response.success(message_map.get(action_enum, Messages.Checkin.SUCCESS_CHECKIN)).to_dict()

    except Exception as e:
        frappe.log_error(f"Error in submit_easy_checkin: {str(e)}")
        return Response.error(Messages.Common.ERR_UNKNOWN).to_dict()


def get_checkin_status_template_data() -> dict:
    """
    Retrieves the template data for the check-in status including duration.

    Returns:
        dict: A dictionary containing the check-in status label and formatted duration.
    """
    status = CheckinService.prod().get_current_status()
    data = CheckinDisplayService.get_display_data(status.state)
    duration = str(datetime.timedelta(seconds=FlextimeStatisticsService.prod().get_current_duration())).split(":")
    data["label"] = data["label"] + ' (' + duration[0] + ':' + duration[1] + ')'
    return data


@frappe.whitelist()
def get_employees_present_count():
    """Get count of present employees (without HTML)"""
    return {"count": len(CheckinReportService.prod().get_present())}


@frappe.whitelist()
def get_checkin_status_data(employee_id: str = None):
    """Get checkin status data for realtime updates (without HTML)"""
    if not employee_id:
        employee_id = get_current_employee_id()

    status = CheckinService.prod().get_current_status()
    render_data = CheckinDisplayService.get_display_data(status.state)

    # Get duration (reuse existing logic)
    duration = str(datetime.timedelta(seconds=FlextimeStatisticsService.prod().get_current_duration())).split(":")
    duration_str = duration[0] + ':' + duration[1]

    return {
        "status": render_data["status"],
        "icon": render_data["icon"],
        "label": render_data["label"],
        "label_with_duration": f"{render_data['label']} ({duration_str})"
    }


@frappe.whitelist()
def get_flextime_balance_data():
    """Get flextime balance data for realtime updates (without HTML)"""
    balance = FlextimeStatisticsService.prod().get_balance()

    return {
        "balance_hours": balance.balance_hours,
        "balance_minutes": balance.balance_minutes,
        "hours_display": frappe._('{0} hour(s)').format(balance.balance_hours),
        "minutes_display": frappe._('{0} minute(s)').format(balance.balance_minutes),
        "trend_hours": abs(balance.trend_hours),
        "trend_minutes": abs(balance.trend_minutes),
        "trend_percent": round(balance.trend_percent * 100),
        "trend_display": "{}H, {}m ({} %)".format(
            abs(balance.trend_hours),
            abs(balance.trend_minutes),
            round(balance.trend_percent * 100)
        ),
        "is_trend_positive": balance.trend_percent > 0,
        "color": "" if balance.is_zero() else ("positive" if balance.balance_minutes > 0 else "negative"),
        "is_zero": balance.is_zero()
    }


@frappe.whitelist()
def get_current_session_state():
    """
    Get current session's stats: status, total work and break times in seconds, and timestamp
    """
    employee_id = get_current_employee_id()
    checkin_service = CheckinService.prod()
    stats_service = FlextimeStatisticsService.prod()

    status_obj = checkin_service.get_current_status()
    state_map = {State.IN: "IN", State.BREAK: "BREAK", State.OUT: "OUT"}
    status_str = state_map.get(status_obj.state, "OUT")

    # collect total work and break seconds
    total_worked_seconds = stats_service.get_todays_worked_seconds(employee_id)
    total_break_seconds = stats_service.get_todays_break_seconds(employee_id)

    return {
        "status": status_str,
        "total_worked_seconds": total_worked_seconds,
        "total_break_seconds": total_break_seconds,
        "timestamp": datetime.datetime.now().isoformat()
    }
