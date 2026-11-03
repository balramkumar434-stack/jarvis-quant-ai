import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def setting(name, default=""):
    value = os.getenv(name)
    if value is not None:
        return value
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default

@dataclass(frozen=True)
class Settings:
    app_name: str = setting("APP_NAME", "JARVIS QUANT AI")
    db_path: str = setting("DB_PATH", "data/quant.db")
    upstox_client_id: str = setting("UPSTOX_CLIENT_ID")
    upstox_client_secret: str = setting("UPSTOX_CLIENT_SECRET")
    upstox_redirect_uri: str = setting("UPSTOX_REDIRECT_URI", "http://127.0.0.1:8765")
    upstox_access_token: str = setting("UPSTOX_ACCESS_TOKEN")
    ollama_base_url: str = setting("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = setting("OLLAMA_MODEL", "qwen3.5:4b")
    cloud_base_url: str = setting("CLOUD_LLM_BASE_URL")
    cloud_api_key: str = setting("CLOUD_LLM_API_KEY")
    cloud_model: str = setting("CLOUD_LLM_MODEL")
    live_env_enabled: bool = setting("LIVE_TRADING_ENABLED", "false").lower() == "true"
    live_phrase: str = setting("LIVE_CONFIRMATION_PHRASE", "I AUTHORIZE LIVE TRADING")
    paper_capital: float = 15000.0
    risk_per_trade: float = 150.0
    daily_loss_limit: float = 450.0
    max_trades_per_day: int = 2
    max_leverage: float = 3.0
    max_slippage_pct: float = 0.1

settings = Settings()
