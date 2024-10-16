import unittest
from unittest.mock import patch
from hr_time.api.worklog.api import has_employee_made_worklogs_today, create_worklog
from hr_time.api.worklog.repository import Worklog, WorklogRepository
from hr_time.api.worklog.service import WorklogService
from hr_time.api.shared.constants.messages import Messages


class TestWorklogAPI(unittest.TestCase):
    worklog: WorklogRepository
    service: WorklogService

    def setUp(self):
        super().setUp()
        self.worklog = WorklogRepository()
        self.service = WorklogService(self.worklog)

        # Patch the get_worklogs_of_employee_on_date method multiple tests in this class
        patcher_worklogs = patch('hr_time.api.flextime.processing.WorklogRepository.get_worklogs_of_employee_on_date')

        # Start the patch
        self.mock_get_worklogs_of_employee_on_date = patcher_worklogs.start()
        # Mock return value for WorklogRepository.get_worklogs_of_employee_on_date
        self.mock_get_worklogs_of_employee_on_date.return_value = [
            Worklog("001", "2023-11-19 08:00:00", "Task A", "T001"),
            Worklog("001", "2023-11-19 09:00:00", "Task B", "T002")
        ]

        # Add cleanup to stop patching after the test
        self.addCleanup(patcher_worklogs.stop)

    @patch('hr_time.api.worklog.service.WorklogService')
    def test_has_employee_made_worklogs_today_positive(self, MockWorklogService):
        # Arrange
        employee_id = '001'
        # Create a mock instance of WorklogService
        mock_service_instance = MockWorklogService.return_value
        # Mock the return value
        mock_service_instance.check_if_employee_has_worklogs_today.return_value = True

        # Act
        result = has_employee_made_worklogs_today(employee_id)

        # Assert
        self.assertTrue(result)
        mock_service_instance.check_if_employee_has_worklogs_today.assert_called_once_with(employee_id)

    @patch('hr_time.api.worklog.service.WorklogService')
    def test_has_employee_made_worklogs_today_negative(self, MockWorklogService):
        # Arrange
        employee_id = '001'
        # Create a mock instance of WorklogService
        mock_service_instance = MockWorklogService.return_value
        # Mock the return value
        mock_service_instance.check_if_employee_has_worklogs_today.return_value = False

        # Act
        result = has_employee_made_worklogs_today(employee_id)

        # Assert
        self.assertFalse(result)
        mock_service_instance.check_if_employee_has_worklogs_today.assert_called_once_with(employee_id)

    @patch('hr_time.api.worklog.service.WorklogService')
    def test_create_worklog_success(self, MockWorklogService):
        # Arrange
        employee_id = '001'
        worklog_text = 'Completed task A'
        task = 'TASK001'
        mock_service_instance = MockWorklogService.return_value
        mock_service_instance.create_worklog.return_value = {
            'status': 'success', 'message': Messages.Worklog.SUCCESS_WORKLOG_CREATION}

        # Act
        result = create_worklog(employee_id, worklog_text, task)

        # Assert
        self.assertEqual(result['status'], 'success')
        # Assert the message
        self.assertEqual(result['message'], Messages.Worklog.SUCCESS_WORKLOG_CREATION)
        mock_service_instance.create_worklog.assert_called_once_with(employee_id, worklog_text, task)

    def test_create_worklog_empty_description(self):
        # Arrange
        employee_id = '001'
        worklog_text = ''  # Empty Task description
        task = 'TASK001'

        # Act
        result = create_worklog(employee_id, worklog_text, task)

        # Assert
        self.assertEqual(result['status'], 'error')  # Expect an error status
        self.assertEqual(result['message'], "Task description must not be empty")   # Expect the error message

    @patch('hr_time.api.worklog.repository.WorklogRepository.create_worklog')
    def test_create_worklog_general_exception(self, mock_create_worklog):
        # Arrange
        employee_id = '001'
        worklog_text = 'Completed task B'
        task = 'TASK002'
        mock_create_worklog.side_effect = Exception("Database connection failed")  # Simulate a general exception

        # Act
        result = create_worklog(employee_id, worklog_text, task)

        # Assert
        self.assertEqual(result['status'], 'error')  # Expect an error status
        self.assertEqual(result['message'], "Database connection failed")   # Expect the error message
