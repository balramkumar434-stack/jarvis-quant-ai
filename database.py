import sqlite3, json, os
from datetime import datetime, timezone
from config import settings

def conn():
    os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
    c = sqlite3.connect(settings.db_path, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS trades(
          id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
          symbol TEXT NOT NULL, instrument_key TEXT, side TEXT NOT NULL,
          qty INTEGER NOT NULL, entry REAL NOT NULL, stop REAL, target REAL,
          status TEXT NOT NULL, mode TEXT NOT NULL, pnl REAL DEFAULT 0,
          broker_order_id TEXT, notes TEXT);
        CREATE TABLE IF NOT EXISTS signals(
          id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
          symbol TEXT, side TEXT, confidence REAL, rationale TEXT, payload TEXT);
        CREATE TABLE IF NOT EXISTS events(
          id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
          level TEXT, message TEXT);
        CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT);
        ''')
def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
def event(message, level="INFO"):
    with conn() as c:
        c.execute("INSERT INTO events(created_at,level,message) VALUES(?,?,?)",(now(),level,message))
def get_kv(key, default=""):
    with conn() as c:
        r=c.execute("SELECT value FROM kv WHERE key=?",(key,)).fetchone()
    return r["value"] if r else default
def set_kv(key,value):
    with conn() as c:
        c.execute("INSERT INTO kv(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(key,str(value)))
def rows(query, params=()):
    with conn() as c:
        return [dict(x) for x in c.execute(query,params).fetchall()]
