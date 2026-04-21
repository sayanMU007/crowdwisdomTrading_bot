"""
Central configuration for CrowdWisdomTrading pipeline.
Edit this file to change assets, timeframes, and model settings.
"""

# Assets to trade
ASSETS = ["BTC", "ETH"]

# Timeframes to analyze
TIMEFRAMES = ["5min", "15min"]

# Number of OHLCV bars to fetch per asset
BARS_TO_FETCH = 1000

# Free OpenRouter model (change to any model at https://openrouter.ai/models)
MODEL = "meta-llama/llama-4-maverick:free"

# Log file path
LOG_FILE = "logs/trading.log"

# Kelly criterion settings
HALF_KELLY = True          # Use half-Kelly for conservative sizing
MAX_POSITION_PCT = 0.10    # Never bet more than 10% of bankroll

# Prediction confidence threshold — skip trade if below this
MIN_CONFIDENCE = 0.50

# Apify actor for OHLCV data
APIFY_ACTOR = "lukaskrivka/binance-ohlcv"

# Polymarket API base
POLYMARKET_API = "https://clob.polymarket.com"

# Kalshi API base
KALSHI_API = "https://trading-api.kalshi.com/trade-api/v2"
