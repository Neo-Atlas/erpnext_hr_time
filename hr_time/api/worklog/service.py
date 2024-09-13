
import datetime
from hr_time.api.worklog.repository import WorklogRepository
from frappe.utils import nowdate

class WorklogService:
    worklog: WorklogRepository

    def __init__(self, worklog: WorklogRepository):
        super().__init__()
        self.worklog = worklog

    @staticmethod
    def prod():
        return WorklogService(WorklogRepository())

    def check_if_employee_has_worklogs_today(self, employee_id):
        # Use the repository to check if the employee has any worklogs
        today = datetime.date.today()
        worklogs = self.get_worklogs_for_employee_on_date(employee_id, today)
        return len(worklogs) > 0

    def get_all_worklogs(self):
        return self.worklog.get_worklogs(filters=None)

    def get_worklogs_for_employee(self, employee_id):
        return self.worklog.get_worklogs(filters={
                    "employee": employee_id,
                })

    def get_worklogs_for_employee_on_date(self, employee_id, date):
        date_str = date
        # Check if the input is a date object and format it accordingly to a string in the format 'YYYY-MM-DD' 
        if isinstance(date, datetime.date):
            date_str = date.strftime('%Y-%m-%d')
        
        return self.worklog.get_worklogs(filters={
                        "employee": employee_id,
                        "log_time": ["between", [date_str + " 00:00:00", date_str + " 23:59:59"]]
                    })