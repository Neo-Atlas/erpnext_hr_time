import frappe

from hr_time.api.check_in.service import CheckinService, CheckinStatus
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
    match CheckinService.prod().get_current_status():
        case CheckinStatus.In:
            label = "Checked in"
            status = "work"
            icon = "check"
        case CheckinStatus.Out:
            label = "Checked out"
            status = "out"
            icon = "remove"
        case CheckinStatus.Break:
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
