import frappe

from hr_time.api.check_in.service import CheckinService, State, Action
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
        "color": "" if balance.balance_minutes == 0 else ("positive" if balance.balance_minutes > 0 else "negative")
    })


@frappe.whitelist()
def render_number_card_checkin_status():
    match CheckinService.prod().get_current_status().state:
        case State.In:
            label = "Checked in"
            status = "work"
            icon = "check"
        case State.Out:
            label = "Checked out"
            status = "out"
            icon = "remove"
        case State.Break:
            label = "Break"
            status = "break"
            icon = "coffee"
        case _:
            label = "Unknown"
            status = "out"
            icon = "question"

    return frappe.render_template("templates/number_card/checkin_status.html", {
        "label": frappe._(label),
        "status": status,
        "icon": icon
    })


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

