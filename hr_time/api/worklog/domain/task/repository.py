from typing import List, Dict, Optional
import json

import frappe

from hr_time.api.worklog.domain.task.task_enums import TaskPriority, TaskStatus, TaskType
from hr_time.api.employee.repository import EmployeeRepository
from hr_time.api.shared.domain.document_status import DocumentStatus


class TaskRepository:
    """Repository for Task operations.

    Note: Constants defined for custom fields and doctype names only.
    Standard Frappe fields (modified, creation, owner, etc.) are hardcoded
    as they are unlikely to change.
    """
    DOCTYPE_NAME = "Task"
    DOCTYPE_TIMESHEET_DETAIL = "Timesheet Detail"

    # Field constants - single source of truth
    FIELD_NAME = "name"
    FIELD_IS_GENERIC = "is_generic"
    FIELD_IS_INTERNAL = "custom_is_internal"
    FIELD_STATUS = "status"
    FIELD_SUBJECT = "subject"
    FIELD_PRIORITY = "priority"
    FIELD_EXPECTED_TIME = "expected_time"
    FIELD_EXP_START_DATE = "exp_start_date"
    FIELD_ASSIGN = "_assign"

    @staticmethod
    def _get_task_type_condition(task_type: 'TaskType') -> str:
        """Return SQL WHERE condition for task type"""
        if task_type == TaskType.ASSIGNED:
            return f"({TaskRepository.FIELD_IS_GENERIC} != 1 OR {TaskRepository.FIELD_IS_GENERIC} IS NULL)"
        else:  # TaskType.GENERIC
            return f"{TaskRepository.FIELD_IS_GENERIC} = 1"

    @staticmethod
    def _get_exclude_internal_condition() -> str:
        return f"({TaskRepository.FIELD_IS_INTERNAL} != 1 OR {TaskRepository.FIELD_IS_INTERNAL} IS NULL)"

    @staticmethod
    def _get_order_by_clause(include_priority: bool = False) -> str:
        """
        Generate ORDER BY clause for task listing.

        Args:
            include_priority: If True, orders by priority first (Urgent → Low)
                            If False, starts directly with date ordering.

        Returns:
            Complete ORDER BY clause string
        """
        order_parts = []

        if include_priority:
            priorities = TaskPriority.get_priority_order_list()
            quoted_priorities = [f"'{p}'" for p in priorities]
            order_parts.append(f"FIELD(priority, {', '.join(quoted_priorities)})")

        order_parts.extend([
            "exp_start_date IS NULL ASC",  # NULLs last
            "exp_start_date ASC",          # Soonest first
            "modified DESC"                # Recent activity  (tiebreaker for same start date)
        ])

        return f"ORDER BY {', '.join(order_parts)}"

    @staticmethod
    def get_assigned_tasks(user_id: str, limit: int = 5) -> List[Dict]:
        """Fetch tasks assigned to user (business-critical work)"""
        # Exclude completed/cancelled statuses
        excluded_statuses = TaskStatus.completed_statuses()
        status_placeholders = ', '.join(['%s'] * len(excluded_statuses))
        params = [json.dumps(user_id)] + excluded_statuses

        query = f"""
            SELECT
                name as task,
                subject,
                expected_time,
                status,
                priority
            FROM `tab{TaskRepository.DOCTYPE_NAME}`
            WHERE
                IFNULL(_assign, '') != ''
                AND JSON_CONTAINS(_assign, %s)
                AND status NOT IN ({status_placeholders})
                AND {TaskRepository._get_task_type_condition(TaskType.ASSIGNED)}
                AND {TaskRepository._get_exclude_internal_condition()}
        """

        query += TaskRepository._get_order_by_clause(True)
        query += " LIMIT %s"
        params.append(limit)
        return frappe.db.sql(query, params, as_dict=True)

    @staticmethod
    def get_generic_tasks(limit: int = 5) -> List[Dict]:
        """Fetch generic tasks (only as fillers, lower priority)"""
        if limit <= 0:
            return []

        # Exclude completed/cancelled statuses
        excluded_statuses = TaskStatus.completed_statuses()
        status_placeholders = ', '.join(['%s'] * len(excluded_statuses))
        params = excluded_statuses.copy()

        query = f"""
            SELECT
                name as task,
                subject,
                {TaskRepository.FIELD_EXPECTED_TIME},
                status,
                {TaskRepository.FIELD_PRIORITY}
            FROM `tab{TaskRepository.DOCTYPE_NAME}`
            WHERE
                {TaskRepository._get_task_type_condition(TaskType.GENERIC)}
                AND status NOT IN ({status_placeholders})
                AND {TaskRepository._get_exclude_internal_condition()}
        """

        query += TaskRepository._get_order_by_clause(True)
        query += " LIMIT %s"
        params.append(limit)
        return frappe.db.sql(query, params, as_dict=True)

    @staticmethod
    def get_prefill_tasks(employee_id: str, limit: int = 5) -> List[Dict]:
        """Get tasks to prefill in worklog - combines assigned and generic tasks"""
        user_id = frappe.db.get_value(EmployeeRepository.DOCTYPE_NAME, employee_id, "user_id")
        if not user_id:
            return []

        # 1. Get assigned tasks (business-critical)
        assigned_tasks = TaskRepository.get_assigned_tasks(user_id, limit)

        # 2. If assigned tasks >= limit, return only assigned (no generic)
        if len(assigned_tasks) >= limit:
            return assigned_tasks[:limit]

        # 3. Fill remaining with generic tasks
        remaining = limit - len(assigned_tasks)
        generic_tasks = TaskRepository.get_generic_tasks(remaining)

        # 4. Assigned first, then generic
        return assigned_tasks + generic_tasks

    # ============ CRUD OPERATIONS ============

    @staticmethod
    def get_by_id(task_id: str) -> Optional[Dict]:
        """Get task by ID as dict"""
        if not frappe.db.exists(TaskRepository.DOCTYPE_NAME, task_id):
            return None
        return frappe.get_doc(TaskRepository.DOCTYPE_NAME, task_id).as_dict()

    @staticmethod
    def get_doc_by_id(task_id: str):
        """Get task as Frappe doc (for operations that need doc methods)"""
        if not frappe.db.exists(TaskRepository.DOCTYPE_NAME, task_id):
            return None
        return frappe.get_doc(TaskRepository.DOCTYPE_NAME, task_id)

    @staticmethod
    def create_task(data: dict) -> str:
        """Create a new task"""
        task = frappe.new_doc(TaskRepository.DOCTYPE_NAME)
        for field, value in data.items():
            setattr(task, field, value)
        task.insert(ignore_permissions=True)
        return task.name

    @staticmethod
    def update_progress(task_id: str, progress: float) -> None:
        """Update task progress (without modifying modified timestamp)"""
        task = frappe.get_doc(TaskRepository.DOCTYPE_NAME, task_id)
        task.db_set("progress", round(progress, 2), update_modified=False)

    @staticmethod
    def add_comment(task_id: str, comment: str) -> None:
        """Add a comment to a task"""
        task = frappe.get_doc(TaskRepository.DOCTYPE_NAME, task_id)
        task.add_comment("Info", comment)

    @staticmethod
    def get_total_hours_from_timesheets(task_id: str) -> float:
        """Get total hours from all submitted timesheets for this task"""
        result = frappe.db.sql(f"""
            SELECT SUM(hours)
            FROM `tab{TaskRepository.DOCTYPE_TIMESHEET_DETAIL}`
            WHERE task = %s AND docstatus = %s
        """, (task_id, DocumentStatus.SUBMITTED.value))[0][0] or 0.0
        return float(result)

    @staticmethod
    def get_expected_time(task_id: str) -> float:
        """Get expected time from task"""
        task = frappe.get_doc(TaskRepository.DOCTYPE_NAME, task_id)
        return float(task.expected_time or 0)

    @staticmethod
    def create_buffer_task(subject: str) -> str:
        """Create a buffer/internal task"""
        return TaskRepository.create_task({
            "doctype": TaskRepository.DOCTYPE_NAME,
            "subject": subject,
            "status": TaskStatus.OPEN.value,
            TaskRepository.FIELD_IS_GENERIC: 1,
            TaskRepository.FIELD_IS_INTERNAL: 1,
        })
