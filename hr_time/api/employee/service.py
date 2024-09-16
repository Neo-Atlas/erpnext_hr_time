from hr_time.api.employee.repository import EmployeeRepository


class EmployeeService:
    def __init__(self, employee: EmployeeRepository):
        super().__init__()
        self.employee = employee

    @staticmethod
    def prod():
        return EmployeeService(EmployeeRepository())

    def get_current_employee(self):
        return self.employee.get_current()

    def get_current_employee_id(self):
        # Use the repository to check if the employee has any worklogs
        employee = self.employee.get_current()
        if employee:
            return employee.id
        return None
