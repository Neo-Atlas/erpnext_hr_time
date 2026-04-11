from typing import Dict, Any
from datetime import date

import frappe, json
from frappe import _

from hr_time.api.worklog.service import WorklogService
from hr_time.api.check_in.service import CheckinService
from hr_time.api.worklog.repository import WorklogRepository
from hr_time.api.hr_settings.repository import HRSettingsRepository
from hr_time.api.employee.api import get_current_employee_id


@frappe.whitelist()
def get_tolerance_minutes() -> int:
    """Get worklog tolerance from HR Settings"""
    return HRSettingsRepository.get_tolerance_minutes()

@frappe.whitelist()
def get_tasks_for_user(user: str, limit: int = 5) -> list:
    """Get tasks assigned to user for worklog prefilling. Sorted by modified DESC, then exp_start_date ASC"""
    # Get employee_id from user
    employee_id = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not employee_id:
        return []
    
    return WorklogService.prod()._get_prefill_tasks(employee_id, limit)

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
        # from hr_time.api.employee.api import get_current_employee_id
        employee_id = get_current_employee_id()
    
    return WorklogService.prod().prepare_for_checkout(employee_id)

@frappe.whitelist()
def validate_checkout_allocation(
    employee_id: str = None, 
    allocated_hours: float = 0
) -> Dict[str, Any]:
    """
    Validate if checkout can proceed based on allocation
    Thin wrapper around WorklogService
    """
    if not employee_id:
        # from hr_time.api.employee.api import get_current_employee_id
        employee_id = get_current_employee_id()
    
    return WorklogService.prod().validate_checkout_allocation(
        employee_id, 
        allocated_hours
    )

@frappe.whitelist()
def get_todays_worklog(employee_id: str = None) -> Dict[str, Any]:
    """Get today's worklog if exists"""
    if not employee_id:
        # from hr_time.api.employee.api import get_current_employee_id
        employee_id = get_current_employee_id()
    
    repo = WorklogRepository()
    worklog = repo.get_todays_worklog(employee_id)
    
    if worklog:
        # Calculate allocated from tasks_entry instead of non-existent field
        worklog_doc = frappe.get_doc("Worklog", worklog.name)
        total_allocated = sum(float(t.time_spent or 0) for t in worklog_doc.tasks_entry)
        
        return {
            "exists": True,
            "name": worklog.name,
            "time_allocated": round(total_allocated, 2),
            "docstatus": worklog.docstatus
        }
    
    return {"exists": False}

@frappe.whitelist()
def has_open_session(employee_id: str = None) -> bool:
    """Worklog API - delegates to check_in"""
    from hr_time.api.check_in.api import has_open_session as checkin_has_open_session
    return checkin_has_open_session(employee_id)

def is_new_temporary_document(worklog_name):
    """Check if this is a new unsaved document"""
    if not worklog_name:
        return True
    # Frappe's pattern for new documents
    return worklog_name.startswith('new-') or worklog_name.startswith('New ')

@frappe.whitelist()
def get_worklog_context(worklog_name: str = None, employee_id: str = None) -> dict:
    """Get context for worklog - is it today's? has open session? on break?"""

    if not employee_id:
        # from hr_time.api.employee.api import get_current_employee_id
        employee_id = get_current_employee_id()

    today = date.today()

    is_new_doc = is_new_temporary_document(worklog_name)

    # Get today's worklog(for comparison)
    today_worklog = None
    if employee_id:
        today_worklog = WorklogRepository().get_todays_worklog(employee_id)    # Should this be a static method ?

    # Check if this worklog is today's
    is_todays = False
    if worklog_name and today_worklog:
        is_todays = today_worklog.name == worklog_name

    # Check if latest event was a break
    checkin_service = CheckinService.prod()
    events = checkin_service.data.get(today, employee_id)
    latest = events.get_latest()
    has_open_session = bool(latest and latest.is_in and not latest.is_break)
    on_break = bool(not has_open_session and latest and not latest.is_in and latest.is_break)

    # Determine state
    if is_new_doc:
        state = "new"
    elif not is_todays: # Existing worklog not from today
        state = "historical"
    elif has_open_session:
        state = "working"
    elif on_break:
        state = "break"
    else:
        state = "completed"

    # Get the worklog document if it exists
    # worklog_doc = None
    worklog_total_hours = 0
    if worklog_name and not is_new_doc:
        try:
            worklog_doc = frappe.get_doc("Worklog", worklog_name)
            worklog_total_hours = worklog_doc.time_saved or 0
        except Exception:
            pass

    # Determine if this worklog is editable: if it's new OR today's worklog and has open session
    is_editable = False
    if is_new_doc: # or (is_todays and has_open_session):
        is_editable = True
    elif is_todays and state != "completed":
        is_editable = True

    # Render display HTML for the worklog (top bar)
    worklog_overview_headline = frappe.render_template(
        "templates/worklog/worklog_overview_headline.html",
        {
            "state": state,
            "total_hours": round(worklog_total_hours, 2),
            "is_editable": is_editable,
            "_": frappe._
        }
    )

    # Render worklog made today indicator HTML (for the dialog)
    has_worklog_today = bool(today_worklog)
    # ✅ Render the complete worklog status HTML on the server
    worklog_status_today_html = frappe.render_template(
        "templates/worklog/worklog_made_today_indicator.html",
        {
            "has_worklog": has_worklog_today,
            "_": frappe._
        }
    )

    # Get tolerance from HR Settings repository (cached)
    # tolerance_minutes = HRSettingsRepository.get_tolerance_minutes()

    return {
        "worklog_state": state,
        "is_todays_worklog": is_todays,
        "has_open_session": has_open_session,
        "on_break": on_break,
        "today_worklog_name": today_worklog.name if today_worklog else None,
        "worklog_status_today_html": worklog_status_today_html,
        "worklog_overview_headline": worklog_overview_headline,
        "tolerance_minutes": frappe.db.get_single_value("HR Settings", "cstm_worklog_time_allocation_tolerance") or 30,
        "is_read_only": not is_editable,
        "is_new_doc": is_new_doc
        # "tolerance_minutes": tolerance_minutes,
    }

