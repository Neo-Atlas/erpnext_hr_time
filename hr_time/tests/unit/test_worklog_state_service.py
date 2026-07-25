import unittest

from hr_time.api.worklog.domain.entities import WorklogState
from hr_time.api.worklog.domain.services.worklog_state_service import WorklogStateService


class TestWorklogStateService(unittest.TestCase):

    def setUp(self):
        self.service = WorklogStateService()

    def test_determine_state_new_doc(self):
        """New document should return NEW state"""
        state = self.service.determine_state(
            is_new_doc=True,
            is_todays=False,
            has_open_session=False,
            on_break=False
        )
        self.assertEqual(WorklogState.NEW, state)

    def test_determine_state_historical(self):
        """Non-today worklog should return HISTORICAL"""
        state = self.service.determine_state(
            is_new_doc=False,
            is_todays=False,
            has_open_session=False,
            on_break=False
        )
        self.assertEqual(WorklogState.HISTORICAL, state)

    def test_determine_state_working(self):
        """Today's worklog with open session should return WORKING"""
        state = self.service.determine_state(
            is_new_doc=False,
            is_todays=True,
            has_open_session=True,
            on_break=False
        )
        self.assertEqual(WorklogState.WORKING, state)

    def test_determine_state_on_break(self):
        """Today's worklog on break should return ON_BREAK"""
        state = self.service.determine_state(
            is_new_doc=False,
            is_todays=True,
            has_open_session=False,
            on_break=True
        )
        self.assertEqual(WorklogState.ON_BREAK, state)

    def test_determine_state_completed(self):
        """Today's worklog with no session and not on break should return COMPLETED"""
        state = self.service.determine_state(
            is_new_doc=False,
            is_todays=True,
            has_open_session=False,
            on_break=False
        )
        self.assertEqual(WorklogState.COMPLETED, state)

    # ============ is_editable tests ============

    def test_is_editable_new_doc(self):
        """New document should be editable"""
        result = self.service.is_editable(WorklogState.NEW, is_new_doc=True, is_todays=False)
        self.assertTrue(result)

    def test_is_editable_working_today(self):
        """Working state today should be editable"""
        result = self.service.is_editable(WorklogState.WORKING, is_new_doc=False, is_todays=True)
        self.assertTrue(result)

    def test_is_editable_on_break_today(self):
        """On break state today should be editable"""
        result = self.service.is_editable(WorklogState.ON_BREAK, is_new_doc=False, is_todays=True)
        self.assertTrue(result)

    def test_is_editable_historical(self):
        """Historical worklog should not be editable"""
        result = self.service.is_editable(WorklogState.HISTORICAL, is_new_doc=False, is_todays=False)
        self.assertFalse(result)

    def test_is_editable_completed(self):
        """Completed worklog should not be editable"""
        result = self.service.is_editable(WorklogState.COMPLETED, is_new_doc=False, is_todays=True)
        self.assertFalse(result)
