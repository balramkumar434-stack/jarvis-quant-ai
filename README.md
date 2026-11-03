# jarvis-quant-ai

Standalone, paper-only trading research agent. It evaluates a supplied daily
price history with a 5-day/20-day moving-average rule and prints hypothetical
orders. It does not retrieve market data or connect to a broker.

## Run a decision cycle

Requires Python 3.9 or newer; there are no external dependencies.

Create a JSON input file:

```json
{
  "cash": 10000,
  "holdings": {"ACME": 0},
  "prices": {"ACME": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 20, 20, 20, 20, 20]}
}
```

Provide at least 20 positive daily closing prices per symbol. Held symbols must
have price history so their portfolio value can be calculated. Run:

```sh
python jarvis_agent.py portfolio.json
```

The output includes a decision for each symbol with enough history: buy when
the 5-day average is above the 20-day average, sell an existing position when
it is below, and otherwise hold. New positions are limited to 5% of the
provided portfolio equity and available cash. Quantities may be fractional.
This is a simple research example, not personalized financial advice. Orders
are proposals for paper trading only and are never sent to a broker.

Run tests with:

```sh
python -m unittest
```
