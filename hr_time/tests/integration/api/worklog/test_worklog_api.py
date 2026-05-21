import json
import unittest
from unittest.mock import patch, MagicMock

from hr_time.api.worklog.api import (
    get_tolerance_minutes,
    get_buffer_task,
    prepare_worklog_for_checkout,
    get_worklog_context,
    save_and_checkout
)


class TestWorklogAPI(unittest.TestCase):
    """Tests for worklog API endpoints"""

    def setUp(self):
        self.employee_id = "HR-EMP-001"
        self.worklog_name = "WL-001"

    # ============ get_tolerance_minutes ============

    @patch('hr_time.api.worklog.api.HRSettingsRepository.get_tolerance_minutes')
    def test_get_tolerance_minutes_returns_value(self, mock_get_tolerance):
        """Should return tolerance minutes from HR settings"""
        mock_get_tolerance.return_value = 30

        result = get_tolerance_minutes()

        self.assertEqual(30, result)
        mock_get_tolerance.assert_called_once()

    # ============ get_buffer_task ============

    @patch('hr_time.api.worklog.api.HRSettingsRepository.get_buffer_task')
    def test_get_buffer_task_returns_task_id(self, mock_get_buffer):
        """Should return buffer task ID from HR settings"""
        mock_get_buffer.return_value = "BUFFER-TASK-001"

        result = get_buffer_task()

        self.assertEqual("BUFFER-TASK-001", result)
        mock_get_buffer.assert_called_once()

    # ============ prepare_worklog_for_checkout ============

    @patch('hr_time.api.worklog.api.get_current_employee_id')
    @patch('hr_time.api.worklog.api.WorklogAppService')
    def test_prepare_worklog_for_checkout_with_employee_id(self, MockAppService, mock_get_emp_id):
        """Should call app service with provided employee_id"""
        mock_app = MagicMock()
        mock_app.prepare_for_checkout.return_value = {"time_saved": 2.5}
        MockAppService.return_value = mock_app

        result = prepare_worklog_for_checkout(employee_id=self.employee_id)

        self.assertEqual({"time_saved": 2.5}, result)
        mock_app.prepare_for_checkout.assert_called_once_with(self.employee_id)
        mock_get_emp_id.assert_not_called()

    @patch('hr_time.api.worklog.api.get_current_employee_id')
    @patch('hr_time.api.worklog.api.WorklogAppService')
    def test_prepare_worklog_for_checkout_without_employee_id(self, MockAppService, mock_get_emp_id):
        """Should fetch employee_id when not provided"""
        mock_get_emp_id.return_value = self.employee_id
        mock_app = MagicMock()
        mock_app.prepare_for_checkout.return_value = {"time_saved": 2.5}
        MockAppService.return_value = mock_app

        result = prepare_worklog_for_checkout()

        self.assertEqual({"time_saved": 2.5}, result)
        mock_get_emp_id.assert_called_once()
        mock_app.prepare_for_checkout.assert_called_once_with(self.employee_id)

    # ============ get_worklog_context ============

    @patch('hr_time.api.worklog.api.get_current_employee_id')
    @patch('hr_time.api.worklog.api.WorklogAppService')
    def test_get_worklog_context_returns_formatted_response(self, MockAppService, mock_get_emp_id):
        """Should return formatted context dictionary"""
        mock_get_emp_id.return_value = self.employee_id

        # Mock the app service response
        mock_context = {
            "state": MagicMock(),
            "is_todays": True,
            "is_new_doc": False,
            "is_editable": True,
            "has_open_session": True,
            "on_break": False,
            "today_worklog_name": "WL-001",
            "worklog_total_hours": 3.5,
            "tolerance_minutes": 30,
        }
        mock_context["state"].value = "working"
        mock_context["state"].display_color.return_value = "green"
        mock_app = MagicMock()
        mock_app.get_worklog_context.return_value = mock_context
        MockAppService.return_value = mock_app

        result = get_worklog_context(
            referred_worklog_name=self.worklog_name,
            employee_id=self.employee_id,
            is_dialog_call=False
        )

        # Assert structure
        self.assertEqual("working", result["worklog_state"])
        self.assertEqual("green", result["headline_color"])
        self.assertTrue(result["is_todays_worklog"])
        self.assertFalse(result["is_new_doc"])
        self.assertFalse(result["is_read_only"])
        self.assertTrue(result["has_open_session"])
        self.assertFalse(result["on_break"])
        self.assertEqual("WL-001", result["today_worklog_name"])
        self.assertEqual(3.5, result["worklog_total_hours"])
        self.assertEqual(30, result["tolerance_minutes"])
        self.assertIn("worklog_overview_headline", result)
        self.assertIn("worklog_status_today_html", result)

    # ============ save_and_checkout ============

    @patch('hr_time.api.worklog.api.WorklogAppService')
    def test_save_and_checkout_success(self, MockAppService):
        """Should return success response when save succeeds"""
        mock_app = MagicMock()
        mock_app.save_and_checkout.return_value = ("WL-002", True)
        MockAppService.return_value = mock_app

        worklog_data = {
            "work_desc": "Test work",
            "is_home_office": "No",
            "tasks_entry": []
        }

        result = save_and_checkout(
            worklog_name=None,
            employee_id=self.employee_id,
            worklog_data=worklog_data,
            current_total=3.5
        )

        result_dict = json.loads(result) if isinstance(result, str) else result

        self.assertEqual("success", result_dict["status"])
        self.assertIn("Worklog saved successfully and checked out", result_dict["message"])
        self.assertEqual("WL-002", result_dict["data"]["worklog"])

    @patch('hr_time.api.worklog.api.WorklogAppService')
    def test_save_and_checkout_without_checkout(self, MockAppService):
        """Should return success response without checkout message when no open session"""
        mock_app = MagicMock()
        mock_app.save_and_checkout.return_value = ("WL-002", False)
        MockAppService.return_value = mock_app

        worklog_data = {"work_desc": "Test work"}

        result = save_and_checkout(
            worklog_name=None,
            employee_id=self.employee_id,
            worklog_data=worklog_data,
            current_total=3.5
        )

        result_dict = json.loads(result) if isinstance(result, str) else result

        self.assertEqual("success", result_dict["status"])
        self.assertIn("Worklog saved successfully", result_dict["message"])
        self.assertNotIn("checked out", result_dict["message"])

    @patch('hr_time.api.worklog.api.WorklogAppService')
    def test_save_and_checkout_invalid_json(self, MockAppService):
        """Should return error response when worklog_data is invalid JSON string"""
        result = save_and_checkout(
            worklog_name=None,
            employee_id=self.employee_id,
            worklog_data="invalid json {{",
            current_total=3.5
        )

        result_dict = json.loads(result) if isinstance(result, str) else result

        self.assertEqual("error", result_dict["status"])
        self.assertIn("Invalid JSON", result_dict["message"])
        MockAppService.assert_not_called()

    @patch('hr_time.api.worklog.api.WorklogAppService')
    def test_save_and_checkout_exception(self, MockAppService):
        """Should return error response when exception occurs"""
        mock_app = MagicMock()
        mock_app.save_and_checkout.side_effect = Exception("Database error")
        MockAppService.return_value = mock_app

        worklog_data = {"work_desc": "Test work"}

        result = save_and_checkout(
            worklog_name=None,
            employee_id=self.employee_id,
            worklog_data=worklog_data,
            current_total=3.5
        )

        result_dict = json.loads(result) if isinstance(result, str) else result

        self.assertEqual("error", result_dict["status"])
        self.assertEqual("Database error", result_dict["message"])
