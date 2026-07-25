import unittest
from unittest.mock import MagicMock, patch
from datetime import date, datetime

from hr_time.api.worklog.service import WorklogService
from hr_time.api.worklog.repository import WorklogRepository
from hr_time.api.hr_settings.repository import HRSettingsRepository
from hr_time.api.check_in.service import CheckinService
from hr_time.api.worklog.domain.task.repository import TaskRepository
from hr_time.api.worklog.domain.task.task_progress_service import TaskProgressService
from hr_time.api.worklog.infrastructure.timesheet.service import TimesheetService
from hr_time.api.worklog.infrastructure.services.session_service import SessionService


class TestWorklogService(unittest.TestCase):
    """Tests for WorklogService (remaining methods after refactor)"""

    def setUp(self):
        self.employee_id = "EMP001"
        self.worklog_repo = MagicMock(spec=WorklogRepository)
        self.hr_settings = MagicMock(spec=HRSettingsRepository)
        self.task_repo = MagicMock(spec=TaskRepository)
        self.task_progress_service = MagicMock(spec=TaskProgressService)
        self.timesheet_service = MagicMock(spec=TimesheetService)
        self.session_service = MagicMock(spec=SessionService)
        self.checkin_service = MagicMock(spec=CheckinService)

        self.service = WorklogService(
            worklog_repo=self.worklog_repo,
            hr_settings=self.hr_settings,
            task_repo=self.task_repo,
            task_progress_service=self.task_progress_service,
            timesheet_service=self.timesheet_service,
            session_service=self.session_service,
            checkin_service=self.checkin_service,
        )

    # ============ test prod() factory method ============

    @patch('hr_time.api.worklog.service.WorklogRepository')
    @patch('hr_time.api.worklog.service.HRSettingsRepository')
    @patch('hr_time.api.worklog.service.TaskRepository')
    @patch('hr_time.api.worklog.service.TaskProgressService')
    @patch('hr_time.api.worklog.service.TimesheetService')
    @patch('hr_time.api.worklog.service.SessionService')
    @patch('hr_time.api.worklog.service.CheckinService')
    def test_prod_returns_instance(
        self,
        mock_checkin,
        mock_session,
        mock_timesheet,
        mock_task_progress,
        mock_task_repo,
        mock_hr_settings,
        mock_worklog_repo
    ):
        """Should return a configured WorklogService instance"""
        mock_checkin.prod.return_value = MagicMock()

        result = WorklogService.prod()

        self.assertIsInstance(result, WorklogService)
        mock_worklog_repo.assert_called_once()
        mock_hr_settings.assert_called_once()
        mock_task_repo.assert_called_once()

    # ============ test check_if_employee_has_worklogs_today ============

    def test_check_if_employee_has_worklogs_today_returns_true(self):
        """Should return True when worklogs exist for today"""
        # Arrange
        mock_worklogs = [MagicMock(), MagicMock()]
        self.worklog_repo.get_worklogs_of_employee_on_date.return_value = mock_worklogs

        # Act
        result = self.service.check_if_employee_has_worklogs_today(self.employee_id)

        # Assert
        self.assertTrue(result)
        self.worklog_repo.get_worklogs_of_employee_on_date.assert_called_once_with(
            self.employee_id, date.today()
        )

    def test_check_if_employee_has_worklogs_today_returns_false(self):
        """Should return False when no worklogs exist for today"""
        # Arrange
        self.worklog_repo.get_worklogs_of_employee_on_date.return_value = []

        # Act
        result = self.service.check_if_employee_has_worklogs_today(self.employee_id)

        # Assert
        self.assertFalse(result)

    # ============ test calculate_task_progress_increments ============

    def test_calculate_task_progress_increments_delegates(self):
        """Should delegate to task_progress_service"""
        # Arrange
        mock_doc = MagicMock()

        # Act
        self.service.calculate_task_progress_increments(mock_doc)

        # Assert
        self.task_progress_service.calculate_progress_increments_for_worklog.assert_called_once_with(mock_doc)

    # ============ test process_worklog_save ============

    @patch('hr_time.api.worklog.service.FrappeUtils.success_modal')
    def test_process_worklog_save_creates_new_timesheet(self, mock_success_modal):
        """Should create new timesheet when none exists"""
        # Arrange
        mock_doc = MagicMock()
        mock_doc.employee = self.employee_id
        mock_doc.log_time = datetime.now()
        mock_doc.time_saved = 2.5
        mock_doc.tasks_entry = [MagicMock(task="TASK-001", time_spent=2.0)]
        mock_doc.db_set = MagicMock()

        self.timesheet_service.get_todays_timesheet.return_value = None
        self.session_service.get_session_times.return_value = (datetime.now(), None)
        self.hr_settings.get_default_activity_type.return_value = "Development"
        self.hr_settings.get_buffer_task.return_value = "BUFFER-001"

        # Create a mock timesheet with a name attribute
        mock_timesheet = MagicMock()
        mock_timesheet.name = "TS-001"
        self.timesheet_service.create_from_worklog.return_value = mock_timesheet

        # Act
        result = self.service.process_worklog_save(mock_doc)

        # Assert
        self.assertIsNotNone(result)
        self.timesheet_service.create_from_worklog.assert_called_once()
        mock_doc.db_set.assert_called_once_with("timesheet", "TS-001")
        self.task_progress_service.update_worklog_task_progress.assert_called_once_with(mock_doc)

    @patch('hr_time.api.worklog.service.FrappeUtils.success_modal')
    def test_process_worklog_save_replaces_existing_timesheet(self, mock_success_modal):
        """Should replace existing timesheet when one exists"""
        # Arrange
        mock_doc = MagicMock()
        mock_doc.employee = self.employee_id
        mock_doc.log_time = datetime.now()
        mock_doc.time_saved = 2.5
        mock_doc.tasks_entry = [MagicMock(task="TASK-001", time_spent=2.0)]
        mock_doc.db_set = MagicMock()

        self.timesheet_service.get_todays_timesheet.return_value = "TS-001"
        self.session_service.get_session_times.return_value = (datetime.now(), None)
        self.hr_settings.get_default_activity_type.return_value = "Development"
        self.hr_settings.get_buffer_task.return_value = "BUFFER-001"

        # Create a mock timesheet with a name attribute
        mock_timesheet = MagicMock()
        mock_timesheet.name = "TS-002"
        self.timesheet_service.cancel_and_replace.return_value = mock_timesheet

        # Act
        result = self.service.process_worklog_save(mock_doc)

        # Assert
        self.assertIsNotNone(result)
        self.timesheet_service.cancel_and_replace.assert_called_once()
        mock_doc.db_set.assert_called_once_with("timesheet", "TS-002")

    def test_process_worklog_save_handles_exception(self):
        """Should log error and return None when exception occurs"""
        # Arrange
        mock_doc = MagicMock()
        mock_doc.employee = self.employee_id
        mock_doc.log_time = datetime.now()
        mock_doc.tasks_entry = []
        self.timesheet_service.get_todays_timesheet.side_effect = Exception("Database error")

        # Act
        result = self.service.process_worklog_save(mock_doc)

        # Assert
        self.assertIsNone(result)
