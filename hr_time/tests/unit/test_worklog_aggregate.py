import unittest
from datetime import datetime

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

    def test_is_within_tolerance_true(self):
        """Should return True when difference is within tolerance"""
        # total_allocated = 3.5, actual = 3.5, tolerance = 0.5
        self.assertTrue(self.aggregate.is_within_tolerance(3.5, 0.5))

    def test_is_within_tolerance_false(self):
        """Should return False when difference exceeds tolerance"""
        # total_allocated = 3.5, actual = 5.5, diff = 2.0 > 0.5
        self.assertFalse(self.aggregate.is_within_tolerance(5.5, 0.5))

    def test_adjust_for_tolerance_overallocated(self):
        """When over-allocated, time_saved should be stretched to match allocation"""
        # total_allocated = 3.5, actual = 2.0
        self.aggregate.adjust_for_tolerance(2.0)
        self.assertEqual(3.5, self.aggregate.worklog.time_saved)

    def test_adjust_for_tolerance_underallocated(self):
        """When under-allocated, time_saved should match actual worked hours"""
        # total_allocated = 3.5, actual = 5.0
        self.aggregate.adjust_for_tolerance(5.0)
        self.assertEqual(5.0, self.aggregate.worklog.time_saved)
