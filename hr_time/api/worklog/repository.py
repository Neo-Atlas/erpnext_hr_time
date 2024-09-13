import frappe

class WorklogRepository:
    def get_worklogs(self, filters):
        return frappe.get_all("Worklog", filters=filters, fields=["name", "log_time", "task_desc", "task"])