# SC Disruption Radar

Real-time supply chain risk intelligence tool. Enter any supplier name, 
commodity, or region and get an AI-generated risk brief powered by live news.

**Built with:** Streamlit · NewsAPI · Claude API (Anthropic)

---

## What it does

1. Takes a target input (e.g. "TSMC", "lithium", "Red Sea", "Foxconn")
2. Fetches the last 7 days of news from NewsAPI
3. Sends headlines to Claude for structured risk analysis
4. Returns: overall risk level, risk factors by category, key signals, 
   recommended actions, and alternative sourcing regions

---

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

You'll need:
- **NewsAPI key** — free at https://newsapi.org (100 requests/day free tier)
- **Anthropic API key** — get one at https://console.anthropic.com

---

## Deploy to Streamlit Community Cloud (free)

1. Push this folder to a GitHub repo (public or private)
2. Go to https://share.streamlit.io
3. Click "New app" → select your repo → set main file as `app.py`
4. Add your API keys as Secrets:
   ```toml
   # .streamlit/secrets.toml
   NEWS_API_KEY = "your_newsapi_key"
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
5. Deploy — you get a live URL like `https://yourname-sc-radar.streamlit.app`

---

## Using secrets in production

If you want the app to auto-load keys without users entering them,
update `app.py` to use `st.secrets`:

```python
news_key = st.secrets.get("NEWS_API_KEY", "")
claude_key = st.secrets.get("ANTHROPIC_API_KEY", "")
```

Replace the manual key entry section with this and redeploy.

---

## Project structure

```
sc-radar/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## Built by

[Your Name] — MiM student at HEC Paris, IIT Kharagpur alumnus  
Research Assistant (AI/Data) | Supply Chain & Strategy  
[Your LinkedIn URL]
