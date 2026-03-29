import streamlit as st
import requests
import json
from datetime import datetime, timedelta

st.set_page_config(
    page_title="SC Disruption Radar",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .main { background: #f5f4f0; }
    .block-container { padding: 1.5rem 2rem 3rem; max-width: 1100px; }
    .radar-header {
        background: #1a1a18; border-radius: 16px; padding: 22px 28px;
        margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center;
    }
    .radar-header h1 { font-size: 22px; font-weight: 600; color: #fff; margin: 0 0 3px; }
    .radar-header p  { font-size: 12px; color: #9a9a92; margin: 0; }
    
    /* FIX: Added explicit dark color for visibility in boxes */
    .item-box { 
        background: #f5f4f0; 
        border-radius: 8px; 
        padding: 9px 12px; 
        margin-bottom: 6px; 
        font-size: 12px; 
        color: #1a1a18; 
    }
    
    .company-insight { border-radius: 10px; padding: 14px 16px; margin-bottom: 14px; border: 0.5px solid rgba(0,0,0,0.08); }
    .ci-label { font-size: 10px; font-weight: 600; padding: 2px 9px; border-radius: 20px; display: inline-block; margin-bottom: 8px; }
    .ci-body { font-size: 12px; line-height: 1.65; }
    .risk-card { background: white; border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; border: 0.5px solid rgba(0,0,0,0.08); }
    .risk-high   { border-left: 3px solid #e24b4a; border-radius: 0 10px 10px 0; }
    .risk-medium { border-left: 3px solid #ef9f27; border-radius: 0 10px 10px 0; }
    .risk-low    { border-left: 3px solid #1d9e75; border-radius: 0 10px 10px 0; }
    .risk-badge { display: inline-block; font-size: 10px; font-weight: 600; padding: 2px 9px; border-radius: 20px; margin-bottom: 6px; letter-spacing: .03em; }
    .badge-high   { background: #fcebeb; color: #a32d2d; }
    .badge-medium { background: #faeeda; color: #633806; }
    .badge-low    { background: #e1f5ee; color: #085041; }
    .badge-info   { background: #e6f1fb; color: #0c447c; }
    .metric-box { background: white; border-radius: 10px; padding: 12px; border: 0.5px solid rgba(0,0,0,0.08); text-align: center; }
    .metric-val   { font-size: 22px; font-weight: 600; line-height: 1.1; }
    .metric-label { font-size: 10px; color: #9a9a92; margin-top: 3px; text-transform: uppercase; letter-spacing: .04em; }
    .item-src { font-size: 10px; color: #9a9a92; margin-top: 2px; font-family: 'DM Mono', monospace; }
    .section-title { font-size: 10px; font-weight: 600; color: #9a9a92; text-transform: uppercase; letter-spacing: .06em; margin: 14px 0 7px; }
    .alt-pill { display: inline-block; font-size: 11px; font-weight: 500; padding: 3px 10px; border-radius: 20px; background: #e6f1fb; color: #0c447c; margin: 3px 3px 0 0; }
    .stButton > button { background: #1a1a18; color: white; border: none; border-radius: 10px; padding: 10px 24px; font-size: 13px; font-weight: 500; font-family: 'DM Sans', sans-serif; width: 100%; }
    .stButton > button:hover { background: #3a3a38; border: none; }
    .stTextInput > div > div > input { border-radius: 10px; border: 0.5px solid rgba(0,0,0,0.15); font-family: 'DM Sans', sans-serif; font-size: 13px; padding: 10px 14px; }
    .footer { font-size: 10px; color: #9a9a92; text-align: center; margin-top: 28px; font-family: 'DM Mono', monospace; }
    .ctx-label { font-size: 9px; font-weight: 600; color: #9a9a92; text-transform: uppercase; letter-spacing: .07em; margin-bottom: 6px; }
</style>
""", unsafe_allow_html=True)

# (Companies data remains the same...)
COMPANIES = {
    "L'Oréal": {
        "sector": "Beauty & Personal Care",
        "color": "#d4537e",
        "bg": "#fbeaf0",
        "text_color": "#72243e",
        "insight": "L'Oréal sources 95% of palm oil derivatives through certified channels, but EUDR compliance by Dec 2025 remains under pressure across Tier 2 suppliers. Mica supply from India carries reputational and CSDDD (2026) compliance risk.",
        "commodities": ["Palm oil", "Mica", "Ethanol", "Glass packaging", "Aluminium", "Shea butter"],
        "suppliers": ["Firmenich", "Givaudan", "AkzoNobel", "Verallia"],
        "regions": ["Indonesia", "India", "France", "Germany"],
    },
    "LVMH": {
        "sector": "Luxury Goods",
        "color": "#534ab7",
        "bg": "#eeedfe",
        "text_color": "#3c3489",
        "insight": "LVMH supply chains are uniquely concentrated in artisan suppliers. EU ESPR digital product passport requirements (2027) force full hide-to-goods traceability. Cashmere from Mongolia carries geopolitical risk.",
        "commodities": ["Leather (Italian)", "Cashmere", "Cognac grapes", "Champagne", "Gold", "Diamonds"],
        "suppliers": ["Remy Cointreau", "Hermès tanneries", "Italian leather SMEs", "De Beers"],
        "regions": ["Italy", "Mongolia", "Cognac region", "South Africa"],
    },
    "Schneider Electric": {
        "sector": "Energy Management",
        "color": "#0f6e56",
        "bg": "#e1f5ee",
        "text_color": "#085041",
        "insight": "Copper represents 25-30% of Schneider's direct material cost. Rare earth elements for motors are China-processing-concentrated (>70%). PCBA supply from Taiwan remains geopolitically exposed.",
        "commodities": ["Copper", "Rare earth elements", "Steel", "PCBs / semiconductors", "Aluminium", "Lithium"],
        "suppliers": ["Flex Ltd", "Jabil", "STMicroelectronics", "Vale", "Glencore"],
        "regions": ["China", "Chile", "DRC", "Taiwan"],
    },
    "Amazon": {
        "sector": "E-commerce & Logistics",
        "color": "#185fa5",
        "bg": "#e6f1fb",
        "text_color": "#0c447c",
        "insight": "Amazon's SC risk concentrates in last-mile logistics capacity and Asian manufacturer dependency. The shift to electric delivery fleets introduces battery SC exposure.",
        "commodities": ["Air freight capacity", "Cardboard / packaging", "Lithium (EV fleet)", "Semiconductors", "Diesel fuel"],
        "suppliers": ["UPS", "DHL", "CEVA Logistics", "Foxconn", "Rivian"],
        "regions": ["China", "Germany", "UK", "Poland", "India"],
    },
    "Custom scan": {
        "sector": "Any company or commodity",
        "color": "#5a5a54",
        "bg": "#f0efe9",
        "text_color": "#444441",
        "insight": "",
        "commodities": ["TSMC", "Red Sea", "Lithium", "Foxconn", "Palm oil", "Ukraine wheat"],
        "suppliers": [],
        "regions": [],
    },
}

# (Functions fetch_news, analyze_risk, etc. remain the same...)
def fetch_news(query, news_api_key, days_back=7):
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    params = {"q": query, "from": from_date, "sortBy": "relevancy", "language": "en", "pageSize": 15, "apiKey": news_api_key}
    try:
        r = requests.get("https://newsapi.org/v2/everything", params=params, timeout=10)
        data = r.json()
        return data.get("articles", []) if data.get("status") == "ok" else []
    except: return []

def analyze_risk(target, company_name, company_context, news_digest, groq_key):
    # (Same prompt logic as before...)
    system_prompt = f"You are a senior supply chain risk analyst. Provide a JSON risk brief for {target}."
    # ... logic for API call ...
    return {} # Placeholder for original logic in app.py

# ... (Insert original logic for session state and display from app.py) ...

# ── Updated Header (Free Tier Text Removed) ───────────────────────────────────
st.markdown("""
<div class="radar-header">
  <div>
    <h1>SC Disruption Radar</h1>
    <p>Real-time supply chain risk intelligence — personalised by company</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ... (Rest of the original UI code follows) ...
