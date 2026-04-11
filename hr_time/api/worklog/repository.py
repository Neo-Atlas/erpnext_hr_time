from datetime import datetime, date, time
from typing import Optional, List
import frappe
from frappe import _, ValidationError
from hr_time.api.shared.constants.messages import Messages
from hr_time.api.shared.utils.response import Response


class Worklog:
    """
    Represents a worklog entry for an employee, including details about the task and the time of work.

    Attributes:
        employee_id (str): ID of the Employee for whom the Worklog is to be created.
        log_time (datetime.datetime): The date and time the worklog refers to.
        task_desc (str): A description of the task done.
        task (Optional[str]): (DEPRECATED field) Optional reference to a specific task (TASK doctype) related to the worklog.
        ticket_link (Optional[str]): Optional field to store (related) external ticket link.
        is_home_office (str): if the employee has worked from home (WFH).
    """

    employee_id: str
    log_time: datetime
    task_desc: str
    ticket_link: Optional[str]
    is_home_office: str

    def __init__(
        self, employee_id: str, log_time: datetime, task_desc: str,
        ticket_link: Optional[str] = None,
        is_home_office: str = "No",
        time_saved: float = 0,
        # checkin_events_json: str = "[]",
        # tolerance_minutes: int = 30
    ):
        self.employee_id = employee_id
        self.log_time = log_time
        self.task_desc = task_desc
        self.ticket_link = ticket_link
        self.is_home_office = is_home_office
        self.time_saved = time_saved
        # self.checkin_events_json = checkin_events_json
        # self.tolerance_minutes = tolerance_minutes


