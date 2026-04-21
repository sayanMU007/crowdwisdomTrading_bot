# CrowdWisdomTrading — Crypto Prediction Agent

A multi-agent Python pipeline: Polymarket + Kalshi search, Apify OHLCV data,
Kronos-style directional prediction, Kelly position sizing, and Hermes feedback loop.

## Quick Start (Windows / VS Code Terminal)

```powershell
# 1. Install deps
pip install uv
uv venv venv --python 3.11
.\venv\Scripts\activate
uv pip install -r requirements.txt

# 2. Set up keys
copy .env.example .env
# Open .env and fill in OPENROUTER_API_KEY and APIFY_TOKEN

# 3. Run
python main.py

# Optional: auto-run every 5 min
python scheduler.py

# Optional: web dashboard at http://localhost:8000
python dashboard.py
```

## API Keys Needed

| Variable | Where to get it |
|---|---|
| `OPENROUTER_API_KEY` | https://openrouter.ai (free) |
| `APIFY_TOKEN` | https://apify.com → Settings → Integrations (free) |

## Architecture

- **Agent 1** `market_search_agent` — Polymarket + Kalshi 5-min predictions
- **Agent 2** `data_fetch_agent` — Apify OHLCV (1000 bars, 5m + 15m)
- **Agent 3** `prediction_agent` — Kronos-style UP/DOWN + cross-timeframe arbitrage
- **Agent 4** `risk_agent` — Kelly criterion position sizing
- **Agent 5** `orchestrator` — Hermes LLM feedback loop + final recommendations

## Scaling

- Add assets in `config/settings.py` → `ASSETS`
- Cross-timeframe arbitrage is built-in (5m vs 15m)
- `scheduler.py` runs unattended every 5 minutes
- `dashboard.py` shows a live web UI
