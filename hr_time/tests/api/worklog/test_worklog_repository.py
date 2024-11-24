import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from hr_time.api.worklog.repository import WorklogRepository, Worklog
from hr_time.api.shared.constants.messages import Messages
from hr_time.api.shared.utils.response import Response


class TestWorklogRepository(unittest.TestCase):
    def setUp(self):
        self.repo = WorklogRepository()
        self.DUMMY_EMP_ID = 'EMP001'
        self.DUMMY_VALID_WORKLOG_TEXT = 'Completed task A'
        self.DUMMY_INVALID_WORKLOG_TEXT = ''
        self.DUMMY_TASK = 'TASK001'
        self.DUMMY_TICKET_LINK = 'github.com/PR/1'

    @patch('frappe.get_all')
    def test_get_worklogs(self, mock_get_all):
        # Arrange
        mock_data = [{'employee': self.DUMMY_EMP_ID, 'log_time': '2023-01-01 10:00:00',
                      'task_desc': 'Test Task', 'task': 'Task1', 'ticket_link': 'github.com/PR/1'}]
        # Define the mock method (lambda) to handle all fields defined in frappe framework
        mock_get_all.side_effect = lambda doctype, fields=None, filters=None, **kwargs: mock_data
        filters = {'employee': self.DUMMY_EMP_ID}

        # Act
        worklogs = self.repo.get_worklogs(filters)

        # Assert
        self.assertEqual(worklogs, mock_data)
        mock_get_all.assert_called_once_with(self.repo.get_doctype_name(),
                                             fields=self.repo.get_doc_fields(), filters=filters)

    @patch('frappe.get_all')
    def test_get_worklogs_of_employee_on_date(self, mock_get_all):
        # Arrange
        interested_date = datetime(2024, 10, 10).date()
        mock_data = [
            {'employee': self.DUMMY_EMP_ID, 'log_time': datetime(2024, 10, 10, 10, 10, 10),
             'task_desc': 'Worked on task 1', 'task': 'TASK001', 'ticket_link': 'github.com/PR/1'},
            {'employee': self.DUMMY_EMP_ID, 'log_time': datetime(2024, 10, 11, 10, 0, 0),
             'task_desc': 'Worked on task 2', 'task': 'TASK002', 'ticket_link': 'github.com/PR/2'},
        ]

        # Mocking frappe.get_all to simulate filtering by date
        mock_get_all.side_effect = lambda doctype, fields=None, filters=None: [
            entry for entry in mock_data
            if filters['employee'] == self.DUMMY_EMP_ID
            and filters['log_time'][1][0] <= entry['log_time'] <= filters['log_time'][1][1]
        ]

        # Act
        worklogs = self.repo.get_worklogs_of_employee_on_date(self.DUMMY_EMP_ID, interested_date)

        # Assert
        self.assertEqual(len(worklogs), 1)  # Expecting only one log entry for 2024-10-10
        self.assertIsInstance(worklogs[0], Worklog)
        self.assertEqual(worklogs[0].employee_id, self.DUMMY_EMP_ID)
        self.assertEqual(worklogs[0].task_desc, 'Worked on task 1')
        self.assertEqual(worklogs[0].task, 'TASK001')
        self.assertEqual(worklogs[0].ticket_link, 'github.com/PR/1')
        # Verifying if correct filters are applied
        mock_get_all.assert_called_once_with(
            self.repo.get_doctype_name(), fields=self.repo.get_doc_fields(),
            filters={
                'employee': self.DUMMY_EMP_ID,
                'log_time': ['between', [
                    datetime.combine(interested_date, datetime.min.time()), datetime.combine(
                        interested_date, datetime.max.time())
                ]]
            }
        )

    @patch('frappe.new_doc')
    def test_create_worklog_in_past(self, mock_new_doc):
        # Arrange
        mock_worklog_doc = MagicMock()
        mock_new_doc.return_value = mock_worklog_doc
        log_time = datetime.now() - timedelta(seconds=1)

        # Act
        result = self.repo.create_worklog(self.DUMMY_EMP_ID, log_time,
                                          self.DUMMY_VALID_WORKLOG_TEXT, self.DUMMY_TASK, self.DUMMY_TICKET_LINK)

        # Assert
        mock_new_doc.assert_called_once_with(self.repo.get_doctype_name())
        mock_worklog_doc.save.assert_called_once()
        self.assertEqual(result.status, Response.STATUS_SUCCESS)
        self.assertEqual(result.message, Messages.Worklog.SUCCESS_WORKLOG_CREATION)

    @patch('frappe.new_doc')
    def test_create_worklog_now(self, mock_new_doc):
        # Arrange
        mock_worklog_doc = MagicMock()
        mock_new_doc.return_value = mock_worklog_doc
        log_time = datetime.now()

        # Act
        result = self.repo.create_worklog(self.DUMMY_EMP_ID, log_time,
                                          self.DUMMY_VALID_WORKLOG_TEXT, self.DUMMY_TASK, self.DUMMY_TICKET_LINK)

        # Assert
        mock_new_doc.assert_called_once_with(self.repo.get_doctype_name())
        mock_worklog_doc.save.assert_called_once()
        self.assertEqual(result.status, Response.STATUS_SUCCESS)
        self.assertEqual(result.message, Messages.Worklog.SUCCESS_WORKLOG_CREATION)

    def test_create_worklog_in_future(self):
        # Arrange
        log_time = datetime.now() + timedelta(seconds=1)  # Set log_time to 1 second in the future

        # Act
        result = self.repo.create_worklog(self.DUMMY_EMP_ID, log_time,
                                          self.DUMMY_VALID_WORKLOG_TEXT, self.DUMMY_TASK, self.DUMMY_TICKET_LINK)

        # Assert
        # Check that the response indicates a validation error for future log time
        self.assertEqual(result.status, Response.STATUS_ERROR)
        self.assertEqual(result.message, Messages.Worklog.ERR_CREATE_WORKLOG_FUTURE_TIME)

    def test_create_worklog_empty_task_description(self):
        # Arrange
        log_time = datetime.now() - timedelta(seconds=1)  # Valid log time (in past)
        worklog_text = ''  # Empty worklog description

        # Act
        result = self.repo.create_worklog(self.DUMMY_EMP_ID, log_time, worklog_text)

        # Assert
        self.assertEqual(result.status, Response.STATUS_ERROR)
        self.assertEqual(result.message, Messages.Worklog.EMPTY_TASK_DESC)

    @patch('frappe.new_doc')
    @patch('frappe.db.rollback')
    def test_create_worklog_failure_db(self, mock_rollback, mock_new_doc):
        # Arrange
        mock_new_doc.side_effect = Exception(Messages.Common.ERR_DB)  # Simulate a DB error
        log_time = datetime(2024, 10, 10, 9, 0)

        # Act
        result = self.repo.create_worklog(self.DUMMY_EMP_ID, log_time,
                                          self.DUMMY_VALID_WORKLOG_TEXT, self.DUMMY_TASK, self.DUMMY_TICKET_LINK)

        # Assert
        # Check that result contains the expected error status and message
        self.assertEqual(result.status, Response.STATUS_ERROR)
        self.assertEqual(result.message, Messages.Common.ERR_DB)

        # Ensure rollback is called on failure
        mock_rollback.assert_called_once()
