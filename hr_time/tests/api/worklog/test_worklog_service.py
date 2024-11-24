import unittest
from unittest.mock import MagicMock, patch
from hr_time.api.worklog.service import WorklogService
from hr_time.api.worklog.repository import WorklogRepository
from hr_time.api.shared.constants.messages import Messages
from hr_time.api.shared.utils.response import Response


class TestWorklogService(unittest.TestCase):
    worklog_service: WorklogService

    def setUp(self):
        super().setUp()
        # Arrange
        self.DUMMY_EMP_ID = '001'
        self.DUMMY_VALID_WORKLOG_TEXT = 'Completed task A'
        self.DUMMY_INVALID_EMPTY_WORKLOG_TEXT = ''
        self.DUMMY_TASK = 'TASK001'
        self.DUMMY_TICKET_LINK = 'https://github.com/Atlas-Neo/app/issues'
        self.worklog_repository = MagicMock(spec=WorklogRepository)
        self.worklog_service = WorklogService(self.worklog_repository)

    def test_check_if_employee_has_worklogs_today_true(self):
        # Arrange
        # Simulate worklogs for today
        mock_worklogs = [{'id': '1', 'employee': self.DUMMY_EMP_ID}]
        self.worklog_repository.get_worklogs_of_employee_on_date.return_value = mock_worklogs

        # Act
        result = self.worklog_service.check_if_employee_has_worklogs_today(self.DUMMY_EMP_ID)

        # Assert
        self.assertTrue(result)  # Should return True if there are worklogs

    def test_check_if_employee_has_worklogs_today_false(self):
        # Arrange
        self.worklog_repository.get_worklogs_of_employee_on_date.return_value = []  # No worklogs

        # Act
        result = self.worklog_service.check_if_employee_has_worklogs_today(self.DUMMY_EMP_ID)

        # Assert
        self.assertFalse(result)

    def test_create_worklog_success(self):
        # Arrange
        expected_result = Response.success(Messages.Worklog.SUCCESS_WORKLOG_CREATION)
        self.worklog_repository.create_worklog.return_value = expected_result

        # Act
        result = self.worklog_service.create_worklog_now(
            self.DUMMY_EMP_ID, self.DUMMY_VALID_WORKLOG_TEXT, self.DUMMY_TASK, self.DUMMY_TICKET_LINK)

        # Assert
        # Verify create_worklog was called
        self.worklog_repository.create_worklog.assert_called_once()
        self.assertEqual(result.status, Response.STATUS_SUCCESS)
        self.assertEqual(result.message, Messages.Worklog.SUCCESS_WORKLOG_CREATION)

    def test_create_worklog_empty_description(self):
        # Act
        result = self.worklog_service.create_worklog_now(
            self.DUMMY_EMP_ID, self.DUMMY_INVALID_EMPTY_WORKLOG_TEXT, self.DUMMY_TASK, self.DUMMY_TICKET_LINK)

        # Assert
        self.assertEqual(result.status, Response.STATUS_ERROR)
        self.assertEqual(result.message, Messages.Worklog.EMPTY_TASK_DESC)

    @patch('hr_time.api.worklog.service.get_current_employee_id')
    def test_create_worklog_with_none_employee_id(self, mock_get_current_emp_id):
        # Arrange
        mock_get_current_emp_id.return_value = 'emp123'
        # Mock the return value of create_worklog to simulate a successful creation
        expected_result = Response.success(Messages.Worklog.SUCCESS_WORKLOG_CREATION)
        self.worklog_repository.create_worklog.return_value = expected_result

        # Act
        result = self.worklog_service.create_worklog_now(
            employee_id=None, worklog_text=self.DUMMY_VALID_WORKLOG_TEXT,
            task=self.DUMMY_TASK, ticket_link=self.DUMMY_TICKET_LINK)

        # Assert
        # Verify that get_current_employee_id was called
        mock_get_current_emp_id.assert_called_once()

        # Check that create_worklog on repository was called with the correct parameters
        # i.e. (Current employee ID, ANY date, worklog_text, task)
        self.worklog_repository.create_worklog.assert_called_once_with(
            'emp123', unittest.mock.ANY, self.DUMMY_VALID_WORKLOG_TEXT, self.DUMMY_TASK, self.DUMMY_TICKET_LINK)

        # Verify the result is as expected
        self.assertEqual(result.status, Response.STATUS_SUCCESS)
        self.assertEqual(result.message, Messages.Worklog.SUCCESS_WORKLOG_CREATION)

    def test_create_worklog_general_exception(self):
        # Arrange
        self.worklog_repository.create_worklog.side_effect = Exception(Messages.Common.ERR_DB)

        # Act
        result = self.worklog_service.create_worklog_now(
            self.DUMMY_EMP_ID, self.DUMMY_VALID_WORKLOG_TEXT, self.DUMMY_TASK, self.DUMMY_TICKET_LINK)

        # Assert
        self.assertEqual(result.status, Response.STATUS_ERROR)
        self.assertEqual(result.message, Messages.Common.ERR_DB)
