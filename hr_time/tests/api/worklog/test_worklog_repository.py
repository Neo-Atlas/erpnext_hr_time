import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from hr_time.api.worklog.repository import WorklogRepository, Worklog
from hr_time.api.shared.constants.messages import Messages


class TestWorklogRepository(unittest.TestCase):
    def setUp(self):
        self.repo = WorklogRepository()

    @patch('hr_time.api.employee.repository.frappe.get_all')
    def test_get_worklogs(self, mock_get_all):
        # Arrange
        mock_get_all.side_effect = lambda filters: [
            {'employee': 'EMP001', 'log_time': datetime(
                2024, 1, 1, 9, 0, 0), 'task_desc': 'Test task 1', 'task': 'TASK001'}
        ] if filters == {'employee': 'EMP001'} else [
            {'employee': 'EMP002', 'log_time': datetime(
                2024, 1, 2, 10, 30, 0), 'task_desc': 'Test task 2', 'task': 'TASK002'}
        ]
        filters = {'employee': 'EMP001'}

        # Act
        worklogs = self.repo.get_worklogs(filters)

        # Assert
        self.assertEqual(len(worklogs), 1)
        self.assertEqual(worklogs[0]['employee'], 'EMP001')
        mock_get_all.assert_called_once_with("Worklog", fields=self.repo.doc_fields, filters=filters)

    @patch('hr_time.api.worklog.repository.frappe.get_all')
    def test_get_worklogs_of_employee_on_date(self, mock_get_all):
        # Arrange
        mock_get_all.return_value = [
            {'employee': 'EMP001', 'log_time': datetime(
                2024, 10, 10, 10, 10, 10), 'task_desc': 'Worked on task 1', 'task': 'TASK001'},
            {'employee': 'EMP001', 'log_time': datetime(
                2024, 10, 10, 11, 0, 0), 'task_desc': 'Worked on task 2', 'task': 'TASK002'},
        ]
        employee_id = 'EMP001'
        date = datetime(2024, 10, 10).date()

        # Act
        worklogs = self.repo.get_worklogs_of_employee_on_date(employee_id, date)

        # Assert
        self.assertEqual(len(worklogs), 2)
        self.assertIsInstance(worklogs[0], Worklog)
        self.assertEqual(worklogs[0].employee_id, 'EMP001')
        self.assertEqual(worklogs[0].task_desc, 'Worked on task 1')

        # Check that the correct filters were applied
        mock_get_all.assert_called_once_with("Worklog", fields=self.repo.doc_fields, filters={
            "employee": employee_id,
            "log_time": ["between", [datetime.combine(date, datetime.min.time()),
                                     datetime.combine(date, datetime.max.time())]]
        })

    @patch('hr_time.api.worklog.repository.frappe.new_doc')
    @patch('hr_time.api.worklog.repository.frappe.db.commit')
    def test_create_worklog_success(self, mock_commit, mock_new_doc):
        # Arrange
        mock_worklog_doc = MagicMock()
        mock_new_doc.return_value = mock_worklog_doc
        employee_id = 'EMP001'
        log_time = datetime(2024, 10, 10, 9, 0)
        worklog_text = 'Completed task'
        task = 'TASK001'

        # Act
        result = self.repo.create_worklog(employee_id, log_time, worklog_text, task)

        # Assert
        mock_new_doc.assert_called_once_with("Worklog")
        mock_worklog_doc.save.assert_called_once()
        mock_commit.assert_called_once()
        self.assertEqual(result, {'status': 'success', 'message': Messages.Worklog.SUCCESS_WORKLOG_CREATION})

    @patch('hr_time.api.worklog.repository.frappe.new_doc')
    @patch('hr_time.api.worklog.repository.frappe.db.rollback')
    def test_create_worklog_failure(self, mock_rollback, mock_new_doc):
        # Arrange
        mock_new_doc.side_effect = Exception(Messages.Common.ERR_DB)
        employee_id = 'EMP001'
        log_time = datetime(2024, 10, 10, 9, 0)
        worklog_text = 'Completed task'
        task = 'TASK001'

        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.repo.create_worklog(employee_id, log_time, worklog_text, task)
        # Ensure the exception contains the ERR_DB message
        self.assertEqual(str(context.exception), Messages.Common.ERR_DB)
        # Ensure rollback is called on failure
        mock_rollback.assert_called_once()
