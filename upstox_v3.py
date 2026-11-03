import requests
from urllib.parse import quote
from config import settings

API = "https://api.upstox.com"
HFT = "https://api-hft.upstox.com"

class UpstoxClient:
    def __init__(self, token=None):
        self.token = token or settings.upstox_access_token
    def headers(self):
        if not self.token:
            raise RuntimeError("Upstox access token missing. Add UPSTOX_ACCESS_TOKEN to .env.")
        return {"Authorization": f"Bearer {self.token}", "Accept":"application/json", "Content-Type":"application/json"}
    def get(self, path, params=None):
        r=requests.get(API+path,headers=self.headers(),params=params,timeout=20)
        r.raise_for_status(); return r.json()
    def candles(self, instrument_key, unit="minutes", interval=5, to_date=None, from_date=None):
        from datetime import date, timedelta
        to_date = to_date or date.today().isoformat()
        if from_date:
            path=f"/v3/historical-candle/{quote(instrument_key,safe='')}/{unit}/{interval}/{to_date}/{from_date}"
        else:
            path=f"/v3/historical-candle/intraday/{quote(instrument_key,safe='')}/{unit}/{interval}"
        return self.get(path)
    def profile(self):
        return self.get("/v2/user/profile")
    def funds(self):
        return self.get("/v2/user/get-funds-and-margin")
    def place_order_v3(self, instrument_key, quantity, side, order_type="LIMIT", price=0, product="I", tag="jqai"):
        if side not in ("BUY","SELL"): raise ValueError("side must be BUY or SELL")
        body={"quantity":int(quantity),"product":product,"validity":"DAY","price":float(price),
              "tag":tag[:20],"instrument_token":instrument_key,"order_type":order_type,
              "transaction_type":side,"disclosed_quantity":0,"trigger_price":0,"is_amo":False,
              "slice":False}
        r=requests.post(HFT+"/v3/order/place",headers=self.headers(),json=body,timeout=20)
        r.raise_for_status(); return r.json()
    def order_book(self):
        return self.get("/v2/order/retrieve-all")
