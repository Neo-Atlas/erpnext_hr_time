import unittest
from datetime import datetime

from hr_time.api.worklog.domain.entities import WorklogEntity, TaskAllocation
from hr_time.api.shared.domain.document_status import DocumentStatus


class TestTaskAllocation(unittest.TestCase):
    """Tests for TaskAllocation value object"""

    def test_create_valid_allocation(self):
        """Should create allocation with valid values"""
        alloc = TaskAllocation(
            task_id="TASK-001",
            subject="Test Task",
            time_spent=2.5,
            expected_time=8.0,
            progress_increment=31.25,
            status="Working",
            priority="High"
        )
        self.assertEqual("TASK-001", alloc.task_id)
        self.assertEqual(2.5, alloc.time_spent)

    def test_negative_time_spent_raises_error(self):
        """Should raise ValueError when time_spent is negative"""
        with self.assertRaises(ValueError):
            TaskAllocation(
                task_id="TASK-001",
                subject="Test",
                time_spent=-1.0,
                expected_time=8.0,
                progress_increment=0,
                status="",
                priority=""
            )

    def test_negative_expected_time_raises_error(self):
        """Should raise ValueError when expected_time is negative"""
        with self.assertRaises(ValueError):
            TaskAllocation(
                task_id="TASK-001",
                subject="Test",
                time_spent=2.0,
                expected_time=-8.0,
                progress_increment=0,
                status="",
                priority=""
            )

    def test_calculate_progress_normal(self):
        """Should calculate progress percentage correctly"""
        alloc = TaskAllocation(
            task_id="TASK-001",
            subject="Test",
            time_spent=2.0,
            expected_time=8.0,
            progress_increment=0,
            status="",
            priority=""
        )
        self.assertEqual(25.0, alloc.calculate_progress())

    def test_calculate_progress_zero_expected(self):
        """Should return 0 when expected_time is 0"""
        alloc = TaskAllocation(
            task_id="TASK-001",
            subject="Test",
            time_spent=2.0,
            expected_time=0,
            progress_increment=0,
            status="",
            priority=""
        )
        self.assertEqual(0, alloc.calculate_progress())

    def test_calculate_progress_exceeds_100(self):
        """Should cap at 100%"""
        alloc = TaskAllocation(
            task_id="TASK-001",
            subject="Test",
            time_spent=10.0,
            expected_time=8.0,
            progress_increment=0,
            status="",
            priority=""
        )
        self.assertEqual(100.0, alloc.calculate_progress())


class TestWorklogEntity(unittest.TestCase):
    """Tests for WorklogEntity domain entity"""

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

    def test_total_allocated_sum(self):
        """Should sum time_spent from all allocations"""
        entity = WorklogEntity(
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
        self.assertEqual(3.5, entity.total_allocated)

    def test_total_allocated_empty(self):
        """Should return 0 when no allocations"""
        entity = WorklogEntity(
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
        self.assertEqual(0, entity.total_allocated)
