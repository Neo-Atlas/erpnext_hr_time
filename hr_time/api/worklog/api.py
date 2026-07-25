from typing import Dict, Any
import traceback
import json

import frappe
from frappe import _


from hr_time.api.hr_settings.repository import HRSettingsRepository
from hr_time.api.employee.api import get_current_employee_id
from hr_time.api.shared.utils.response import Response
from hr_time.api.worklog.application.worklog_app_service import WorklogAppService, WORKLOG_STATE_COLORS


@frappe.whitelist()
def get_tolerance_minutes() -> int:
    """Get worklog tolerance from HR Settings"""
    return HRSettingsRepository.get_tolerance_minutes()


@frappe.whitelist()
def get_buffer_task():
    return HRSettingsRepository.get_buffer_task()


@frappe.whitelist()
def prepare_worklog_for_checkout(employee_id: str = None) -> Dict[str, Any]:
    """
    Prepare worklog data for checkout dialog
    Thin wrapper around WorklogService
    """
    if not employee_id:
        employee_id = get_current_employee_id()
    app = WorklogAppService()
    return app.prepare_for_checkout(employee_id)


def _render_overview_headline(state, total_hours: float, is_editable: bool) -> str:
    """Render the worklog overview headline HTML."""
    return frappe.render_template(
        "templates/worklog/worklog_overview_headline.html",
        {
            "state": state.value,
            "total_hours": round(total_hours, 2),
            "is_editable": is_editable,
            "_": frappe._
        }
    )


def _render_today_indicator(has_worklog_today: bool) -> str:
    """Render the indicator showing if a worklog exists for today."""
    return frappe.render_template(
        "templates/worklog/worklog_made_today_indicator.html",
        {
            "has_worklog": has_worklog_today,
            "_": frappe._
        }
    )


@frappe.whitelist()
def get_worklog_context(
    referred_worklog_name: str = None, employee_id: str = None, is_dialog_call: bool = False
) -> dict:
    """Get context for worklog - is it today's? has open session? on break?"""

    employee_id = employee_id or get_current_employee_id()
    app = WorklogAppService()
    context = app.get_worklog_context(employee_id, referred_worklog_name, is_dialog_call)

    return {
        "worklog_state": context["state"].value,
        "headline_color": WORKLOG_STATE_COLORS.get(context["state"], "red"),
        "is_todays_worklog": context["is_todays"],
        "is_new_doc": context["is_new_doc"],
        "is_read_only": not context["is_editable"],
        "has_open_session": context["has_open_session"],
        "on_break": context["on_break"],
        "today_worklog_name": context["today_worklog_name"],
        "worklog_total_hours": context["worklog_total_hours"],
        "tolerance_minutes": context["tolerance_minutes"],
        "worklog_overview_headline": _render_overview_headline(
            context["state"],
            context["worklog_total_hours"],
            context["is_editable"]
        ),
        "worklog_status_today_html": _render_today_indicator(
            bool(context["today_worklog_name"])
        ),
    }


@frappe.whitelist()
def save_and_checkout(
    worklog_name: str = None,
    employee_id: str = None,
    worklog_data=None,
    current_total=0
) -> dict:
    """Save worklog and perform checkout in one action"""
    try:
        # Parsing worklog_data
        if worklog_data and isinstance(worklog_data, str):
            worklog_data = json.loads(worklog_data)
        else:
            worklog_data = worklog_data or {}

        # make sure current_total is a float
        if current_total is None or current_total == '':
            current_total = 0
        current_total = float(current_total)

        # Delegate saving worklog and checkout to App service
        app = WorklogAppService()
        saved_name, checkout_performed = app.save_and_checkout(
            worklog_name=worklog_name,
            employee_id=employee_id,
            worklog_data=worklog_data,
            current_total=current_total
        )

        return Response.success(
            _("Worklog saved successfully" + (" and checked out." if checkout_performed else "")),
            {"worklog": saved_name}
        ).to_dict()

    except json.JSONDecodeError as e:
        return Response.error(f"Invalid JSON: {str(e)}").to_dict()

    except Exception as e:
        frappe.db.rollback()
        traceback.print_exc()
        return Response.error(str(e)).to_dict()
