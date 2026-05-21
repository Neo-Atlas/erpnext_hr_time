import unittest
from datetime import datetime
from unittest.mock import MagicMock

from hr_time.api.worklog.domain.aggregates import WorklogAggregate
from hr_time.api.worklog.domain.entities import WorklogEntity, TaskAllocation
from hr_time.api.shared.domain.document_status import DocumentStatus


class TestWorklogAggregate(unittest.TestCase):
    """Tests for WorklogAggregate"""

    def setUp(self):
        self.alloc1 = TaskAllocation(
            task_id="TASK-001",
            subject="Task 1",
            time_spent=2.0,
            expected_time=8.0,
            progress_increment=25.0,
            status="Working",
            priority="High"
        )
        self.alloc2 = TaskAllocation(
            task_id="TASK-002",
            subject="Task 2",
            time_spent=1.5,
            expected_time=4.0,
            progress_increment=37.5,
            status="Working",
            priority="Medium"
        )
        self.entity = WorklogEntity(
            id=None,
            employee_id="EMP-001",
            log_time=datetime.now(),
            work_desc="Test",
            time_saved=3.5,
            is_home_office=False,
            ticket_link=None,
            docstatus=DocumentStatus.DRAFT,
            timesheet_id=None,
            allocations=[self.alloc1, self.alloc2]
        )
        self.aggregate = WorklogAggregate(self.entity)

    def test_total_allocated_property(self):
        """Should return total allocated time from entity"""
        self.assertEqual(3.5, self.aggregate.total_allocated)

    def test_has_allocations_true(self):
        """Should return True when allocations exist"""
        self.assertTrue(self.aggregate.has_allocations)

    def test_has_allocations_false(self):
        """Should return False when no allocations"""
        empty_entity = WorklogEntity(
            id=None,
            employee_id="EMP-001",
            log_time=datetime.now(),
            work_desc="Test",
            time_saved=0,
            is_home_office=False,
            ticket_link=None,
            docstatus=DocumentStatus.DRAFT,
            timesheet_id=None,
            allocations=[]
        )
        aggregate = WorklogAggregate(empty_entity)
        self.assertFalse(aggregate.has_allocations)

    def test_is_within_tolerance_delegates(self):
        """Should delegate to entity.is_within_tolerance"""
        # Mock the entity to verify delegation
        mock_entity = MagicMock(spec=WorklogEntity)
        aggregate = WorklogAggregate(mock_entity)

        aggregate.is_within_tolerance(4.0, 0.5)

        mock_entity.is_within_tolerance.assert_called_once_with(4.0, 0.5)

    def test_adjust_for_tolerance_delegates(self):
        """Should delegate to entity.adjusted_time_saved"""
        mock_entity = MagicMock(spec=WorklogEntity)
        aggregate = WorklogAggregate(mock_entity)

        aggregate.adjust_for_tolerance(4.0)

        # Verify time_saved was set
        mock_entity.adjusted_time_saved.assert_called_once_with(4.0)
