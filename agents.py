import requests
from config import settings
from database import conn, now, event

def technical_agent(candles):
    # candles expected Upstox [timestamp, open, high, low, close, volume, oi]
    if not candles or len(candles)<25: return {"side":"WAIT","confidence":0.0,"rationale":"Need at least 25 candles."}
    closes=[float(x[4]) for x in candles]
    vols=[float(x[5] or 0) for x in candles]
    fast=sum(closes[-9:])/9
    slow=sum(closes[-21:])/21
    momentum=(closes[-1]-closes[-6])/closes[-6]*100 if closes[-6] else 0
    vol_ratio=(vols[-1]/(sum(vols[-10:-1])/9)) if sum(vols[-10:-1]) else 1
    if fast>slow and momentum>0.15 and vol_ratio>1.1:
        side="BUY"; confidence=min(.85,.55+abs(momentum)/3+(vol_ratio-1)*.08)
    elif fast<slow and momentum<-.15 and vol_ratio>1.1:
        side="SELL"; confidence=min(.85,.55+abs(momentum)/3+(vol_ratio-1)*.08)
    else: side="WAIT"; confidence=.35
    return {"side":side,"confidence":round(confidence,2),"fast_sma":round(fast,2),"slow_sma":round(slow,2),
            "momentum_pct":round(momentum,3),"volume_ratio":round(vol_ratio,2),
            "rationale":"SMA(9)/SMA(21), 5-candle momentum and relative-volume heuristic; not a validated edge."}

def local_llm_review(prompt):
    try:
        r=requests.post(settings.ollama_base_url.rstrip("/")+"/api/generate",
            json={"model":settings.ollama_model,"prompt":prompt,"stream":False},timeout=45)
        r.raise_for_status()
        return {"provider":"ollama","text":r.json().get("response","")}
    except Exception as e:
        return {"provider":"unavailable","text":f"Local model unavailable: {e}"}

def cloud_review(prompt):
    if not (settings.cloud_base_url and settings.cloud_api_key and settings.cloud_model):
        return {"provider":"not_configured","text":"Cloud inference not configured; set endpoint, key and model in .env."}
    try:
        url=settings.cloud_base_url.rstrip("/")+"/chat/completions"
        r=requests.post(url,headers={"Authorization":f"Bearer {settings.cloud_api_key}"},
            json={"model":settings.cloud_model,"messages":[{"role":"user","content":prompt}],"temperature":.1},timeout=45)
        r.raise_for_status()
        return {"provider":"cloud","text":r.json()["choices"][0]["message"]["content"]}
    except Exception as e: return {"provider":"error","text":str(e)}

def save_signal(symbol, signal):
    with conn() as c:
        c.execute("INSERT INTO signals(created_at,symbol,side,confidence,rationale,payload) VALUES(?,?,?,?,?,?)",
            (now(),symbol,signal["side"],signal["confidence"],signal["rationale"],str(signal)))
    event(f"Signal {symbol}: {signal['side']} ({signal['confidence']})")
