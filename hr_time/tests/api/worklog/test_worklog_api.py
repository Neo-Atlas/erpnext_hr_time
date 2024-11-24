import json
import unittest
from unittest.mock import patch
from hr_time.api.worklog.api import has_employee_made_worklogs_today, create_worklog_now
from hr_time.api.shared.constants.messages import Messages
import frappe
from hr_time.api.shared.utils.response import Response


class TestWorklogAPI(unittest.TestCase):
    def setUp(self):
        # Arrange
        # Sample employeeID for testing
        self.DUMMY_EMP_ID = '001'
        self.DUMMY_VALID_WORKLOG_TEXT = 'Completed task A'
        self.DUMMY_TASK = 'TASK001'
        self.DUMMY_TICKET_LINK = 'https://github.com/Atlas-Neo/app/issues'
        self.DUMMY_INVALID_WORKLOG_TEXT = ''
        self.worklog = frappe.get_doc({
            "doctype": "Worklog"
        })

    @patch('hr_time.api.worklog.service.WorklogService.check_if_employee_has_worklogs_today')
    def test_has_employee_made_worklogs_today(self, mock_check_if_has_worklogs):
        # Define test cases with the mock return values and expected results
        test_cases = [
            (True, True),  # (mock return value, expected result)
            (False, False),
        ]

        for mock_return, expected in test_cases:
            mock_check_if_has_worklogs.side_effect = lambda x: mock_return

            # Act
            result = has_employee_made_worklogs_today(self.DUMMY_EMP_ID)

            # Assert
            self.assertEqual(result, expected)

    @patch('hr_time.api.worklog.service.WorklogService.create_worklog_now')
    def test_create_worklog_success(self, mock_create_worklog_now):
        # Test for success case
        # Arrange
        mock_create_worklog_now.side_effect = [
            Response.success(Messages.Worklog.SUCCESS_WORKLOG_CREATION)
        ]

        # Act
        result = create_worklog_now(self.DUMMY_EMP_ID, self.DUMMY_VALID_WORKLOG_TEXT,
                                    self.DUMMY_TASK, self.DUMMY_TICKET_LINK)
        result = json.loads(result)  # Parse JSON string to dictionary

        # Assert
        self.assertEqual(result['status'], Response.STATUS_SUCCESS)
        self.assertEqual(result['message'], Messages.Worklog.SUCCESS_WORKLOG_CREATION)
        mock_create_worklog_now.assert_called_once_with(
            self.DUMMY_EMP_ID, self.DUMMY_VALID_WORKLOG_TEXT, self.DUMMY_TASK, self.DUMMY_TICKET_LINK)

    def test_create_worklog_empty_description(self):
        # Act
        result = create_worklog_now(self.DUMMY_EMP_ID, self.DUMMY_INVALID_WORKLOG_TEXT,
                                    self.DUMMY_TASK, self.DUMMY_TICKET_LINK)
        result = json.loads(result)  # Parse JSON string to dictionary

        # Assert
        self.assertEqual(result['status'], Response.STATUS_ERROR)
        self.assertEqual(result['message'], Messages.Worklog.EMPTY_TASK_DESC)   # Expect the error message

    @patch('hr_time.api.worklog.repository.WorklogRepository.create_worklog')
    def test_create_worklog_general_exception(self, mock_create_worklog):
        # Arrange
        mock_create_worklog.side_effect = Exception(Messages.Common.ERR_DB_CONN)  # Simulate a general exception

        # Act
        result = create_worklog_now(self.DUMMY_EMP_ID, self.DUMMY_VALID_WORKLOG_TEXT,
                                    self.DUMMY_TASK, self.DUMMY_TICKET_LINK)
        result = json.loads(result)  # Parse JSON string to dictionary

        # Assert
        self.assertEqual(result['status'], Response.STATUS_ERROR)
        self.assertEqual(result['message'], Messages.Common.ERR_DB_CONN)   # Expect the error message

    @patch('hr_time.api.worklog.service.WorklogService.create_worklog_now')
    def test_response_format_success(self, mock_create_worklog_now):
        # Arrange
        mock_create_worklog_now.return_value = Response.success(Messages.Worklog.SUCCESS_WORKLOG_CREATION)

        # Act
        result = create_worklog_now(self.DUMMY_EMP_ID, self.DUMMY_VALID_WORKLOG_TEXT,
                                    self.DUMMY_TASK, self.DUMMY_TICKET_LINK)
        result_json = json.loads(result)  # Parse JSON string to dictionary

        # Assert
        self.assertIsInstance(result_json, dict)
        self.assertIn('status', result_json)
        self.assertIn('message', result_json)
        self.assertIn('data', result_json)  # 'data' can be None
        self.assertEqual(result_json['status'], Response.STATUS_SUCCESS)
        self.assertEqual(result_json['message'], Messages.Worklog.SUCCESS_WORKLOG_CREATION)

    @patch('hr_time.api.worklog.service.WorklogService.create_worklog_now')
    def test_response_format_error(self, mock_create_worklog_now):
        # Arrange
        mock_create_worklog_now.return_value = Response.error(Messages.Worklog.ERR_CREATE_WORKLOG)

        # Act
        result = create_worklog_now(self.DUMMY_EMP_ID, self.DUMMY_VALID_WORKLOG_TEXT,
                                    self.DUMMY_TASK, self.DUMMY_TICKET_LINK)
        result_json = json.loads(result)  # Parse JSON string to dictionary

        # Assert
        self.assertIsInstance(result_json, dict)
        self.assertIn('status', result_json)
        self.assertIn('message', result_json)
        self.assertIn('data', result_json)  # 'data' can be None
        self.assertEqual(result_json['status'], Response.STATUS_ERROR)
        self.assertEqual(result_json['message'], Messages.Worklog.ERR_CREATE_WORKLOG)
