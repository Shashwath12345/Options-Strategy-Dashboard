import unittest
import numpy as np
from finance_functions import black_scholes, calculate_payoff, strategy_metrics


class TestFinanceFunctions(unittest.TestCase):
    def test_put_call_parity(self):
        s, k, days, sigma, rate = 100.0, 105.0, 90, 0.20, 0.05
        call, put = black_scholes(s, k, days, sigma, rate)
        t = days / 365.0
        self.assertAlmostEqual(call - put, s - k * np.exp(-rate * t), places=7)

    def test_bull_call_spread_payoff_at_known_prices(self):
        # Long 100 call for 8, short 120 call for 3 => debit 5.
        prices = np.array([90.0, 105.0, 130.0])
        pnl = calculate_payoff("Bull Call Spread", prices, 100, 8, 120, 3)
        np.testing.assert_allclose(pnl, [-5.0, 0.0, 15.0])

    def test_bull_call_spread_debit_metrics(self):
        m = strategy_metrics("Bull Call Spread", 100, 8, 10, 120, 3)
        self.assertEqual(m["breakeven"], 105)
        self.assertEqual(m["max_profit"], 150)
        self.assertEqual(m["max_loss"], 50)

    def test_bull_call_spread_zero_debit(self):
        m = strategy_metrics("Bull Call Spread", 100, 5, 10, 120, 5)
        self.assertEqual(m["breakeven"], 100)
        self.assertEqual(m["max_profit"], 200)
        self.assertEqual(m["max_loss"], 0)

    def test_bull_call_spread_credit(self):
        m = strategy_metrics("Bull Call Spread", 100, 3, 10, 120, 5)
        self.assertIsNone(m["breakeven"])
        self.assertEqual(m["max_profit"], 220)
        self.assertEqual(m["max_loss"], 0)
        self.assertEqual(m["minimum_profit"], 20)


if __name__ == "__main__":
    unittest.main()
