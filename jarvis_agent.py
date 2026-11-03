"""A small, paper-only daily trading decision agent."""

import argparse
import json
import math
import sys

SHORT_WINDOW = 5
LONG_WINDOW = 20
MAX_POSITION_FRACTION = 0.05


def _validate_portfolio(data):
    if not isinstance(data, dict):
        raise ValueError("Input must be a JSON object")
    cash = data.get("cash")
    holdings = data.get("holdings")
    prices = data.get("prices")
    if not isinstance(cash, (int, float)) or isinstance(cash, bool) or not math.isfinite(cash) or cash < 0:
        raise ValueError("'cash' must be a finite, non-negative number")
    if not isinstance(holdings, dict) or not isinstance(prices, dict):
        raise ValueError("'holdings' and 'prices' must be JSON objects")

    clean_holdings = {}
    for symbol, quantity in holdings.items():
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("Holding symbols must be non-empty strings")
        if not isinstance(quantity, (int, float)) or isinstance(quantity, bool) or not math.isfinite(quantity) or quantity < 0:
            raise ValueError(f"Holding for {symbol} must be a finite, non-negative number")
        clean_holdings[symbol.upper()] = quantity

    clean_prices = {}
    for symbol, history in prices.items():
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("Price symbols must be non-empty strings")
        if not isinstance(history, list) or not history:
            raise ValueError(f"Prices for {symbol} must be a non-empty array")
        if any(not isinstance(price, (int, float)) or isinstance(price, bool) or not math.isfinite(price) or price <= 0 for price in history):
            raise ValueError(f"Prices for {symbol} must be finite, positive numbers")
        clean_prices[symbol.upper()] = history

    missing_prices = clean_holdings.keys() - clean_prices.keys()
    if missing_prices:
        raise ValueError(f"Missing price history for held symbols: {', '.join(sorted(missing_prices))}")
    return cash, clean_holdings, clean_prices


def decide(data):
    """Return one paper-only decision per symbol with enough price history."""
    cash, holdings, prices = _validate_portfolio(data)
    equity = cash + sum(holdings.get(symbol, 0) * history[-1] for symbol, history in prices.items())
    decisions = []
    available_cash = cash

    for symbol in sorted(prices):
        history = prices[symbol]
        if len(history) < LONG_WINDOW:
            continue
        short_average = sum(history[-SHORT_WINDOW:]) / SHORT_WINDOW
        long_average = sum(history[-LONG_WINDOW:]) / LONG_WINDOW
        quantity = holdings.get(symbol, 0)
        current_price = history[-1]

        if short_average > long_average:
            budget = max(0, min(equity * MAX_POSITION_FRACTION - quantity * current_price, available_cash))
            order_quantity = math.floor((budget / current_price) * 1_000_000) / 1_000_000
            action = "buy" if order_quantity > 0 else "hold"
            available_cash -= order_quantity * current_price
        elif short_average < long_average and quantity > 0:
            action = "sell"
            order_quantity = quantity
        else:
            action = "hold"
            order_quantity = 0

        decisions.append({
            "symbol": symbol,
            "action": action,
            "quantity": round(order_quantity, 6),
            "price": current_price,
            "short_average": round(short_average, 6),
            "long_average": round(long_average, 6),
            "reason": (
                "short average above long average"
                if short_average > long_average
                else "short average below long average"
                if short_average < long_average
                else "short and long averages are equal"
            ),
        })

    return {"mode": "paper", "decisions": decisions}


def main():
    parser = argparse.ArgumentParser(description="Generate paper-trading decisions from supplied price history.")
    parser.add_argument("input", help="JSON file containing cash, holdings, and price history")
    args = parser.parse_args()
    try:
        with open(args.input, encoding="utf-8") as input_file:
            result = decide(json.load(input_file))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"jarvis-agent: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
