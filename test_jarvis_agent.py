import unittest

from jarvis_agent import decide


def portfolio(prices, cash=10_000, holdings=None):
    return {"cash": cash, "holdings": holdings or {}, "prices": {"ACME": prices}}


class DecideTests(unittest.TestCase):
    def test_bullish_signal_buys_only_up_to_position_limit(self):
        data = portfolio([10] * 15 + [20] * 5, cash=10_000)

        result = decide(data)

        self.assertEqual(result["mode"], "paper")
        self.assertEqual(result["decisions"][0]["action"], "buy")
        self.assertEqual(result["decisions"][0]["quantity"], 25)

    def test_bearish_signal_sells_existing_position(self):
        data = portfolio([20] * 15 + [10] * 5, holdings={"ACME": 12})

        result = decide(data)

        self.assertEqual(result["decisions"][0]["action"], "sell")
        self.assertEqual(result["decisions"][0]["quantity"], 12)

    def test_insufficient_history_produces_no_decision(self):
        self.assertEqual(decide(portfolio([10] * 19))["decisions"], [])

    def test_multiple_buys_do_not_exceed_available_cash(self):
        data = {
            "cash": 15,
            "holdings": {"RESERVE": 185},
            "prices": {
                "ACME": [10] * 15 + [20] * 5,
                "BETA": [20] * 15 + [40] * 5,
                "RESERVE": [1],
            },
        }

        result = decide(data)

        spent = sum(
            decision["quantity"] * decision["price"]
            for decision in result["decisions"]
            if decision["action"] == "buy"
        )
        self.assertLessEqual(spent, data["cash"])

    def test_missing_held_asset_price_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing price history"):
            decide({"cash": 10, "holdings": {"ACME": 1}, "prices": {}})

    def test_invalid_price_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "finite, positive"):
            decide(portfolio([10] * 19 + [0]))


if __name__ == "__main__":
    unittest.main()
