import unittest
from unittest.mock import MagicMock, patch
from hr_time.api.worklog.service import WorklogService
from hr_time.api.worklog.repository import WorklogRepository

from hr_time.api.employee.repository import EmployeeRepository


class TestWorklogService(unittest.TestCase):
    worklog_service: WorklogService

    def setUp(self):
        super().setUp()
        self.worklog_repository = MagicMock(spec=WorklogRepository)
        self.worklog_service = WorklogService(self.worklog_repository)
        self.employee_repository = EmployeeRepository()

    def test_check_if_employee_has_worklogs_today_true(self):
        # Arrange
        employee_id = '001'
        # Simulate worklogs for today
        mock_worklogs = [{'id': '1', 'employee': employee_id}]
        self.worklog_repository.get_worklogs_of_employee_on_date.return_value = mock_worklogs

        # Act
        result = self.worklog_service.check_if_employee_has_worklogs_today(
            employee_id)

        # Assert
        self.assertTrue(result)  # Should return True if there are worklogs

    def test_check_if_employee_has_worklogs_today_false(self):
        # Arrange
        employee_id = '001'
        self.worklog_repository.get_worklogs_of_employee_on_date.return_value = []  # No worklogs

        # Act
        result = self.worklog_service.check_if_employee_has_worklogs_today(
            employee_id)

        # Assert
        # Should return False if there are no worklogs
        self.assertFalse(result)

    def test_create_worklog_success(self):
        # Arrange
        employee_id = '001'
        worklog_text = 'Completed task A'
        task = 'TASK001'
        expected_result = {'status': 'success',
                           'message': 'Worklog created successfully'}
        self.worklog_repository.create_worklog.return_value = expected_result

        # Act
        result = self.worklog_service.create_worklog(
            employee_id, worklog_text, task)

        # Assert
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['message'], 'Worklog created successfully')
        self.worklog_repository.create_worklog.assert_called_once()  # Verify it was called

    def test_create_worklog_empty_description(self):
        # Arrange
        employee_id = '001'
        worklog_text = ''  # Empty description
        task = 'TASK001'

        # Act
        result = self.worklog_service.create_worklog(
            employee_id, worklog_text, task)

        # Assert
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'],
                         "Worklog description cannot be empty")

    @patch('hr_time.api.worklog.service.get_current_employee_id')
    @patch('hr_time.api.worklog.repository.WorklogRepository')
    def test_create_worklog_with_none_employee_id(self, MockWorklogRepository, MockGetCurrentEmployeeId):
        # Arrange
        mock_worklog_repo = MockWorklogRepository.return_value
        MockGetCurrentEmployeeId.return_value = 'emp123'

        # Mock the return value of WorklogRepository.create_worklog to simulate a successful creation
        mock_worklog_repo.create_worklog.return_value = {
            'status': 'success',
            'message': 'Worklog created successfully'
        }

        service = WorklogService(mock_worklog_repo)
        worklog_text = "Worked on project X"
        task = "task_001"

        # Act
        result = service.create_worklog(
            employee_id=None, worklog_text=worklog_text, task=task)

        # Assert
        # Verify that get_current_employee_id was called
        MockGetCurrentEmployeeId.assert_called_once()

        # Check that create_worklog on repository was called with the correct parameters
        mock_worklog_repo.create_worklog.assert_called_once_with(
            'emp123',  # Current employee ID
            # log_time (it can be any datetime, so we use ANY)
            unittest.mock.ANY,
            worklog_text,
            task
        )

        # Verify the result is as expected
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['message'], 'Worklog created successfully')

    def test_create_worklog_general_exception(self):
        # Arrange
        employee_id = '001'
        worklog_text = 'Completed task B'
        task = 'TASK002'
        self.worklog_repository.create_worklog.side_effect = Exception(
            "Database error")

        # Act
        result = self.worklog_service.create_worklog(
            employee_id, worklog_text, task)

        # Assert
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], "Database error")
