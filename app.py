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
    .radar-header-right { font-size: 10px; color: #5a5a54; text-align: right; font-family: 'DM Mono', monospace; }
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
    .item-box { background: #f5f4f0; border-radius: 8px; padding: 9px 12px; margin-bottom: 6px; font-size: 12px; }
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


# ── Company profiles ─────────────────────────────────────────────────────────────

COMPANIES = {
    "L'Oréal": {
        "sector": "Beauty & Personal Care",
        "color": "#d4537e",
        "bg": "#fbeaf0",
        "text_color": "#72243e",
        "insight": (
            "L'Oréal sources 95% of palm oil derivatives through certified channels, "
            "but EUDR compliance by Dec 2025 remains under pressure across Tier 2 suppliers. "
            "Mica supply from India carries reputational and CSDDD (2026) compliance risk. "
            "Glass and aluminium packaging represent ~40% of total packaging cost."
        ),
        "commodities": ["Palm oil", "Mica", "Ethanol", "Glass packaging", "Aluminium", "Shea butter"],
        "suppliers": ["Firmenich", "Givaudan", "AkzoNobel", "Verallia"],
        "regions": ["Indonesia", "India", "France", "Germany"],
    },
    "LVMH": {
        "sector": "Luxury Goods",
        "color": "#534ab7",
        "bg": "#eeedfe",
        "text_color": "#3c3489",
        "insight": (
            "LVMH supply chains are uniquely concentrated in artisan suppliers — many single-source. "
            "Louis Vuitton leather is 80% sourced from ~12 Tuscan tanneries. "
            "EU ESPR digital product passport requirements (2027) force full hide-to-goods "
            "traceability. Cashmere from Mongolia and Inner China carries geopolitical risk."
        ),
        "commodities": ["Leather (Italian)", "Cashmere", "Cognac grapes", "Champagne", "Gold", "Diamonds"],
        "suppliers": ["Remy Cointreau", "Hermès tanneries", "Italian leather SMEs", "De Beers"],
        "regions": ["Italy", "Mongolia", "Cognac region", "South Africa"],
    },
    "Schneider Electric": {
        "sector": "Energy Management",
        "color": "#0f6e56",
        "bg": "#e1f5ee",
        "text_color": "#085041",
        "insight": (
            "Copper represents 25-30% of Schneider's direct material cost. "
            "Prices have surged 22% YoY on energy transition demand. "
            "Rare earth elements for motors are China-processing-concentrated (>70%). "
            "PCBA and semiconductor supply from Taiwan remains geopolitically exposed. "
            "FY2025 copper hedge ratio is ~65%, leaving 35% at spot market risk."
        ),
        "commodities": ["Copper", "Rare earth elements", "Steel", "PCBs / semiconductors", "Aluminium", "Lithium"],
        "suppliers": ["Flex Ltd", "Jabil", "STMicroelectronics", "Vale", "Glencore"],
        "regions": ["China", "Chile", "DRC", "Taiwan"],
    },
    "Amazon": {
        "sector": "E-commerce & Logistics",
        "color": "#185fa5",
        "bg": "#e6f1fb",
        "text_color": "#0c447c",
        "insight": (
            "Amazon's SC risk concentrates in last-mile logistics capacity and Asian manufacturer dependency. "
            "Last-mile driver availability in Germany and France runs 12-15% below demand. "
            "The shift to electric delivery fleets (Rivian partnership) introduces battery SC exposure. "
            "Q4 peak season freight cost surges of 18-22% are a recurring structural pressure on EU margins."
        ),
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


# ── Helpers ──────────────────────────────────────────────────────────────────────

def fetch_news(query: str, news_api_key: str, days_back: int = 7) -> list[dict]:
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    params = {
        "q": query, "from": from_date, "sortBy": "relevancy",
        "language": "en", "pageSize": 15, "apiKey": news_api_key,
    }
    try:
        r = requests.get("https://newsapi.org/v2/everything", params=params, timeout=10)
        data = r.json()
        if data.get("status") == "ok":
            return data.get("articles", [])
        st.warning(f"NewsAPI: {data.get('message', 'Unknown error')}")
        return []
    except Exception as e:
        st.error(f"News fetch failed: {e}")
        return []


def build_news_digest(articles: list[dict]) -> str:
    if not articles:
        return "No recent news articles found."
    lines = []
    for i, a in enumerate(articles[:12], 1):
        title  = a.get("title", "")
        source = a.get("source", {}).get("name", "Unknown")
        desc   = a.get("description") or ""
        pub    = a.get("publishedAt", "")[:10]
        lines.append(f"{i}. [{source} | {pub}] {title}. {desc[:120]}")
    return "\n".join(lines)


def analyze_risk(target: str, company_name: str, company_context: str,
                  news_digest: str, groq_key: str) -> dict:

    company_block = (
        f"\nCompany context: This scan is for {company_name}. {company_context}\n"
        f"Tailor all findings, risk framing, and recommendations specifically to "
        f"{company_name}'s business model, regulatory exposure, and supplier relationships.\n"
        if company_name != "Custom scan" else ""
    )

    system_prompt = f"""You are a senior supply chain risk intelligence analyst.
Given a target and recent news, produce a structured risk brief in JSON only.
No preamble, no markdown fences, no code blocks — raw JSON only.
{company_block}
Return exactly this JSON structure:
{{
  "overall_risk": "HIGH or MEDIUM or LOW",
  "risk_score": <integer 1-10>,
  "one_line_summary": "<max 20 words>",
  "risk_factors": [
    {{"category": "<Geopolitical|Weather|Financial|Logistics|Labour|Regulatory|Reputational|Supply>",
      "level": "HIGH or MEDIUM or LOW",
      "finding": "<1-2 sentences specific to {company_name if company_name != 'Custom scan' else 'the buyer'}>"
    }},
    {{"category": "...", "level": "...", "finding": "..."}},
    {{"category": "...", "level": "...", "finding": "..."}}
  ],
  "key_signals": ["<signal 1>", "<signal 2>", "<signal 3>", "<signal 4>", "<signal 5>"],
  "recommended_actions": [
    "<action 1 specific to {company_name if company_name != 'Custom scan' else 'the company'}>",
    "<action 2>",
    "<action 3>"
  ],
  "alternative_regions": ["<alternative 1>", "<alternative 2>", "<alternative 3>"],
  "analyst_note": "<2-3 sentence plain-English summary for a senior SC manager at {company_name if company_name != 'Custom scan' else 'the company'}>"
}}
Return valid JSON only. No other text."""

    user_prompt = f"""Target: {target}

Recent news (last 7 days):
{news_digest}

Return the risk brief JSON now."""

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 1400,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=payload, timeout=30
        )
        r.raise_for_status()
        raw = r.json()["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except json.JSONDecodeError as e:
        st.error(f"AI returned non-JSON: {e}")
        return {}
    except Exception as e:
        st.error(f"AI API error: {e}")
        return {}


def risk_color(level: str) -> str:
    return {"HIGH": "#e24b4a", "MEDIUM": "#ef9f27", "LOW": "#1d9e75"}.get(level.upper(), "#888")

def badge_cls(level: str) -> str:
    return {"HIGH": "badge-high", "MEDIUM": "badge-medium", "LOW": "badge-low"}.get(level.upper(), "badge-info")

def card_cls(level: str) -> str:
    return {"HIGH": "risk-high", "MEDIUM": "risk-medium", "LOW": "risk-low"}.get(level.upper(), "")

def score_emoji(s: int) -> str:
    return "🔴" if s >= 8 else "🟡" if s >= 5 else "🟢"


# ── Session state ────────────────────────────────────────────────────────────────

if "selected_company" not in st.session_state:
    st.session_state["selected_company"] = "L'Oréal"
if "scan_target" not in st.session_state:
    st.session_state["scan_target"] = ""


# ── Header ───────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="radar-header">
  <div>
    <h1>SC Disruption Radar</h1>
    <p>Real-time supply chain risk intelligence — personalised by company</p>
  </div>
  <div class="radar-header-right">NewsAPI + Groq AI<br>Free tier</div>
</div>
""", unsafe_allow_html=True)


# ── API keys ─────────────────────────────────────────────────────────────────────

with st.expander("⚙️  API keys — both free, no credit card required", expanded=False):
    st.markdown(
        "**NewsAPI** → [newsapi.org](https://newsapi.org) &nbsp;|&nbsp; "
        "**Groq** → [console.groq.com/keys](https://console.groq.com/keys)"
    )
    c1, c2 = st.columns(2)
    with c1:
        nk = st.text_input("NewsAPI key", type="password",
                            value=st.session_state.get("news_key", ""),
                            placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    with c2:
        gk = st.text_input("Groq API key", type="password",
                            value=st.session_state.get("groq_key", ""),
                            placeholder="gsk_...")
    if nk: st.session_state["news_key"] = nk
    if gk: st.session_state["groq_key"] = gk

st.markdown("---")


# ── Company selector ──────────────────────────────────────────────────────────────

st.markdown('<div class="section-title" style="margin-top:0">Select company</div>',
            unsafe_allow_html=True)

co_cols = st.columns(len(COMPANIES))
for col, (co_name, co_data) in zip(co_cols, COMPANIES.items()):
    with col:
        is_active = st.session_state["selected_company"] == co_name
        border = f"2px solid {co_data['color']}" if is_active else "0.5px solid rgba(0,0,0,0.12)"
        bg     = co_data["bg"] if is_active else "white"
        st.markdown(f"""
        <div style="background:{bg};border:{border};border-radius:10px;
                    padding:9px 12px;margin-bottom:6px">
          <div style="font-size:12px;font-weight:600;color:{co_data['color']}">{co_name}</div>
          <div style="font-size:10px;color:#9a9a92;margin-top:2px">{co_data['sector']}</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Select", key=f"co_{co_name}", use_container_width=True):
            st.session_state["selected_company"] = co_name
            st.session_state["scan_target"] = ""
            st.rerun()

selected_co = st.session_state["selected_company"]
co = COMPANIES[selected_co]


# ── Context bar ───────────────────────────────────────────────────────────────────

if selected_co != "Custom scan":
    with st.container():
        st.markdown(
            f'<div style="background:white;border-radius:10px;padding:14px 16px;'
            f'margin-bottom:14px;border:0.5px solid rgba(0,0,0,0.08)">',
            unsafe_allow_html=True
        )
        cb1, cb2, cb3 = st.columns([2, 1, 1])

        with cb1:
            st.markdown('<div class="ctx-label">Key commodities — click to scan</div>',
                        unsafe_allow_html=True)
            comm_cols = st.columns(3)
            for i, comm in enumerate(co["commodities"]):
                with comm_cols[i % 3]:
                    if st.button(comm, key=f"comm_{comm}", use_container_width=True):
                        st.session_state["scan_target"] = comm
                        st.rerun()

        with cb2:
            st.markdown('<div class="ctx-label">Key suppliers</div>', unsafe_allow_html=True)
            pills = " ".join([
                f'<span style="display:inline-block;font-size:10px;padding:2px 8px;'
                f'border-radius:20px;background:#f0efe9;color:#5a5a54;margin:2px 2px 0 0">{s}</span>'
                for s in co["suppliers"]
            ])
            st.markdown(pills, unsafe_allow_html=True)

        with cb3:
            st.markdown('<div class="ctx-label">Risk regions — click to scan</div>',
                        unsafe_allow_html=True)
            for region in co["regions"]:
                if st.button(region, key=f"reg_{region}", use_container_width=True):
                    st.session_state["scan_target"] = region
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown('<div class="section-title">Quick scans</div>', unsafe_allow_html=True)
    qcols = st.columns(6)
    for i, item in enumerate(co["commodities"]):
        with qcols[i]:
            if st.button(item, key=f"q_{item}", use_container_width=True):
                st.session_state["scan_target"] = item
                st.rerun()


# ── Search bar ────────────────────────────────────────────────────────────────────

sc1, sc2, sc3 = st.columns([3, 1, 1])
with sc1:
    typed = st.text_input(
        "target", label_visibility="collapsed",
        value=st.session_state["scan_target"],
        placeholder="Type any supplier, commodity, or region — or click above",
    )
    if typed != st.session_state["scan_target"]:
        st.session_state["scan_target"] = typed
with sc2:
    days_back = st.selectbox(
        "days", [3, 7, 14, 30], index=1,
        label_visibility="collapsed",
        format_func=lambda x: f"Last {x} days"
    )
with sc3:
    run_scan = st.button("Run radar scan", use_container_width=True)


# ── Run analysis ──────────────────────────────────────────────────────────────────

target = st.session_state["scan_target"].strip()

if run_scan and target:
    nk = st.session_state.get("news_key", "")
    gk = st.session_state.get("groq_key", "")
    if not nk or not gk:
        st.warning("Please enter both API keys in the settings panel above.")
        st.stop()

    with st.spinner(f"Scanning '{target}' in context of {selected_co}..."):
        articles    = fetch_news(f"{target} supply chain disruption risk", nk, days_back)
        news_digest = build_news_digest(articles)
        report      = analyze_risk(
            target          = target,
            company_name    = selected_co,
            company_context = co["insight"],
            news_digest     = news_digest,
            groq_key        = gk,
        )

    if not report:
        st.error("Analysis failed — check your API keys and try again.")
        st.stop()

    overall = report.get("overall_risk", "UNKNOWN")
    score   = report.get("risk_score", 0)
    summary = report.get("one_line_summary", "")
    note    = report.get("analyst_note", "")
    factors = report.get("risk_factors", [])
    signals = report.get("key_signals", [])
    actions = report.get("recommended_actions", [])
    alts    = report.get("alternative_regions", [])

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    for col, val, lbl in [
        (m1, f'<span style="color:{risk_color(overall)}">{overall}</span>', "Overall risk"),
        (m2, f"{score_emoji(score)} {score}/10", "Risk score"),
        (m3, str(len(articles)), "News signals"),
        (m4, str(len(factors)), "Risk factors"),
    ]:
        col.markdown(f"""
        <div class="metric-box">
          <div class="metric-val">{val}</div>
          <div class="metric-label">{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Company insight card
    if selected_co != "Custom scan" and co["insight"]:
        st.markdown(f"""
        <div class="company-insight" style="background:{co['bg']};border-color:{co['color']}44">
          <span class="ci-label" style="background:{co['color']};color:#fff">{selected_co} context</span>
          <span style="font-size:11px;color:#9a9a92;margin-left:8px">
            Why {target} risk matters specifically to {selected_co}
          </span>
          <div class="ci-body" style="color:{co['text_color']};margin-top:6px">{co['insight']}</div>
        </div>""", unsafe_allow_html=True)

    # Summary card
    st.markdown(f"""
    <div class="risk-card">
      <span class="risk-badge {badge_cls(overall)}">{overall} RISK — {target.upper()}</span>
      <div style="font-size:15px;font-weight:500;margin-bottom:8px">{summary}</div>
      <div style="font-size:13px;color:#5a5a54;line-height:1.6">{note}</div>
    </div>""", unsafe_allow_html=True)

    # Two-column layout
    left, right = st.columns([1.1, 0.9])

    with left:
        st.markdown('<div class="section-title">Risk factors</div>', unsafe_allow_html=True)
        for f in factors:
            lvl = f.get("level", "MEDIUM")
            st.markdown(f"""
            <div class="risk-card {card_cls(lvl)}">
              <span class="risk-badge {badge_cls(lvl)}">{lvl}</span>
              <span style="font-size:10px;font-weight:600;color:#9a9a92;margin-left:6px;
                           text-transform:uppercase;letter-spacing:.04em">{f.get('category','')}</span>
              <div style="font-size:12px;color:#3a3a38;margin-top:5px;line-height:1.55">
                {f.get('finding','')}
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-title">Recommended actions</div>', unsafe_allow_html=True)
        for i, action in enumerate(actions, 1):
            st.markdown(f"""
            <div class="item-box">
              <span style="font-weight:600;color:#185fa5;margin-right:5px">{i}.</span>{action}
            </div>""", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-title">Key signals detected</div>', unsafe_allow_html=True)
        for sig in signals:
            st.markdown(f'<div class="item-box">• {sig}</div>', unsafe_allow_html=True)

        if alts:
            st.markdown('<div class="section-title">Alternative sourcing</div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="margin-bottom:12px">' +
                "".join([f'<span class="alt-pill">{a}</span>' for a in alts]) +
                '</div>', unsafe_allow_html=True
            )

        st.markdown('<div class="section-title">Raw news headlines</div>', unsafe_allow_html=True)
        if articles:
            for a in articles[:8]:
                title  = a.get("title", "No title")
                source = a.get("source", {}).get("name", "")
                url    = a.get("url", "#")
                pub    = a.get("publishedAt", "")[:10]
                st.markdown(f"""
                <div class="item-box">
                  <a href="{url}" target="_blank"
                     style="color:#1a1a18;text-decoration:none;font-size:12px">{title}</a>
                  <div class="item-src">{source} · {pub}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="item-box" style="color:#9a9a92">No recent articles found.</div>',
                unsafe_allow_html=True
            )

elif run_scan and not target:
    st.warning("Select a commodity above or type a target to scan.")


# ── Footer ────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="footer">
  SC Disruption Radar · Streamlit + NewsAPI + Groq AI · HEC Paris MiM · IIT Kharagpur
</div>""", unsafe_allow_html=True)
