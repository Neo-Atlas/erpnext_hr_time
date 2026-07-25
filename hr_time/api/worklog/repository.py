from datetime import datetime, time
from typing import Optional, List

import frappe
from frappe import _

from hr_time.api.worklog.domain.entities import WorklogEntity, TaskAllocation
from hr_time.api.shared.domain.document_status import DocumentStatus


class Worklog:
    """
    @deprecated: This class is deprecated and will be removed in future versions.
    Please use hr_time.api.worklog.entity.WorklogEntity instead for domain modelling.

    Represents a worklog entry for an employee, including details about the task and the time of work.

    Attributes:
        employee_id (str): ID of the Employee for whom the Worklog is to be created.
        log_time (datetime.datetime): The date and time the worklog refers to.
        work_desc (str): A summary of the work done.
        ticket_link (Optional[str]): Optional field to store (related) external ticket link.
        is_home_office (str): if the employee has worked from home (WFH).
    """

    employee_id: str
    log_time: datetime
    work_desc: str
    ticket_link: Optional[str]
    is_home_office: str

    def __init__(
        self, employee_id: str, log_time: datetime, work_desc: str,
        ticket_link: Optional[str] = None,
        is_home_office: str = "No",
        time_saved: float = 0
    ):
        self.employee_id = employee_id
        self.log_time = log_time
        self.work_desc = work_desc
        self.ticket_link = ticket_link
        self.is_home_office = is_home_office
        self.time_saved = time_saved


class WorklogRepository:
    """
    Repository class to manage operations related to worklog entries in the system.
    Handles retrieval and creation of worklogs.
    """

    DOCTYPE_NAME = "Worklog"
    _DOC_FIELDS = [
        "employee", "log_time", "work_desc", "ticket_link",
        "is_home_office", "time_saved", "timesheet"
    ]

    # ============ QUERY METHODS ============

    def get_worklogs(self, filters: dict) -> List[dict]:
        """
        Retrieves worklogs from the database based on given filters.

        Args:
            filters (dict): Dictionary of filters to apply for retrieving worklogs.

        Returns:
            List[dict]: A list of worklog entries matching the given filters.
        """
        return frappe.get_all(
            self.DOCTYPE_NAME,
            fields=self._DOC_FIELDS.copy(),
            filters=filters
        )

    def get_worklogs_of_employee_on_date(
        self, employee_id: str, date: datetime.date
    ) -> List[WorklogEntity]:
        """
        Retrieves all worklogs for a specific employee on a given date as entities.

        Args:
            employee_id (str): ID of the employee whose worklogs are being retrieved.
            date (datetime.date): The specific date for which to retrieve worklogs.

        Returns:
            List[Worklog]: A list of WorklogEntity for the employee on the specified date.
        """
        # Define the date filter to include the whole day (date_start to date_end)
        date_start = datetime.combine(date, time(0, 0, 0))
        date_end = datetime.combine(date, time(23, 59, 59, 999999))

        # Fetch worklogs for the employee on the specific date
        # (Filter logtime by full day)
        docs = self.get_worklogs({
            "employee": employee_id,
            "log_time": ["between", [date_start, date_end]]
        })

        return [
            self._to_entity(frappe.get_doc(self.DOCTYPE_NAME, doc["name"]))
            for doc in docs
        ]

    @staticmethod
    def get_todays_worklog_dict(employee_id: str) -> Optional[dict]:
        """Get today's worklog if exists"""

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)

        docs = frappe.db.get_all(
            WorklogRepository.DOCTYPE_NAME,
            filters={
                'employee': employee_id,
                'log_time': ['between', [today_start, today_end]]
            },
            fields=['name', 'time_saved', 'docstatus', 'owner'],
            order_by='creation desc',
            limit=1
        )

        return docs[0] if docs else None

    def get_todays_worklog_entity(self, employee_id: str) -> Optional[WorklogEntity]:
        """Get today's worklog as domain entity."""
        doc_dict = self.get_todays_worklog_dict(employee_id)
        if not doc_dict:
            return None
        return self._to_entity(frappe.get_doc(WorklogRepository.DOCTYPE_NAME, doc_dict["name"]))

    def get_by_id(self, worklog_id: str) -> Optional[WorklogEntity]:
        """Get worklog by ID as domain entity"""
        if not frappe.db.exists(WorklogRepository.DOCTYPE_NAME, worklog_id):
            return None
        doc = frappe.get_doc(WorklogRepository.DOCTYPE_NAME, worklog_id)
        return self._to_entity(doc)

    # ============ CONVERSION METHODS ============

    def _to_entity(self, doc) -> WorklogEntity:
        """Convert Frappe doc to WorklogEntity"""
        allocations = []
        for task_row in doc.tasks_entry:
            allocations.append(TaskAllocation(
                task_id=task_row.task,
                subject=task_row.subject or "",
                time_spent=float(task_row.time_spent or 0),
                expected_time=float(task_row.expected_time or 0),
                progress_increment=float(task_row.progress_increment or 0),
                status=task_row.status or "",
                priority=task_row.priority or "",
                task_desc=task_row.task_desc or "",
            ))

        return WorklogEntity(
            id=doc.name,
            employee_id=doc.employee,
            log_time=doc.log_time,
            work_desc=doc.work_desc,
            time_saved=float(doc.time_saved or 0),
            is_home_office=doc.is_home_office == "Yes",
            ticket_link=doc.ticket_link,
            docstatus=DocumentStatus(doc.docstatus),
            timesheet_id=doc.timesheet,
            allocations=allocations,
        )

    # ============ SAVE METHODS ============

    def save_from_dict(
        self,
        worklog_name: Optional[str],
        worklog_data: dict,
        current_total: float,
        employee_id: str
    ) -> str:
        """
        Save worklog from dictionary data.

        Args:
            worklog_name: Existing worklog name (None for new)
            worklog_data: Dictionary with worklog data
            current_total: Current total hours (for validation)
            employee_id: Employee ID for new worklogs

        Returns:
            Name of saved worklog
        """
        if worklog_name:
            doc = frappe.get_doc(self.DOCTYPE_NAME, worklog_name)
        else:
            doc = frappe.new_doc(self.DOCTYPE_NAME)
            doc.employee = employee_id

        # setting transient attribute for validation
        doc.__current_total = current_total

        # Update simple fields
        doc.time_saved = worklog_data.get('time_saved', doc.time_saved)
        doc.work_desc = worklog_data.get('work_desc', doc.work_desc or '')
        doc.is_home_office = worklog_data.get('is_home_office', doc.is_home_office or 'No')
        doc.ticket_link = worklog_data.get('ticket_link', doc.ticket_link or '')

        # Handle child table
        if 'tasks_entry' in worklog_data:
            doc.set('tasks_entry', [])
            for task in worklog_data['tasks_entry']:
                doc.append('tasks_entry', {
                    'task': task.get('task'),
                    'task_subject': task.get('subject', ''),
                    'task_status': task.get('status', ''),
                    'expected_time': task.get('expected_time', 0),
                    'priority': task.get('priority', ''),
                    'time_spent': task.get('time_spent', 0),
                    'task_desc': task.get('task_desc', ''),
                    'progress_increment': task.get('progress_increment', 0),
                })

        # Save the document
        if worklog_name:
            doc.save()
        else:
            doc.insert()

        frappe.db.commit()
        return doc.name
