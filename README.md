# JARVIS QUANT AI — Standalone Windows Edition

Independent app. It does not import, edit, or depend on your existing Jarvis installation.

## Requirements
- Windows 10/11
- Python 3.12
- 16 GB RAM CPU-only supported
- Upstox developer app + valid access token for broker data
- Optional Ollama for local model review (for example `qwen3.5:4b`)
- Optional OpenAI-compatible cloud inference endpoint

## Install / run
1. Extract this folder to `%USERPROFILE%\OneDrive\Desktop\JARVIS-QUANT-AI`
2. Open PowerShell in that folder.
3. Run:
   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\Start.ps1
   ```
4. Dashboard: http://127.0.0.1:8765

The first launch creates `.venv`, installs dependencies, and copies `.env.example` to `.env`.

## Configure Upstox
Edit `.env` and add your access token:
`UPSTOX_ACCESS_TOKEN=YOUR_TOKEN`
Never share the token. Upstox access tokens expire according to broker policy; refresh/re-authenticate through the official developer flow.

The scanner uses the Upstox V3 historical/intraday candle endpoint. Provide exact instrument keys from Upstox's official BOD instrument master. This starter release does not yet decode the V3 Protobuf market stream or portfolio websocket.

## Hybrid AI
- Local: Ollama-compatible `/api/generate` endpoint, defaults to `qwen3.5:4b`.
- Cloud: configure `CLOUD_LLM_BASE_URL`, `CLOUD_LLM_API_KEY`, `CLOUD_LLM_MODEL`.
- No provider is assumed to be free. No cloud calls happen unless you click the cloud review button.
- Model output is advisory and cannot override deterministic risk controls.

## Trading modes
- Paper is the default and does not send broker orders.
- Live requires BOTH `LIVE_TRADING_ENABLED=true` in `.env` and exact phrase confirmation in the dashboard, followed by a second per-order confirmation. Live order endpoint submits a LIMIT order only.
- No autonomous live execution, no unattended strategy-to-order bridge.
- After an ambiguous order response, reconcile Upstox order book before retrying.
- Review broker permissions, current SEBI/exchange algo-trading requirements, instrument restrictions, and Upstox app eligibility before live use.

## Default risk limits
- Reference capital ₹15,000
- Risk per trade ₹150
- Daily loss threshold ₹450
- Maximum 2 trades/day
- Gross exposure cap ₹45,000 (3x reference capital)
These are hard-coded starter guardrails, not a recommendation. Actual charges, taxes, slippage, margin and open/pending exposure require further integration. This release's P&L is gross and paper fills are simplistic.

## Stop
Run `.\Stop.ps1`. It targets only this app's Streamlit command on port 8765.

## Tests
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Important limitations of this first runnable release
- No claim of profitability or autonomous execution.
- Scanner uses a simple SMA/momentum/volume heuristic, not a trained NSE model.
- No option-chain analytics, Greeks/PCR/OI dashboard, news feed, broker order reconciliation loop, full-depth stream decoder, corporate-action calendar, or production-grade scheduler yet.
- Do not use live mode until these are implemented, independently tested, and validated in paper trading.
