import unittest

from hr_time.api.worklog.domain.task_progress_calculator import TaskProgressCalculator


class TestTaskProgressCalculator(unittest.TestCase):
    """Pure unit tests for TaskProgressCalculator - no Frappe dependencies"""

    def setUp(self):
        self.calc = TaskProgressCalculator()

    def test_calculate_progress_increment_normal(self):
        """Should calculate correct percentage"""
        result = self.calc.calculate_progress_increment(2.0, 8.0)
        self.assertEqual(25.0, result)

    def test_calculate_progress_increment_zero_expected(self):
        """Should return 0 when expected_time is 0"""
        result = self.calc.calculate_progress_increment(5.0, 0)
        self.assertEqual(0.0, result)

    def test_calculate_progress_increment_negative_time(self):
        """Should handle negative time_spent gracefully"""
        result = self.calc.calculate_progress_increment(-2.0, 8.0)
        self.assertEqual(0.0, result)

    def test_calculate_progress_increment_exceeds_100(self):
        """Should cap at 100%"""
        result = self.calc.calculate_progress_increment(10.0, 8.0)
        self.assertEqual(100.0, result)

    def test_calculate_total_progress_normal(self):
        """Should calculate total progress from cumulative hours"""
        result = self.calc.calculate_total_progress(4.0, 8.0)
        self.assertEqual(50.0, result)

    def test_calculate_total_progress_zero_expected(self):
        """Should return 0 when expected_time is 0"""
        result = self.calc.calculate_total_progress(5.0, 0)
        self.assertEqual(0.0, result)

    def test_should_update_progress_true(self):
        """Should return True when difference exceeds epsilon"""
        result = self.calc.should_update_progress(25.0, 30.0)
        self.assertTrue(result)

    def test_should_update_progress_false(self):
        """Should return False when difference is within epsilon"""
        result = self.calc.should_update_progress(25.0, 25.005)
        self.assertFalse(result)

    def test_calculate_row_progress_increment_normal(self):
        """Should calculate increment for a single row"""
        result = self.calc.calculate_row_progress_increment(2.0, 8.0)
        self.assertEqual(25.0, result)

    def test_calculate_row_progress_increment_zero_spent(self):
        """Should return 0 when time_spent is 0"""
        result = self.calc.calculate_row_progress_increment(0, 8.0)
        self.assertEqual(0.0, result)
