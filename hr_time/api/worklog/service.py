
import datetime
from hr_time.api.worklog.repository import WorklogRepository
from hr_time.api.employee.api import get_current_employee_id
from hr_time.api import logger
from hr_time.api.shared.constants.messages import Messages


class WorklogService:
    """
    Service layer for managing operations related to employee worklogs.
    Provides methods to check for existing worklogs and to create new worklogs using the WorklogRepository.

    Attributes:
        worklog (WorklogRepository): Repository instance used for interacting with Worklog doctype table.
    """
    worklog: WorklogRepository

    def __init__(self, worklog: WorklogRepository):
        """
        Initializes the WorklogService with a given WorklogRepository.

        Args:
            worklog (WorklogRepository): Repository for worklog operations.
        """
        super().__init__()
        self.worklog = worklog

    @staticmethod
    def prod() -> 'WorklogService':
        """
        Creates a production instance of WorklogService with a default WorklogRepository.

        Returns:
            WorklogService: An initialized WorklogService instance for production use.
        """
        return WorklogService(WorklogRepository())

    def check_if_employee_has_worklogs_today(self, employee_id) -> bool:
        """
        Checks if the specified employee has created any worklogs today.

        Args:
            employee_id (str): The ID of the employee whose worklogs are being checked.

        Returns:
            bool: True if the employee has worklogs for the current day, False otherwise.
        """
        today = datetime.date.today()
        worklogs = self.worklog.get_worklogs_of_employee_on_date(employee_id, today)
        return len(worklogs) > 0

    def create_worklog(self, employee_id=None, worklog_text='', task=None):
        """
        Creates a new worklog for an employee with the given description and optional task reference.

        Args:
            employee_id (Optional[str], optional): The ID of the employee creating the worklog.
            If None, the current employee ID is used. Defaults to None.
            worklog_text (str): The description of the task performed in the worklog.
            task (Optional[str], optional): Optional reference to a specific task associated with the worklog.
            Defaults to None.

        Returns:
            dict: A dictionary indicating the success or failure of the worklog creation process.

        Raises:
            ValueError: If the task description is empty.
        """
        try:
            if employee_id is None:
                employee_id = get_current_employee_id()
            if not worklog_text.strip():
                raise ValueError(Messages.Worklog.EMPTY_TASK_DESC)

            log_time = datetime.datetime.now()  # Get current time as log_time
            # Call repository to create the worklog
            result = self.worklog.create_worklog(employee_id, log_time, worklog_text, task)

            return result

        except ValueError as ve:
            # Handle specific ValueError
            logger.error(f"Validation error: {str(ve)}", 'Worklog Creation Error')
            return {'status': 'error', 'message': str(ve)}

        except Exception as e:
            # Centralized error handling and logging
            logger.error(f"Error creating worklog: {str(e)}", 'Worklog Creation Error')
            return {'status': 'error', 'message': str(e)}
