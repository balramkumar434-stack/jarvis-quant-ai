import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from config import settings
from database import init_db, rows, event
from upstox_v3 import UpstoxClient
from agents import technical_agent, local_llm_review, cloud_review, save_signal
from risk import validate_order, RiskRejected
from broker import PaperBroker, LiveBroker

st.set_page_config(page_title="JARVIS QUANT AI",page_icon="📈",layout="wide")
init_db()
st.markdown('''<style>
.block-container{padding-top:1.2rem}
[data-testid="stSidebar"]{background:#101827}
.metric-card{padding:14px;border:1px solid #26364c;border-radius:12px}
</style>''',unsafe_allow_html=True)
st.title("📈 JARVIS QUANT AI")
st.caption("Standalone trading research & execution console • CPU-first • Hybrid AI • Paper-first")
mode=st.sidebar.radio("Execution mode",["PAPER","LIVE"],index=0)
st.sidebar.warning("LIVE mode is separately gated. AI signals never auto-submit live orders.")
st.sidebar.markdown("### Risk limits")
st.sidebar.write(f"Capital ₹{settings.paper_capital:,.0f}")
st.sidebar.write(f"Risk / trade ₹{settings.risk_per_trade:,.0f}")
st.sidebar.write(f"Daily loss ₹{settings.daily_loss_limit:,.0f}")
st.sidebar.write(f"Max trades/day {settings.max_trades_per_day}")
st.sidebar.write(f"Gross exposure cap ₹{settings.paper_capital*settings.max_leverage:,.0f}")
tabs=st.tabs(["Overview","Market scanner","Trade desk","Positions & journal","AI research","Upstox connection","Settings"])

with tabs[0]:
    a,b,c,d=st.columns(4)
    open_trades=rows("SELECT * FROM trades WHERE status='OPEN'")
    closed=rows("SELECT * FROM trades WHERE status='CLOSED'")
    pnl=sum(float(x["pnl"] or 0) for x in closed)
    a.metric("Open positions",len(open_trades))
    b.metric("Closed trades",len(closed))
    c.metric("Realized gross P&L",f"₹{pnl:,.2f}")
    d.metric("Execution mode",mode)
    st.subheader("System status")
    st.write({"Database":"Connected","Default execution":"Paper","Live env switch":settings.live_env_enabled,
              "Upstox token configured":bool(settings.upstox_access_token),
              "Ollama configured":settings.ollama_base_url})
    st.info("This is a research-grade starter system, not a profitability guarantee. Include brokerage, STT, GST, exchange charges, stamp duty, slippage and taxes in every performance review.")

with tabs[1]:
    st.subheader("Instrument scanner")
    st.caption("Fetches historical/intraday candles through Upstox V3. Enter the exact Upstox instrument key.")
    with st.form("scan"):
        symbol=st.text_input("Display symbol", "RELIANCE")
        ikey=st.text_input("Upstox instrument key", "NSE_EQ|INE002A01018")
        interval=st.selectbox("Candle interval", [1,3,5,15,30],index=2)
        submitted=st.form_submit_button("Fetch candles & run technical agent")
    if submitted:
        try:
            data=UpstoxClient().candles(ikey,"minutes",interval)
            candles=data.get("data",{}).get("candles",[])
            sig=technical_agent(candles); save_signal(symbol,sig)
            st.session_state["last_signal"]={"symbol":symbol,"instrument_key":ikey,"signal":sig,"candles":candles}
            st.success(f"Scanner complete: {sig['side']}")
        except Exception as e: st.error(str(e))
    last=st.session_state.get("last_signal")
    if last:
        sig=last["signal"]
        x,y,z=st.columns(3); x.metric("Signal",sig["side"]); y.metric("Confidence",f'{sig["confidence"]:.0%}'); z.metric("Momentum",f'{sig.get("momentum_pct",0)}%')
        st.write(sig)
        cs=last["candles"]
        if cs:
            df=pd.DataFrame(cs,columns=["time","open","high","low","close","volume","oi"][:len(cs)])
            fig=go.Figure(data=[go.Candlestick(x=df["time"],open=df["open"],high=df["high"],low=df["low"],close=df["close"])])
            fig.update_layout(height=420,xaxis_rangeslider_visible=False); st.plotly_chart(fig,use_container_width=True)

