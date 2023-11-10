import datetime

import frappe

from hr_time.api.check_in.service import CheckinService, State, Action
from hr_time.api.employee.repository import EmployeeRepository, TimeModel
from hr_time.api.flextime.processing import FlexTimeProcessingService
from hr_time.api.flextime.stats import FlextimeStatisticsService


@frappe.whitelist()
def generate_daily_flextime_status():
    return FlexTimeProcessingService.prod().process_daily_status()


@frappe.whitelist()
def render_number_card_flextime_time_balance():
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
def render_number_card_checkin_status():
    return frappe.render_template("templates/number_card/checkin_status.html", get_checkin_status_template_data())


@frappe.whitelist()
def render_navbar_checkin_status():
    employee = EmployeeRepository().get_current()

    if employee is None:
        return ""

    if employee.time_model is not TimeModel.Flextime:
        return ""

    return frappe.render_template("templates/navbar/checkin_status.html",
                                  CheckinService.prod().get_current_status().state.render())


@frappe.whitelist()
def get_easy_checkin_options():
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
def submit_easy_checkin(action: str):
    match action:
        case "Start of work":
            CheckinService.prod().checkin(Action.startOfWork)
        case "Break":
            CheckinService.prod().checkin(Action.breakTime)
        case "End of work":
            CheckinService.prod().checkin(Action.endOfWork)
        case _:
            raise ValueError("Unknown action given")


def get_checkin_status_template_data() -> dict:
    data = CheckinService.prod().get_current_status().state.render()
    duration = str(datetime.timedelta(seconds=FlextimeStatisticsService.prod().get_current_duration())).split(":")

    data["duration"] = duration[0] + ':' + duration[1]
    return data
