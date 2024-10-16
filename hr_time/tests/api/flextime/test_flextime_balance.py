import unittest

from hr_time.api.flextime.stats import FlextimeBalance


class TestFlextimeBalance(unittest.TestCase):
    def test_init_positive_balance_positive_trend(self):
        balance = FlextimeBalance(1.3, 0.56)

        self.assertEqual(1, balance.balance_hours)
        self.assertEqual(18, balance.balance_minutes)
        self.assertEqual(0, balance.trend_hours)
        self.assertEqual(34, balance.trend_minutes)
        self.assertEqual(0.43, round(balance.trend_percent, ndigits=2))

    def test_init_positive_balance_negative_trend(self):
        balance = FlextimeBalance(2.4, -0.25)

        self.assertEqual(2, balance.balance_hours)
        self.assertEqual(24, balance.balance_minutes)
        self.assertEqual(0, balance.trend_hours)
        self.assertEqual(-15, balance.trend_minutes)
        self.assertEqual(-0.10, round(balance.trend_percent, ndigits=2))

    def test_init_negative_balance_negative_trend(self):
        balance = FlextimeBalance(-3.0, -1.3)

        self.assertEqual(-3, balance.balance_hours)
        self.assertEqual(0, balance.balance_minutes)
        self.assertEqual(-1, balance.trend_hours)
        self.assertEqual(-18, balance.trend_minutes)
        self.assertEqual(-0.43, round(balance.trend_percent, ndigits=2))

    def test_init_negative_balance_positive_trend(self):
        balance = FlextimeBalance(-3.1, 0.5)

        self.assertEqual(-3, balance.balance_hours)
        self.assertEqual(-6, balance.balance_minutes)
        self.assertEqual(0, balance.trend_hours)
        self.assertEqual(30, balance.trend_minutes)
        self.assertEqual(0.16, round(balance.trend_percent, ndigits=2))

    def test_init_all_zero(self):
        balance = FlextimeBalance(0, 0)

        self.assertEqual(0, balance.balance_hours)
        self.assertEqual(0, balance.balance_minutes)
        self.assertEqual(0, balance.trend_hours)
        self.assertEqual(0, balance.trend_minutes)
        self.assertEqual(0, round(balance.trend_percent, ndigits=2))

    def test_init_zero_growth(self):
        balance = FlextimeBalance(1.2, 0)

        self.assertEqual(1, balance.balance_hours)
        self.assertEqual(12, balance.balance_minutes)
        self.assertEqual(0, balance.trend_hours)
        self.assertEqual(0, balance.trend_minutes)
        self.assertEqual(0, round(balance.trend_percent, ndigits=2))
