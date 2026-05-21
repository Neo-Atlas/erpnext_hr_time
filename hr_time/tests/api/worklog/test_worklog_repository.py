import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date

from hr_time.api.worklog.repository import WorklogRepository
from hr_time.api.worklog.domain.entities import WorklogEntity


class TestWorklogRepository(unittest.TestCase):
    """Tests for WorklogRepository"""

    def setUp(self):
        self.repo = WorklogRepository()
        self.employee_id = "EMP001"
        self.worklog_name = "WL-001"
        self.current_total = 3.5

    # ============ get_worklogs ============

    @patch('hr_time.api.worklog.repository.frappe.get_all')
    def test_get_worklogs_returns_list(self, mock_get_all):
        """Should return list of worklogs matching filters"""
        mock_data = [
            {"name": "WL-001", "employee": self.employee_id, "time_saved": 2.5},
            {"name": "WL-002", "employee": self.employee_id, "time_saved": 1.5}
        ]
        mock_get_all.return_value = mock_data

        result = self.repo.get_worklogs({"employee": self.employee_id})

        self.assertEqual(mock_data, result)
        mock_get_all.assert_called_once()

    # ============ get_worklogs_of_employee_on_date ============

    @patch('hr_time.api.worklog.repository.WorklogRepository.get_worklogs')
    @patch('hr_time.api.worklog.repository.frappe.get_doc')
    def test_get_worklogs_of_employee_on_date_returns_entities(self, mock_get_doc, mock_get_worklogs):
        """Should return WorklogEntity list for employee on date"""
        # Mock the document list
        mock_docs = [{"name": "WL-001"}, {"name": "WL-002"}]
        mock_get_worklogs.return_value = mock_docs

        # Mock the doc objects
        mock_doc = MagicMock()
        mock_doc.name = "WL-001"
        mock_doc.employee = self.employee_id
        mock_doc.log_time = datetime.now()
        mock_doc.work_desc = "Test work"
        mock_doc.time_saved = 2.5
        mock_doc.is_home_office = "Yes"
        mock_doc.ticket_link = ""
        mock_doc.docstatus = 0
        mock_doc.timesheet = None
        mock_doc.tasks_entry = []
        mock_get_doc.return_value = mock_doc

        interested_date = date(2024, 10, 10)

        result = self.repo.get_worklogs_of_employee_on_date(self.employee_id, interested_date)

        self.assertEqual(2, len(result))
        self.assertIsInstance(result[0], WorklogEntity)
        mock_get_worklogs.assert_called_once()

    # ============ get_todays_worklog_entity ============

    @patch('hr_time.api.worklog.repository.WorklogRepository.get_todays_worklog_dict')
    @patch('hr_time.api.worklog.repository.frappe.get_doc')
    def test_get_todays_worklog_entity_when_exists(self, mock_get_doc, mock_get_dict):
        """Should return WorklogEntity when today's worklog exists"""
        mock_get_dict.return_value = {"name": "WL-001"}

        mock_doc = MagicMock()
        mock_doc.name = "WL-001"
        mock_doc.employee = self.employee_id
        mock_doc.log_time = datetime.now()
        mock_doc.work_desc = "Test work"
        mock_doc.time_saved = 2.5
        mock_doc.is_home_office = "No"
        mock_doc.ticket_link = ""
        mock_doc.docstatus = 0
        mock_doc.timesheet = None
        mock_doc.tasks_entry = []
        mock_get_doc.return_value = mock_doc

        result = self.repo.get_todays_worklog_entity(self.employee_id)

        self.assertIsInstance(result, WorklogEntity)
        self.assertEqual("WL-001", result.id)

    @patch('hr_time.api.worklog.repository.WorklogRepository.get_todays_worklog_dict')
    def test_get_todays_worklog_entity_when_not_exists(self, mock_get_dict):
        """Should return None when no worklog exists for today"""
        mock_get_dict.return_value = None

        result = self.repo.get_todays_worklog_entity(self.employee_id)

        self.assertIsNone(result)

    # ============ get_by_id ============

    @patch('hr_time.api.worklog.repository.frappe.db.exists')
    @patch('hr_time.api.worklog.repository.frappe.get_doc')
    def test_get_by_id_when_exists(self, mock_get_doc, mock_exists):
        """Should return WorklogEntity when worklog exists"""
        mock_exists.return_value = True

        mock_doc = MagicMock()
        mock_doc.name = "WL-001"
        mock_doc.employee = self.employee_id
        mock_doc.log_time = datetime.now()
        mock_doc.work_desc = "Test work"
        mock_doc.time_saved = 2.5
        mock_doc.is_home_office = "No"
        mock_doc.ticket_link = ""
        mock_doc.docstatus = 0
        mock_doc.timesheet = None
        mock_doc.tasks_entry = []
        mock_get_doc.return_value = mock_doc

        result = self.repo.get_by_id("WL-001")

        self.assertIsInstance(result, WorklogEntity)
        self.assertEqual("WL-001", result.id)

    @patch('hr_time.api.worklog.repository.frappe.db.exists')
    def test_get_by_id_when_not_exists(self, mock_exists):
        """Should return None when worklog does not exist"""
        mock_exists.return_value = False

        result = self.repo.get_by_id("WL-999")

        self.assertIsNone(result)

    # ============ save_from_dict ============

    @patch('hr_time.api.worklog.repository.frappe.get_doc')
    def test_save_from_dict_updates_existing_worklog(self, mock_get_doc):
        """Should update existing worklog"""
        mock_doc = MagicMock()
        mock_doc.name = "WL-001"
        mock_get_doc.return_value = mock_doc

        worklog_data = {
            "time_saved": 3.0,
            "work_desc": "Updated description",
            "is_home_office": "Yes",
            "ticket_link": "https://example.com",
            "tasks_entry": []
        }

        result = self.repo.save_from_dict(
            worklog_name="WL-001",
            worklog_data=worklog_data,
            current_total=self.current_total,
            employee_id=self.employee_id
        )

        self.assertEqual("WL-001", result)
        mock_doc.save.assert_called_once()

    @patch('hr_time.api.worklog.repository.frappe.new_doc')
    def test_save_from_dict_creates_new_worklog(self, mock_new_doc):
        """Should create new worklog when name not provided"""
        mock_doc = MagicMock()
        mock_doc.name = "new-WL-001"
        mock_new_doc.return_value = mock_doc

        worklog_data = {
            "time_saved": 2.5,
            "work_desc": "New worklog",
            "is_home_office": "No",
            "ticket_link": "",
            "tasks_entry": []
        }

        result = self.repo.save_from_dict(
            worklog_name=None,
            worklog_data=worklog_data,
            current_total=self.current_total,
            employee_id=self.employee_id
        )

        self.assertEqual("new-WL-001", result)
        mock_doc.insert.assert_called_once()

    @patch('hr_time.api.worklog.repository.frappe.get_doc')
    def test_save_from_dict_handles_tasks_entry(self, mock_get_doc):
        """Should correctly process tasks_entry child table"""
        mock_doc = MagicMock()
        mock_doc.name = "WL-001"
        mock_doc.set = MagicMock()
        mock_doc.append = MagicMock()
        mock_get_doc.return_value = mock_doc

        worklog_data = {
            "time_saved": 2.5,
            "work_desc": "Test",
            "is_home_office": "No",
            "tasks_entry": [
                {
                    "task": "TASK-001",
                    "subject": "Task 1",
                    "status": "Open",
                    "expected_time": 8.0,
                    "priority": "High",
                    "time_spent": 2.0,
                    "task_desc": "Description",
                    "progress_increment": 25.0
                }
            ]
        }

        result = self.repo.save_from_dict(
            worklog_name="WL-001",
            worklog_data=worklog_data,
            current_total=self.current_total,
            employee_id=self.employee_id
        )

        self.assertEqual("WL-001", result)
        mock_doc.set.assert_called_once_with('tasks_entry', [])
        mock_doc.append.assert_called_once()
