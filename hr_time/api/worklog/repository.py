from datetime import datetime, time
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
        task (Optional[str]): Optional reference to a specific task (TASK doctype) related to the worklog.
        ticket_link (Optional[str]): Optional field to store (related) external ticket link.
    """

    employee_id: str
    log_time: datetime
    task_desc: str
    task: Optional[str]
    ticket_link: Optional[str]

    def __init__(
        self, employee_id: str, log_time: datetime, task_desc: str,
        task: Optional[str] = None, ticket_link: Optional[str] = None
    ):
        self.employee_id = employee_id
        self.log_time = log_time
        self.task_desc = task_desc
        self.task = task
        self.ticket_link = ticket_link


class WorklogRepository:
    """
    Repository class to manage operations related to worklog entries in the system.
    Handles retrieval and creation of worklogs.
    """

    _DOCTYPE_NAME = "Worklog"
    _DOC_FIELDS = ["employee", "log_time", "task_desc", "task", "ticket_link"]

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
            WorklogRepository.get_doctype_name(), fields=WorklogRepository.get_doc_fields(), filters=filters
        )

    def get_worklogs_of_employee_on_date(self, employee_id: str, date: datetime.date) -> List[Worklog]:
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

        # Fetch worklogs for the employee on the specific date (# Filter logtime by full day)
        docs = self.get_worklogs({"employee": employee_id, "log_time": ["between", [date_start, date_end]]})

        if not docs:
            return []

        for doc in docs:
            worklogs.append(self._build_from_doc(doc))

        return worklogs

    @staticmethod
    def create_worklog(
        employee_id: str, log_time: datetime, worklog_text: str,
        task: Optional[str] = None, ticket_link: Optional[str] = None
    ) -> Response:
        """
        Creates a new worklog entry for an employee.

        Args:
            employee_id (str): The ID of the employee creating the worklog.
            log_time (datetime.datetime): The date and time the worklog refers to.
            worklog_text (str): The content or description of the worklog.
            task (Optional[str]): Optional reference to a specific task associated with the worklog.
            ticket_link (Optional[str]): Optional field to store (related) external ticket link.

        Returns:
            Response: A Response object indicating the status of the operation.
                - If successful, the status will be 'success' with a success message.
                - If an error occurs, the status will be 'error' with a corresponding error message.


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
            new_worklog.task = task
            new_worklog.ticket_link = ticket_link
            new_worklog.save()

            return Response.success(Messages.Worklog.SUCCESS_WORKLOG_CREATION)

        except ValidationError as ve:
            # Handle validation error of log time being in future
            return Response.error(str(ve))

        except Exception as e:
            frappe.db.rollback()  # Rollback transaction in case of failure
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
            task=doc['task'],
            ticket_link=doc['ticket_link']
        )
