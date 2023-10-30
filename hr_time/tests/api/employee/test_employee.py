import datetime
import unittest

from hr_time.api.employee.repository import Employee, TimeModel


class TestEmployee(unittest.TestCase):
    def test_is_minor_true(self):
        employee = Employee("test", "Test employee", TimeModel.Undefined, "", datetime.date(2000, 1, 15),
                            datetime.date.today())
        today = datetime.date(2018, 1, 10)

        self.assertTrue(employee.is_minor(today))

    def test_is_minor_false_birthday(self):
        employee = Employee("test", "Test employee", TimeModel.Undefined, "", datetime.date(2000, 1, 15),
                            datetime.date.today())
        today = datetime.date(2018, 1, 15)

        self.assertFalse(employee.is_minor(today))

    def test_is_minor_true_leap_year(self):
        employee = Employee("test", "Test employee", TimeModel.Undefined, "", datetime.date(2004, 2, 29),
                            datetime.date.today())
        today = datetime.date(2018, 1, 10)

        self.assertTrue(employee.is_minor(today))

    def test_is_minor_false_birthday_leap_year(self):
        employee = Employee("test", "Test employee", TimeModel.Undefined, "", datetime.date(2004, 2, 29),
                            datetime.date.today())
        today = datetime.date(2022, 2, 28)

        self.assertFalse(employee.is_minor(today))

    def test_is_minor_false_leap_year(self):
        employee = Employee("test", "Test employee", TimeModel.Undefined, "", datetime.date(2004, 2, 29),
                            datetime.date.today())
        today = datetime.date(2022, 3, 5)

        self.assertFalse(employee.is_minor(today))

    def test_is_minor_real_datetime(self):
        employee = Employee("test", "Test employee", TimeModel.Undefined, "", datetime.date(2000, 1, 15),
                            datetime.date.today())
        self.assertFalse(employee.is_minor())