@frappe.whitelist()
def save_and_checkout(worklog_name: str = None, employee_id: str = None, worklog_data = None, current_total = 0) -> dict:
    """Save worklog and perform checkout in one action"""
    try:
        from hr_time.api.check_in.service import CheckinService, Action
        # Parse worklog_data - it's ALWAYS a string in form data
        if worklog_data and isinstance(worklog_data, str):
            worklog_data = json.loads(worklog_data)
        else:
            worklog_data = worklog_data or {}
        
        # Ensure current_total is float
        if current_total is None or current_total == '':
            current_total = 0
        current_total = float(current_total)
        
        # 1. Handle worklog
        if worklog_name:
            # Update existing
            worklog = frappe.get_doc("Worklog", worklog_name)

            if worklog_data:
                # Store current_total as transient for validation
                worklog.__current_total = current_total

                # Update simple fields
                worklog.time_saved = worklog_data.get('time_saved', worklog.time_saved)
                
                if 'task_desc' in worklog_data:
                    worklog.task_desc = worklog_data['task_desc']
                if 'is_home_office' in worklog_data:
                    worklog.is_home_office = worklog_data['is_home_office']
                if 'ticket_link' in worklog_data:
                    worklog.ticket_link = worklog_data['ticket_link']
                                    
                # Handle child table separately
                if 'tasks_entry' in worklog_data:
                    worklog.set('tasks_entry', [])
                    for task in worklog_data['tasks_entry']:
                        worklog.append('tasks_entry', {
                            'task': task.get('task'),
                            'task_subject': task.get('task_subject'),   # Historical snapshot
                            'task_status': task.get('task_status'),
                            'expected_time': task.get('expected_time',0),
                            'priority': task.get('priority'),
                            'time_spent': task.get('time_spent',0), # Actual work done
                            'description': task.get('description', ''), # User notes
                            'progress_increment': task.get('progress_increment',0), # Calculated
                        })

            worklog.save()
            frappe.db.commit()

        else:
            # otherise, Create new
            worklog = frappe.new_doc("Worklog")
            worklog.employee = employee_id
            worklog.__current_total = current_total

            if worklog_data:
                worklog.task_desc = worklog_data.get('task_desc', '')
                worklog.is_home_office = worklog_data.get('is_home_office', 'No')
                worklog.ticket_link = worklog_data.get('ticket_link', '')
                worklog.time_saved = worklog_data.get('time_saved', 0)

                # Add tasks
                if 'tasks_entry' in worklog_data:
                    for task in worklog_data['tasks_entry']:
                        worklog.append('tasks_entry', {
                            'task': task.get('task'),
                            'task_subject': task.get('task_subject'),
                            'expected_time': task.get('expected_time', 0),
                            'time_spent': task.get('time_spent', 0),
                            'progress_increment': task.get('progress_increment', 0),
                            'task_status': task.get('task_status', 'Open'),
                            'description': task.get('description', ''),
                            'priority': task.get('priority', '')
                        })

            worklog.insert()    # Just insert, not submit
            frappe.db.commit()

        # 2. Perform checkout (ONLY if there's an open session!)
        checkin_service = CheckinService.prod()

        # Check if employee has an open session
        has_open_session = checkin_service.has_open_session(employee_id)
    
        if has_open_session:
            checkin_service.checkin(Action.endOfWork)

        return {
            "success": True,
            "worklog": worklog.name,
            "message": "Worklog saved successfully" + (" and checked out" if has_open_session else "")
        }

    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON: {str(e)}"}
    
    except Exception as e:
        frappe.db.rollback()
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }
