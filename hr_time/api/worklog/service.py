
from datetime import datetime, date, timedelta
import json
from typing import Optional, List, Dict, Any

import frappe
from frappe import _

from hr_time.api import logger
from hr_time.api.worklog.repository import WorklogRepository
from hr_time.api.hr_settings.repository import HRSettingsRepository
from hr_time.api.check_in.service import CheckinService
from hr_time.api.flextime.repository import DurationType


class WorklogService:
    """
    Service layer for managing operations related to employee worklogs.
    Provides methods to check for existing worklogs and to create new worklogs using the WorklogRepository.

    Attributes:
        worklog (WorklogRepository): Repository instance used for interacting with Worklog doctype table.
        hr_settings:
    """
    worklog: WorklogRepository
    hr_settings: HRSettingsRepository

    def __init__(self, worklog: WorklogRepository, hr_settings: HRSettingsRepository):
        """
        Initializes the WorklogService with a given WorklogRepository.

        Args:
            worklog (WorklogRepository): Repository for worklog operations.
        """
        super().__init__()
        self.worklog = worklog
        self.hr_settings = hr_settings

    @staticmethod
    def prod() -> 'WorklogService':
        """
        Creates a production instance of WorklogService with a default WorklogRepository.

        Returns:
            WorklogService: An initialized WorklogService instance for production use.
        """
        return WorklogService(WorklogRepository(), HRSettingsRepository())

    def check_if_employee_has_worklogs_today(self, employee_id) -> bool:
        """
        Checks if the specified employee has created any worklogs today.

        Args:
            employee_id (str): The ID of the employee whose worklogs are being checked.

        Returns:
            bool: True if the employee has worklogs for the current day, False otherwise.
        """
        today = date.today()
        worklogs = self.worklog.get_worklogs_of_employee_on_date(employee_id, today)
        return len(worklogs) > 0
    
    # ============ 2. CHECKOUT PREPARATION ============
    
    def prepare_for_checkout(self, employee_id: str) -> Dict[str, Any]:
        """
        Prepare all data needed for checkout worklog dialog
        Main entry point for checkout flow
        """
        today = date.today()

        # 1. Get fresh check-in data
        checkin_service = CheckinService.prod()
        events = checkin_service.data.get(today, employee_id)
        durations = events.get_durations()

        # 2. Calculate CURRENT total work time
        current_work_seconds = self._calculate_work_seconds(durations, events)
        current_work_hours = current_work_seconds / 3600

        # 3. Check for existing worklog
        existing = self.worklog.get_todays_worklog(employee_id)

        # 4. Initialize variables with defaults
        saved_hours = 0
        time_since_last_save = 0
        work_duration = 0
        tasks_data = []

        # 5. Calculate components if existing worklog
        if existing and existing.docstatus == 0:  # Draft worklog exists
            saved_hours = existing.time_saved or 0
            time_since_last_save = max(0, current_work_hours - saved_hours)
            work_duration = saved_hours  # Show saved value

            # Get the full worklog document with tasks and other fields
            worklog_doc = frappe.get_doc("Worklog", existing.name)

            for task in worklog_doc.tasks_entry:
                tasks_data.append({
                    "task": task.task,
                    "task_subject": task.task_subject,
                    "task_status": task.task_status,
                    "time_spent": task.time_spent,
                    "expected_time": task.expected_time,
                    "description": task.description,
                    "progress_increment": task.progress_increment,
                    "priority": task.priority or "",
                })
            
            # Include all existing worklog data
            existing_data = {
                "existing_worklog_name": existing.name,
                "existing_tasks": tasks_data,
                "existing_task_desc": worklog_doc.task_desc,
                "existing_ticket_link": worklog_doc.ticket_link,
                "existing_is_home_office": worklog_doc.is_home_office,
            }
        else:
            time_since_last_save = 0
            work_duration = 0
            existing_data = {}

        # 6. Get tolerance from HR Settings repository (cached)
        tolerance_minutes = HRSettingsRepository.get_tolerance_minutes()
        
        # 7. Get prefilled tasks (suggestions, not saved)
        prefilled_tasks = self._get_prefill_tasks(employee_id)

        # ___________________________________________________________________________________________
        # Generate overview headline
        state = "working"
        color = "green"

        if existing and existing.docstatus == 0:
            if self._has_open_session(events):
                state = "working"
                color = "green"
            elif self._is_on_break(events):
                state = "break"
                color = "orange"
            else:
                state = "completed"
                color = "blue"
        else:
            state = "new"
            color = "purple"

        # Calculate totals for headline
        total_hours = current_work_hours
        saved_hours = existing.time_saved if existing else 0
        time_since_last_save = max(0, total_hours - saved_hours)

        # Render the headline template
        worklog_overview_headline = frappe.render_template(
            "templates/worklog/worklog_overview_headline.html",
            {
                "state": state,
                "total_hours": round(total_hours, 2),
                "saved_hours": round(saved_hours, 2),
                "time_since_last_save": round(time_since_last_save, 2),
                "is_editable": True,
                "_": frappe._
            }
        )

        # 8. Build response
        response = {
            "time_saved": round(work_duration, 2),  # Saved in DB (0 if new worklog) 
            "time_since_last_save": round(time_since_last_save, 2),    # Current session (since last save)
            "time_total_actual": round(current_work_hours, 2),      # time_saved + time_since_last_save
            "has_open_session": self._has_open_session(events), # Employee currently checked in?
            "prefilled_tasks": prefilled_tasks, # Tasks assigned to user (sorted by modified DESC, exp_start_date ASC)
            "tolerance_minutes": tolerance_minutes,
            "worklog_overview_headline": worklog_overview_headline,
            "headline_color": color,
        }

        if existing:
            response.update(existing_data)

        return response


    def _calculate_work_seconds(self, durations: list, events) -> float:
        """Calculate total work seconds from WORK durations"""
        total = 0.0
        
        # Sum all WORK durations
        for duration in durations:
            if duration.duration_type == DurationType.WORK:
                total += duration.total_time
        
        # Add open session if exists
        if self._has_open_session(events):
            latest = events.get_latest()
            if latest and latest.is_in and not latest.is_break:
                total += (datetime.now() - latest.timestamp).total_seconds()
        
        return total
    
    def _has_open_session(self, events) -> bool:
        """Check if employee is currently checked in"""
        latest = events.get_latest()
        return bool(latest and latest.is_in and not latest.is_break)

    def _is_on_break(self, events) -> bool:
        """Check if employee is currently on break"""
        latest = events.get_latest()
        return bool(latest and not latest.is_in and latest.is_break)
    
    def _serialize_events(self, events: list) -> str:
        """Convert CheckinEvent objects to JSON string"""
        events_data = [{
            "id": e.id,
            "timestamp": e.timestamp.isoformat(),
            "is_in": e.is_in,
            "is_break": e.is_break,
            "log_type": "IN" if e.is_in else "OUT"
        } for e in events]
        
        return json.dumps(events_data, indent=2)
    
    def _get_prefill_tasks(self, employee_id: str, limit: int = 5) -> List[Dict]:
        """Get tasks to prefill in worklog - used by both full form and dialog"""
        user_id = frappe.db.get_value("Employee", employee_id, "user_id")
        if not user_id:
            return []

        # Get the buffer task name from HR Settings
        buffer_task_id = self.hr_settings.get_buffer_task()
        print('buffer_task_id')
        print(buffer_task_id)

        # 1. Get assigned tasks (business-critical)
        assigned_tasks = self._get_assigned_tasks(user_id, buffer_task_id, limit)

        # 2. If assigned tasks >= limit, return only assigned (no generic)
        if len(assigned_tasks) >= limit:
            return assigned_tasks[:limit]
        
        # 3. Fill remaining with generic tasks
        remaining = limit - len(assigned_tasks)
        generic_tasks = self._get_generic_tasks(buffer_task_id, remaining)

        # 4. Assigned first, then generic
        return assigned_tasks + generic_tasks

    def _get_assigned_tasks(self, user_id: str, buffer_task_id: str, limit: int) -> List[Dict]:
        """Fetch tasks assigned to user (business-critical work)"""
        query = """
            SELECT 
                name as task,
                subject as task_subject,
                expected_time,
                status as task_status,
                priority
            FROM `tabTask`
            WHERE 
                IFNULL(_assign, '') != ''
                AND JSON_CONTAINS(_assign, %s)
                AND status NOT IN ('Completed', 'Cancelled')
                AND (is_generic != 1 OR is_generic IS NULL)
        """
        params = [json.dumps(user_id)]

        if buffer_task_id:
            query += " AND name != %s"
            params.append(buffer_task_id)

        query += """
            ORDER BY
                FIELD(priority, 'Urgent', 'High', 'Medium', 'Low', ''),
                modified DESC
            LIMIT %s
        """
        params.append(limit)

        return frappe.db.sql(query, params, as_dict=True)

    def _get_generic_tasks(self, buffer_task_id: str, limit: int) -> List[Dict]:
        """Fetch generic tasks (only as fillers, lower priority)"""
        if limit <= 0:
            return []
        
        query = """
            SELECT 
                name as task,
                subject as task_subject,
                expected_time,
                status as task_status,
                priority
            FROM `tabTask`
            WHERE 
                is_generic = 1
                AND status NOT IN ('Completed', 'Cancelled')
        """
        params = []

        if buffer_task_id:
            query += " AND name != %s"
            params.append(buffer_task_id)

        query += """
            ORDER BY
                FIELD(priority, 'Urgent', 'High', 'Medium', 'Low', ''),
                modified DESC
            LIMIT %s
        """
        params.append(limit)

        return frappe.db.sql(query, params, as_dict=True)

    # ============ 3. VALIDATION ============

    def validate_checkout_allocation(
        self, 
        employee_id: str, 
        allocated_hours: float
    ) -> Dict[str, Any]:
        """
        Validate if time allocation is within tolerance
        Called during checkout to enable/disable button
        """
        today = date.today()

        # Get current work duration
        checkin_service = CheckinService.prod()
        events = checkin_service.data.get(today, employee_id)
        durations = events.get_durations()
        
        work_seconds = self._calculate_work_seconds(durations, events)
        work_hours = work_seconds / 3600

        # Get tolerance from HR Settings repository (cached)
        tolerance_minutes = self.hr_settings.get_tolerance_minutes()
        tolerance_hours = tolerance_minutes / 60

        difference = abs(work_hours - allocated_hours)

        return {
            "can_checkout": difference <= tolerance_hours,
            "work_hours": round(work_hours, 2),
            "allocated_hours": round(allocated_hours, 2),
            "difference": round(difference, 2),
            "tolerance_hours": tolerance_hours,
            "tolerance_minutes": tolerance_minutes,
            "within_tolerance": difference <= tolerance_hours
        }

    def validate_worklog_document(self, doc) -> Dict[str, Any]:
        """
        Validate worklog document before saving
        """
        # Get current total from frontend (passed via API)
        print('VALIDATING!!!')
        current_total = getattr(doc, '__current_total', None)

        if current_total is None:
            today = date.today()
            checkin_service = CheckinService.prod()
            events = checkin_service.data.get(today, doc.employee)
            durations = events.get_durations()

            # Calculate actual work hours from check-in events
            actual_work_hours = self._calculate_work_seconds(durations, events) / 3600
            # ✅ Ensure doc.time_saved is float
            time_saved = float(doc.time_saved) if doc.time_saved else 0.0

            print(f"doc.time_saved type: {type(time_saved)}, value: {time_saved}")
            print(f"actual_work_hours type: {type(actual_work_hours)}, value: {actual_work_hours}")
            
            # For existing worklogs, use the larger of saved time or actual work
            if doc.docstatus == 0 and time_saved > 0:
                current_total = max(time_saved, actual_work_hours)
            else:
                current_total = actual_work_hours
            
            if current_total <= 0 and time_saved > 0:
                current_total = time_saved
            # _________________________________________________________
        
        current_total = float(current_total) if current_total is not None else 0.0
        
        # Calculate allocated from tasks
        total_allocated = 0.0
        for row in doc.tasks_entry:
            total_allocated += float(row.time_spent or 0)

        # Calculate difference
        time_unallocated = current_total - total_allocated

        # Get tolerance from HR Settings repository (cached)
        tolerance_minutes = HRSettingsRepository.get_tolerance_minutes()
        tolerance_hours = (tolerance_minutes / 60)
        abs_difference = abs(time_unallocated)

        # Check if within tolerance
        if abs_difference <= tolerance_hours:
            # WITHIN TOLERANCE - accept user's allocation
            if time_unallocated < 0:
                # Overallocated within tolerance → increase recorded time
                doc.time_saved = total_allocated
            else:
                doc.time_saved = current_total
            
            return {"valid": True}
        
        else:
            # EXCEEDS TOLERANCE - reject save
            return {
                "valid": False,
                "title": "Allocation Mismatch",
                "message": _(f"Time allocation mismatch!"
                            f"<br>Worked <b> {current_total:.2f} hrs</b>,"
                            f" but allocated <b> {total_allocated:.2f} hrs</b>. "
                            f"<br>Difference of <b> {abs_difference:.2f} hrs </b>"
                            f"exceeds tolerance (<b> ±{tolerance_hours:.2f} hrs</b>)."
                            f"<br>Please adjust your allocations.")
            }
    # ============ 4. SUBMISSION PROCESSING ============

    def process_worklog_save(self, doc, timesheet_name=None):
        """Process worklog after save - creates/cancels timesheet AND updates task progress"""
        try:
            timesheet = None

            # 1. Handle timesheet
            if not timesheet_name:
                # Create new timesheet with distributed times
                timesheet = self._create_timesheet_from_worklog(doc)
                if timesheet:
                    doc.db_set("timesheet", timesheet.name)
            else:
                # Update existing timesheet
                timesheet = self._replace_old_timesheet_of_worklog(doc, timesheet_name)

            # 2. ALWAYS update task progress (regardless of timesheet)
            self._update_task_progress(doc)

            return timesheet or True

        except Exception as e:
            frappe.log_error(f"Worklog processing failed: {str(e)}")
            return None


    def _update_task_progress(self, doc):
        """Update progress percentage for each task based on time spent"""
        for task_row in doc.tasks_entry:
            if not task_row.task or not task_row.time_spent: #there is nth called 'total row'
                continue

            try:
                # 1. Update the increment in worklog (for this session)
                if task_row.expected_time and task_row.expected_time > 0:
                    increment = (task_row.time_spent / task_row.expected_time) * 100
                    task_row.progress_increment = min(increment, 100)

                # 2. Recalculate task's TOTAL progress from ALL submitted timesheets
                total_progress_hours = frappe.db.sql("""
                    SELECT SUM(hours)
                    FROM `tabTimesheet Detail`
                    WHERE task = %s AND docstatus = 1
                """, task_row.task)[0][0] or 0

                task = frappe.get_doc("Task", task_row.task)
                if task.expected_time and task.expected_time > 0:
                    new_progress = (total_progress_hours / task.expected_time) * 100
                    new_progress = min(new_progress, 100)

                if abs(new_progress - task.progress) > 0.01:
                    task.db_set("progress", round(new_progress, 2), update_modified=False)

            except Exception as e:
                logger.error(f"Error updating task {task_row.task}: {str(e)}")
                continue

    # ============ 5. TASK ALLOCATION HELPERS ============

    def calculate_progress_increment(self, time_spent: float, expected_time: float) -> float:
        """Calculate progress percentage from time spent"""
        if expected_time and expected_time > 0:
            increment = (time_spent / expected_time) * 100
            return round(min(increment, 100), 1)
        return 0.0

    def _get_session_times_from_checkin(self, employee_id, date=None):
        """
        Get session start and end from fresh check-in events

            Get raw events from events_list.events to access timestamps

            Build a map of event IDs to timestamps

            Use duration.event_first and duration.event_second to look up timestamps

            Handle cases where event_second might be None (ongoing session)

            Properly identify WORK durations by checking duration.duration_type != DurationType.BREAK
        """
        from hr_time.api.check_in.repository import CheckinRepository
        from hr_time.api.flextime.repository import DurationType
        from datetime import datetime, timedelta
        import frappe
        
        # Handle if date is a string
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()

        if date is None:
            date = frappe.utils.today()

        # If date is datetime object, get date part
        if hasattr(date, 'date'):
            date = date.date()


        try:
            checkin_repo = CheckinRepository()

            events_list = checkin_repo.get(date, employee_id)
            
            if not events_list:
                return None, None

            # Get the raw events to access timestamps
            events = events_list.events
            # Build a map of event ID to timestamp
            event_timestamps = {}
            for event in events:
                event_timestamps[event.id] = event.timestamp
            durations = events_list.get_durations()

            if not durations:
                return None, None
            
            # Find first WORK duration start and last WORK duration end
            session_start = None
            session_end = None
            
            for idx, duration in enumerate(durations):
                # Get timestamps from original events
                start_timestamp = event_timestamps.get(duration.event_first)
                end_timestamp = event_timestamps.get(duration.event_second) if duration.event_second else None

                # Check if this is a WORK duration (not BREAK)
                if duration.duration_type != DurationType.BREAK:
                    # This is a WORK duration
                    if session_start is None and start_timestamp:
                        session_start = start_timestamp
                    
                    # Always update session_end to the latest work duration end
                    if end_timestamp:
                        session_end = end_timestamp
                    elif start_timestamp:
                        # If no end timestamp (still working), use start as current
                        session_end = datetime.now()
            
            # If no end found but we have a start, assume still working
            if session_start and not session_end:
                session_end = datetime.now()

            return session_start, session_end

        except Exception as e:
            print(f'ERROR in _get_session_times_from_checkin: {str(e)}')
            import traceback
            traceback.print_exc()
            return None, None
    

    def _create_timesheet_from_worklog(self, worklog):
        """Create Timesheet document with distributed time entries"""

        if not worklog.tasks_entry:
            return None

        # TIME SHEET NOT CREATED!
        timesheet = frappe.new_doc("Timesheet")
        timesheet.employee = worklog.employee

        try:
            # Convert log_time to datetime if it's a string
            if isinstance(worklog.log_time, str):
                log_datetime = datetime.strptime(worklog.log_time, '%Y-%m-%d %H:%M:%S.%f')
            else:
                log_datetime = worklog.log_time
            
            date_to_use = log_datetime.date()

            # Get session times fresh from check-in
            session_start, session_end = self._get_session_times_from_checkin(
                worklog.employee, 
                date_to_use
            )

            if not session_start:
                session_start = log_datetime    #! Shouldn't the session start be today's first checkin time and not log_time bcoz that can be just few moments ago ?
                session_end = log_datetime

            # Get activity type from HR Settings
            activity_type = self.hr_settings.get_default_activity_type()

            # Calculate current totals
            current_total = worklog.time_saved
            total_allocated = sum(float(t.time_spent or 0) for t in worklog.tasks_entry)
            time_unallocated = current_total - total_allocated

            # So time_unallocated should be 0 or very close
            if abs(time_unallocated) <= 0.01:
                # Perfect match - allocate as is
                self._add_allocated_tasks(timesheet, worklog, session_start, activity_type)
                # No buffer task needed
            elif time_unallocated > 0:
                # Underallocated - add buffer task for remaining time
                current_time = self._add_allocated_tasks(timesheet, worklog, session_start, activity_type)
                self._add_unallocated_task(timesheet, worklog, current_time, activity_type, time_unallocated)
            else:
                # This shouldn't happen within tolerance, but if it does, it means
                # overallocated but within tolerance - time_saved was adjusted up
                # So allocations already match time_saved exactly
                self._add_allocated_tasks(timesheet, worklog, session_start, activity_type)
        
            # Submit and return the timesheet
            return self._submit_timesheet(timesheet, worklog)
        
        except Exception as e:
            print(f'ERROR in _create_timesheet_from_worklog: {str(e)}')
            import traceback
            traceback.print_exc()
            return None

    def _replace_old_timesheet_of_worklog(self, doc, timesheet_name):
        """Cancels old timesheet and create fresh one"""
        if not timesheet_name:
            return self._create_timesheet_from_worklog(doc)

        original_user = frappe.session.user

        try:
            # Switch to admin for cancel operation
            frappe.set_user("Administrator")

            # Cancel existing timesheet if submitted
            old_timesheet = frappe.get_doc("Timesheet", timesheet_name)
            affected_tasks = [log.task for log in old_timesheet.time_logs if log.task]
            
            if old_timesheet.docstatus == 1:
                old_timesheet.cancel()
                frappe.msgprint(f"Cancelled old timesheet {timesheet_name}")

                # frappe.db.commit()
                # Reset progress for affected tasks
                for task_name in set(affected_tasks):
                    self._recalculate_task_progress(task_name)
                    frappe.msgprint(f"Recalculated progress for task {task_name}")

        except Exception as e:
            frappe.log_error(f"Error canceling timesheet {timesheet_name}: {str(e)}")
        finally:
            # Switch back to original user
            frappe.set_user(original_user)
        
        # Always create fresh timesheet
        return self._create_timesheet_from_worklog(doc)
    
    def _add_allocated_tasks(self, timesheet, worklog, start_time, activity_type):
        """Add allocated tasks sequentially (existing method)"""
        task_start_time = start_time

        for task_row in worklog.tasks_entry:
            if task_row.task and task_row.time_spent > 0:
                task_end = task_start_time + timedelta(hours=float(task_row.time_spent))

                timesheet.append("time_logs", {
                    "activity_type": activity_type,
                    "task": task_row.task,
                    "hours": float(task_row.time_spent),
                    "from_time": task_start_time,
                    "to_time": task_end,
                    "completed": 1,
                    "is_billable": 1,
                    "description": task_row.description or task_row.task_subject
                })

                task_start_time = task_end

        return task_start_time

    def _add_unallocated_task(self, timesheet, worklog, task_start_time, activity_type, time_unallocated):
        """Add unallocated time at the end (for underallocation)"""
        if time_unallocated <= 0.01:
            return task_start_time
        
        buffer_task = self.hr_settings.get_buffer_task()
        task_end_time = task_start_time + timedelta(hours=float(time_unallocated))
        
        timesheet.append("time_logs", {
            "activity_type": activity_type,
            "task": buffer_task,
            "hours": float(time_unallocated),
            "from_time": task_start_time,
            "to_time": task_end_time,
            "completed": 0,
            "is_billable": 1,
            "description": "Unallocated excess time from the allocated tasks"
        })
        
        return task_end_time

    def _get_or_create_unallocated_task(self):
        """Get or create tolerance buffer task"""
        task_name = frappe.db.get_single_value(
            "HR Settings", 
            "cstm_worklog_buffer_task"
        )

        if not task_name:
            task_name = "Worklog Buffer" 
        
        # Create if doesn't exist
        if not frappe.db.exists("Task", {"subject": task_name}):
            task = frappe.new_doc("Task")
            task.subject = task_name
            task.status = "Open"
            task.is_generic = 1
            task.insert(ignore_permissions=True)
            return task.name
        
        return frappe.db.get_value("Task", {"subject": task_name}, "name")

    def _recalculate_task_progress(self, task_name):
        """Recalculate task progress based on ALL submitted timesheets"""
        task = frappe.get_doc("Task", task_name)
    
        # Get total hours from ALL submitted (not cancelled) timesheets
        total_progress_hours = frappe.db.sql("""
            SELECT SUM(hours) 
            FROM `tabTimesheet Detail` 
            WHERE task = %s 
            AND parent IN (
                SELECT name FROM `tabTimesheet` 
                WHERE docstatus = 1  # Only submitted, not cancelled
            )
        """, task_name)[0][0] or 0

        if task.expected_time and task.expected_time > 0:
            new_progress = (total_progress_hours / task.expected_time) * 100
            new_progress = min(new_progress, 100)
            
            task.db_set("progress", round(new_progress, 2), update_modified=False)
            task.add_comment("Info", f"Progress recalculated: {new_progress:.1f}%")

    def _submit_timesheet(self, timesheet, doc):
        """Submit timesheet with admin privileges"""
        if not timesheet.time_logs:
            return None
        
        original_user = frappe.session.user
        
        try:
            timesheet.save()
            
            frappe.set_user("Administrator")
            timesheet.submit()
            
            doc.db_set("timesheet", timesheet.name)
            frappe.msgprint(_(f"Timesheet {timesheet.name} created successfully"))
            
            return timesheet
            
        except Exception as e:
            frappe.log_error(f"Timesheet submission failed: {str(e)}")
            raise
        finally:
            frappe.set_user(original_user)