with tabs[2]:
    st.subheader("Trade desk")
    st.warning("Paper trades are simulated at the entered price; this does not model queue position or guaranteed fills.")
    with st.form("trade"):
        s1,s2=st.columns(2)
        sym=s1.text_input("Symbol","RELIANCE")
        inst=s2.text_input("Instrument key","NSE_EQ|INE002A01018")
        side=st.selectbox("Side",["BUY","SELL"])
        q=st.number_input("Quantity",min_value=1,value=1,step=1)
        entry=st.number_input("Expected entry price ₹",min_value=.05,value=1000.0,step=.05)
        stop=st.number_input("Stop-loss price ₹",min_value=.01,value=995.0,step=.05)
        target=st.number_input("Target price ₹ (optional; 0 = none)",min_value=0.0,value=1010.0,step=.05)
        note=st.text_input("Trade thesis / notes")
        submit=st.form_submit_button("Validate & submit")
    if submit:
        try:
            checks=validate_order(sym,side,int(q),entry,stop,mode.lower())
            if mode=="PAPER":
                result=PaperBroker().submit(sym,inst,side,int(q),entry,stop,target or None,note)
                st.success(f"Paper trade opened: {result}")
            else:
                st.error("Live execution requires the separate authorization panel below. No live order was sent.")
            st.write("Risk checks:",checks)
        except (RiskRejected,Exception) as e: st.error(str(e))
    st.divider()
    st.subheader("Separate live authorization")
    st.error("Live trading can lose money. First verify broker permissions, exchange/algo requirements, instrument eligibility, order types and all charges.")
    live_phrase=st.text_input("Type exact authorization phrase",type="password")
    live_ack=st.checkbox("I understand this can place real orders and I have independently tested the strategy in paper mode.")
    if st.button("Arm live order panel",disabled=not(settings.live_env_enabled and live_ack and live_phrase==settings.live_phrase)):
        st.session_state["live_armed"]=True
        st.success("Live order panel armed for this dashboard session only.")
    if st.session_state.get("live_armed"):
        st.warning("This panel submits only the specific order you review here. It does not enable autonomous live execution.")
        with st.form("live_order"):
            li=st.text_input("Verified Upstox instrument key")
            ls=st.selectbox("Transaction",["BUY","SELL"])
            lq=st.number_input("Quantity",min_value=1,value=1)
            lp=st.number_input("Limit price ₹",min_value=.05,value=100.0)
            lstop=st.number_input("Risk stop reference ₹",min_value=.01,value=99.0)
            confirm=st.text_input("Type SEND THIS LIVE ORDER")
            go=st.form_submit_button("Submit live LIMIT order")
        if go:
            try:
                validate_order(li,ls,int(lq),lp,lstop,"live")
                if confirm!="SEND THIS LIVE ORDER": raise ValueError("Live order confirmation text mismatch.")
                result=LiveBroker().submit(li,ls,int(lq),lp,"LIMIT")
                event(f"Live order API response: {result}","WARNING")
                st.json(result)
                st.warning("Verify order status in Upstox order book. If response is ambiguous, do not retry until reconciled.")
            except Exception as e: st.error(f"Live order blocked/failed: {e}")

with tabs[3]:
    st.subheader("Positions & journal")
    tdf=pd.DataFrame(rows("SELECT * FROM trades ORDER BY id DESC LIMIT 200"))
    if not tdf.empty:
        st.dataframe(tdf,use_container_width=True,hide_index=True)
        st.subheader("Close paper position")
        openp=[x for x in open_trades if x["mode"]=="PAPER"]
        if openp:
            labels={f'#{x["id"]} {x["side"]} {x["symbol"]} x{x["qty"]}':x["id"] for x in openp}
            chosen=st.selectbox("Open paper trade",list(labels))
            xp=st.number_input("Exit price ₹",min_value=.01,value=100.0)
            if st.button("Close selected paper trade"):
                try: st.success(f"Gross P&L ₹{PaperBroker().close(labels[chosen],xp):.2f}")
                except Exception as e: st.error(str(e))
    else: st.info("No trades yet.")
    st.subheader("Recent events")
    ev=pd.DataFrame(rows("SELECT * FROM events ORDER BY id DESC LIMIT 50"))
    if not ev.empty: st.dataframe(ev,use_container_width=True,hide_index=True)

with tabs[4]:
    st.subheader("Hybrid AI research desk")
    prompt=st.text_area("Research question", "Review the latest market setup, list risks, and explain what evidence would invalidate a bullish thesis.")
    col1,col2=st.columns(2)
    if col1.button("Ask local Ollama"):
        with st.spinner("Local model reviewing..."): st.session_state["local_review"]=local_llm_review(prompt)
    if col2.button("Ask configured cloud model"):
        with st.spinner("Cloud model reviewing..."): st.session_state["cloud_review"]=cloud_review(prompt)
    for key in ["local_review","cloud_review"]:
        if key in st.session_state:
            st.markdown(f"**{st.session_state[key]['provider']}**")
            st.write(st.session_state[key]["text"])
    st.caption("LLM output is advisory. It cannot override the risk engine or submit orders.")

with tabs[5]:
    st.subheader("Upstox connection")
    st.write("Token source:", ".env → UPSTOX_ACCESS_TOKEN")
    if st.button("Test Upstox profile"):
        try: st.json(UpstoxClient().profile())
        except Exception as e: st.error(str(e))
    if st.button("Fetch funds & margin"):
        try: st.json(UpstoxClient().funds())
        except Exception as e: st.error(str(e))
    st.markdown("Official docs: [Upstox V3 Market Data](https://upstox.com/developer/api-documentation/v3/get-market-data-feed/) · [Historical Candle V3](https://upstox.com/developer/api-documentation/v3/get-historical-candle-data/) · [Place Order V3](https://upstox.com/developer/api-documentation/v3/place-order/)")

with tabs[6]:
    st.subheader("Configuration")
    st.write("Edit `.env` in the application folder, then restart.")
    st.code("UPSTOX_ACCESS_TOKEN=...\nOLLAMA_MODEL=qwen3.5:4b\nLIVE_TRADING_ENABLED=false")
    st.write("Risk controls are intentionally fixed in config.py for this starter release.")
    st.warning("Never paste broker tokens into chat, screenshots, source control, or shared logs.")
