from typing import Dict, Any
from datetime import date
import traceback
import json

import frappe
from frappe import _

from hr_time.api.worklog.service import WorklogService
from hr_time.api.worklog.repository import WorklogRepository
from hr_time.api.hr_settings.repository import HRSettingsRepository
from hr_time.api.check_in.service import CheckinService
from hr_time.api.employee.api import get_current_employee_id
from hr_time.api.check_in.api import has_open_session as checkin_has_open_session
from hr_time.api.shared.utils.response import Response
from hr_time.api.worklog.domain.services.worklog_state_service import WorklogStateService


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

    return WorklogService.prod().prepare_for_checkout(employee_id)


@frappe.whitelist()
def has_open_session(employee_id: str = None) -> bool:
    """Worklog API - delegates to check_in"""
    return checkin_has_open_session(employee_id)


def is_new_temporary_document(referred_worklog_name: str) -> bool:
    """Check if this is a new unsaved document"""
    if not referred_worklog_name:
        return True
    # Frappe's pattern for new documents
    return referred_worklog_name.startswith('new-') or referred_worklog_name.startswith('New ')


@frappe.whitelist()
def get_worklog_context(
    referred_worklog_name: str = None, employee_id: str = None, is_dialog_call: bool = False
) -> dict:
    """Get context for worklog - is it today's? has open session? on break?"""

    employee_id = employee_id or get_current_employee_id()
    today = date.today()

    # Get today's worklog entity
    today_worklog_entity = WorklogRepository().get_todays_worklog_entity(employee_id)
    today_worklog_name = today_worklog_entity.id if today_worklog_entity else None

    is_new_doc = is_new_temporary_document(referred_worklog_name)
    ignore_is_new_doc = is_dialog_call  # Dialog calls with no name are for existing worklogs, not new ones

    # Check if this worklog is today's
    is_todays = False
    if referred_worklog_name and today_worklog_name:
        is_todays = today_worklog_name == referred_worklog_name

    if is_dialog_call:
        # For dialog calls, we want to treat it as today's worklog if there's an existing one, even if no name is passed
        is_todays = bool(today_worklog_name)
        is_new_doc = not bool(today_worklog_name)  # If there's an existing today's worklog, it's not a new doc

    # Check if latest event was a break
    checkin_service = CheckinService.prod()
    events = checkin_service.data.get(today, employee_id)
    latest = events.get_latest()
    has_open_session = bool(latest and latest.is_in and not latest.is_break)
    on_break = bool(not has_open_session and latest and not latest.is_in and latest.is_break)

    state = WorklogStateService.determine_state(
        is_new_doc=is_new_doc and not ignore_is_new_doc,
        is_todays=is_todays,
        has_open_session=has_open_session,
        on_break=on_break
    )

    # Get the worklog document if it exists
    worklog_total_hours = 0
    if referred_worklog_name and not is_new_doc:
        try:
            worklog_doc = frappe.get_doc(WorklogRepository.DOCTYPE_NAME, referred_worklog_name)
            worklog_total_hours = worklog_doc.time_saved or 0
        except Exception:
            pass

    is_editable = WorklogStateService.is_editable(state, is_new_doc, is_todays)

    # Render display HTML for the worklog (top bar)
    worklog_overview_headline = frappe.render_template(
        "templates/worklog/worklog_overview_headline.html",
        {
            "state": state.value,
            "total_hours": round(worklog_total_hours, 2),
            "is_editable": is_editable,
            "_": frappe._
        }
    )

    # Render worklog made today indicator HTML (for the dialog)
    has_worklog_today = bool(today_worklog_name)
    worklog_status_today_html = frappe.render_template(
        "templates/worklog/worklog_made_today_indicator.html",
        {
            "has_worklog": has_worklog_today,
            "_": frappe._
        }
    )

    return {
            "worklog_state": state.value,
            "is_todays_worklog": is_todays,
            "has_open_session": has_open_session,
            "on_break": on_break,
            "today_worklog_name": today_worklog_name,
            "worklog_status_today_html": worklog_status_today_html,
            "worklog_overview_headline": worklog_overview_headline,
            "headline_color": state.display_color(),
            "tolerance_minutes": frappe.db.get_single_value(
                HRSettingsRepository.DOCTYPE_NAME,
                HRSettingsRepository.FIELD_NAME_TOLERANCE
            ) or 0,
            "is_read_only": not is_editable,
            "is_new_doc": is_new_doc
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

        # Save worklog using service
        service = WorklogService.prod()
        saved_name, checkout_performed = service.save_worklog_and_checkout(
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
