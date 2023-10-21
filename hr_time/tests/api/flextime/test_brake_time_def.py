import unittest

from hr_time.api.flextime.brake_time import BrakeTimeDefinitions, BrakeTime


class TestBrakeTimeDefinition(unittest.TestCase):
    def test_get_brake_time_fully_defined(self):
        definition = BrakeTimeDefinitions()
        definition.insert(BrakeTime(2000, 100), False)
        definition.insert(BrakeTime(3000, 200), False)
        definition.insert(BrakeTime(1000, 50), True)
        definition.insert(BrakeTime(2000, 75), True)
        definition.insert(BrakeTime(4000, 80), True)

        # Correct regular times
        self.assertEqual(definition.get_brake_time(500, False), 0)
        self.assertEqual(definition.get_brake_time(1500, False), 0)
        self.assertEqual(definition.get_brake_time(2000, False), 100)
        self.assertEqual(definition.get_brake_time(2500, False), 100)
        self.assertEqual(definition.get_brake_time(3000, False), 200)
        self.assertEqual(definition.get_brake_time(3100, False), 200)

        # Correct minor times
        self.assertEqual(definition.get_brake_time(500, True), 0)
        self.assertEqual(definition.get_brake_time(1000, True), 50)
        self.assertEqual(definition.get_brake_time(1100, True), 50)
        self.assertEqual(definition.get_brake_time(2000, True), 75)
        self.assertEqual(definition.get_brake_time(2500, True), 75)
        self.assertEqual(definition.get_brake_time(4000, True), 80)
        self.assertEqual(definition.get_brake_time(4500, True), 80)

    def test_get_brake_time_only_regular_defined(self):
        definition = BrakeTimeDefinitions()
        definition.insert(BrakeTime(2000, 100), False)
        definition.insert(BrakeTime(3000, 200), False)

        # Regular times used, if no minor time definition exists
        self.assertEqual(definition.get_brake_time(500, True), 0)
        self.assertEqual(definition.get_brake_time(1500, True), 0)
        self.assertEqual(definition.get_brake_time(2000, True), 100)
        self.assertEqual(definition.get_brake_time(2500, True), 100)
        self.assertEqual(definition.get_brake_time(3000, True), 200)
        self.assertEqual(definition.get_brake_time(3500, True), 200)