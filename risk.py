from datetime import date
from config import settings
from database import rows

class RiskRejected(Exception): pass

def validate_order(symbol, side, qty, entry, stop, mode="paper"):
    if side not in ("BUY","SELL"): raise RiskRejected("Side must be BUY or SELL.")
    if not symbol or qty <= 0 or entry <= 0: raise RiskRejected("Symbol, positive quantity and entry required.")
    if stop is None or stop <= 0: raise RiskRejected("A valid stop-loss price is mandatory.")
    if side == "BUY" and stop >= entry: raise RiskRejected("For BUY, stop must be below entry.")
    if side == "SELL" and stop <= entry: raise RiskRejected("For SELL, stop must be above entry.")
    risk=abs(entry-stop)*qty
    if risk > settings.risk_per_trade: raise RiskRejected(f"Risk ₹{risk:.2f} exceeds ₹{settings.risk_per_trade:.2f} per trade.")
    if entry*qty > settings.paper_capital*settings.max_leverage:
        raise RiskRejected("Gross exposure exceeds configured 3x capital cap.")
    today=date.today().isoformat()
    trades=rows("SELECT * FROM trades WHERE substr(created_at,1,10)=? AND status!='REJECTED'",(today,))
    if len(trades) >= settings.max_trades_per_day: raise RiskRejected("Daily trade count limit reached.")
    realized=sum(float(t.get("pnl") or 0) for t in trades)
    if realized <= -settings.daily_loss_limit: raise RiskRejected("Daily loss limit reached.")
    return {"risk_amount":risk,"gross_exposure":entry*qty}
