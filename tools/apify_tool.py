"""
Data Tool — fetches OHLCV data directly from Binance public API.
No Apify needed for OHLCV. Apify token is still used for other scraping tasks.
"""

import requests
from loguru import logger

BINANCE_API = "https://api.binance.com/api/v3/klines"

SYMBOL_MAP = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "SOL": "SOLUSDT",
    "BNB": "BNBUSDT",
    "DOGE": "DOGEUSDT",
    "XRP": "XRPUSDT",
}

def fetch_ohlcv(asset: str, bars: int = 1000, interval: str = "5m") -> list:
    symbol = SYMBOL_MAP.get(asset.upper(), f"{asset.upper()}USDT")
    try:
        logger.info(f"[Binance] Fetching {bars} x {interval} bars for {symbol}")
        resp = requests.get(
            BINANCE_API,
            params={"symbol": symbol, "interval": interval, "limit": min(bars, 1000)},
            timeout=15,
        )
        resp.raise_for_status()
        raw = resp.json()
        bars_list = [
            {
                "open_time": r[0], "open": float(r[1]), "high": float(r[2]),
                "low": float(r[3]), "close": float(r[4]), "volume": float(r[5]),
                "close_time": r[6],
            }
            for r in raw
        ]
        logger.success(f"[Binance] Got {len(bars_list)} bars for {symbol}")
        return bars_list
    except Exception as e:
        logger.error(f"[Binance] Failed for {asset}: {e}")
        return []

def fetch_multi_timeframe(asset: str, bars: int = 1000) -> dict:
    return {
        "5m":  fetch_ohlcv(asset, bars=bars, interval="5m"),
        "15m": fetch_ohlcv(asset, bars=bars // 3, interval="15m"),
    }