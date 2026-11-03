from database import conn, now, event
from upstox_v3 import UpstoxClient

class PaperBroker:
    def submit(self, symbol, instrument_key, side, qty, entry, stop, target=None, notes=""):
        with conn() as c:
            cur=c.execute('''INSERT INTO trades(created_at,symbol,instrument_key,side,qty,entry,stop,target,status,mode,notes)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)''',(now(),symbol,instrument_key,side,qty,entry,stop,target,"OPEN","PAPER",notes))
            trade_id=cur.lastrowid
        event(f"Paper trade opened #{trade_id}: {side} {qty} {symbol} @ {entry}")
        return {"trade_id":trade_id,"mode":"PAPER","status":"OPEN"}
    def close(self, trade_id, exit_price):
        with conn() as c:
            t=c.execute("SELECT * FROM trades WHERE id=? AND status='OPEN' AND mode='PAPER'",(trade_id,)).fetchone()
            if not t: raise ValueError("Open paper trade not found.")
            pnl=(exit_price-t["entry"])*t["qty"]*(1 if t["side"]=="BUY" else -1)
            c.execute("UPDATE trades SET status='CLOSED',pnl=?,notes=COALESCE(notes,'') || ? WHERE id=?",(pnl,f" | exit={exit_price}",trade_id))
        event(f"Paper trade #{trade_id} closed; gross P&L ₹{pnl:.2f}")
        return pnl

class LiveBroker:
    def submit(self, instrument_key, side, qty, price, order_type="LIMIT"):
        return UpstoxClient().place_order_v3(instrument_key,qty,side,order_type,price)