class WorklogRepository:
    """
    Repository class to manage operations related to worklog entries in the system.
    Handles retrieval and creation of worklogs.
    """

    _DOCTYPE_NAME = "Worklog"
    _DOC_FIELDS = [
        "employee", "log_time", "task_desc", "ticket_link",
        "is_home_office", "time_saved", "timesheet"
        # "checkin_events_json", "tolerance_minutes", "time_allocated", "time_unallocated",
    ]

    @staticmethod
    def get_doctype_name() -> str:
        """Returns the pre-defined DocType name."""
        return WorklogRepository._DOCTYPE_NAME

    @staticmethod
    def get_doc_fields() -> List[str]:
        """
        Returns a copy of the document fields.

        Returns:
            List[str]: List of field names used in worklog documents.
        """
        return WorklogRepository._DOC_FIELDS.copy()

    def get_worklogs(self, filters: dict) -> List[dict]:
        """
        Retrieves worklogs from the database based on given filters.

        Args:
            filters (dict): Dictionary of filters to apply for retrieving worklogs.

        Returns:
            List[dict]: A list of worklog entries matching the given filters.
        """
        return frappe.get_all(
            WorklogRepository.get_doctype_name(),
            fields=WorklogRepository.get_doc_fields(),
            filters=filters
        )

    def get_worklogs_of_employee_on_date(
            self, employee_id: str, date: datetime.date) -> List[Worklog]:
        """
        Retrieves all worklogs for a specific employee on a given date.

        Args:
            employee_id (str): ID of the employee whose worklogs are being retrieved.
            date (datetime.date): The specific date for which to retrieve worklogs.

        Returns:
            List[Worklog]: A list of worklogs for the employee on the specified date.
        """
        worklogs = []
        # Define the date filter to include the whole day (date_start to date_end)
        date_start = datetime.combine(date, time(0, 0, 0))
        date_end = datetime.combine(date, time(23, 59, 59, 999999))

        # Fetch worklogs for the employee on the specific date
        # (Filter logtime by full day)
        docs = self.get_worklogs({
            "employee": employee_id,
            "log_time": ["between", [date_start, date_end]]
        })

        for doc in docs:
            worklogs.append(self._build_from_doc(doc))

        return worklogs

    @staticmethod
    def get_todays_worklog(employee_id: str) -> Optional[dict]:
        """Get today's worklog if exists"""
        today = date.today()
        # SELECT name, time_saved, docstatus, owner
        docs = frappe.db.sql("""
            SELECT name, time_saved, docstatus, owner
            FROM `tabWorklog`
            WHERE employee = %s
            AND DATE(log_time) = %s
            ORDER BY creation DESC
            LIMIT 1
        """, (employee_id, today), as_dict=True)

        return docs[0] if docs else None

    @staticmethod
    def create_worklog(
        employee_id: str,
        log_time: datetime,
        worklog_text: str,
        ticket_link: Optional[str] = None,
        is_home_office: str = "No",
        time_saved: float = 0,
        tasks_entry: List[dict] = None,
        current_total: float = None  # passed from API
    ) -> Response:
        """
        Creates a new worklog entry for an employee.

        Args:
            employee_id (str): The ID of the employee creating the worklog.
            log_time (datetime.datetime): The date and time the worklog
                refers to.
            worklog_text (str): The content or description of the worklog.
            ticket_link (Optional[str]): Optional field to store (related)
                external ticket link.
            is_home_office (str): Is the work done from Home - Yes/No. Default
                is "No".
            time_saved (float): sth,
            tasks_entry (List[dict]): sth,
            current_total (float): (time_saved + time_since_last_save)

        Returns:
            Response: A Response object indicating the status of the operation
                - If successful, the status will be 'success' with a success
                    message.
                - If an error occurs, the status will be 'error' with a
                    corresponding error message.

        Raises:
            ValidationError: If log_time is set in the future.
            Exception: For other errors during Worklog creation.
        """

        try:
            if not worklog_text:
                return Response.error(Messages.Worklog.EMPTY_TASK_DESC)

            if log_time > datetime.now():
                raise ValidationError(Messages.Worklog.ERR_CREATE_WORKLOG_FUTURE_TIME)

            new_worklog = frappe.new_doc(WorklogRepository.get_doctype_name())
            new_worklog.employee = employee_id
            new_worklog.log_time = log_time
            new_worklog.task_desc = worklog_text
            new_worklog.ticket_link = ticket_link
            new_worklog.is_home_office = is_home_office
            new_worklog.time_saved = time_saved
            # Store current_total transient attribute for validation (not saved to DB)
            new_worklog.__current_total = current_total

            # Add task allocations if provided
            if tasks_entry:
                for task_row in tasks_entry:
                    row = new_worklog.append("tasks_entry", {})
                    row.task = task_row.get("task")
                    row.task_subject = task_row.get("task_subject")
                    row.expected_time = task_row.get("expected_time", 0)
                    row.time_spent = task_row.get("time_spent", 0)
                    row.progress_increment = task_row.get("progress_increment", 0)
                    row.task_status = task_row.get("task_status")

            new_worklog.save()

            return Response.success(
                Messages.Worklog.SUCCESS_WORKLOG_CREATION,
                {"name": new_worklog.name}
            )

        except ValidationError as ve:
            # Handle validation error of log time being in future
            return Response.error(str(ve))

        except Exception as e:
            frappe.db.rollback()  # Rollback transaction in case of failure
            return Response.error(str(e))

    @staticmethod
    def update_worklog_tasks(worklog_name: str, tasks_entry: List[dict]) -> Response:
        """Update task allocations for existing worklog"""
        try:
            worklog = frappe.get_doc("Worklog", worklog_name)

            # Clear existing tasks
            worklog.set("tasks_entry", [])

            # Add updated tasks
            for task_row in tasks_entry:
                row = worklog.append("tasks_entry", {})
                row.task = task_row.get("task")
                row.task_subject = task_row.get("task_subject")
                row.expected_time = task_row.get("expected_time", 0)
                row.time_spent = task_row.get("time_spent", 0)
                row.progress_increment = task_row.get("progress_increment", 0)
                row.task_status = task_row.get("task_status")

            worklog.save()
            return Response.success("Worklog updated successfully")
            
        except Exception as e:
            frappe.db.rollback()
            return Response.error(str(e))

    @staticmethod
    def _build_from_doc(doc) -> Worklog:
        """
        Builds a Worklog object from a database document.

        Args:
            doc (dict): A dictionary representing a Worklog document from the database.

        Returns:
            Worklog: A Worklog object created from the document data.
        """
        return Worklog(
            employee_id=doc['employee'],
            log_time=doc['log_time'],
            task_desc=doc['task_desc'],
            ticket_link=doc.get('ticket_link'),
            is_home_office=doc.get('is_home_office', "No"),
            time_saved=doc.get('time_saved', 0),
            # checkin_events_json=doc.get('checkin_events_json', "[]"),
            # tolerance_minutes=doc.get('tolerance_minutes', 30)
        )
