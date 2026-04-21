"""
Agent 2: Data Fetch Agent
Fetches the last N OHLCV bars for a crypto asset using Apify.
Also fetches multi-timeframe data for arbitrage analysis.
"""

from loguru import logger
from tools.apify_tool import fetch_ohlcv, fetch_multi_timeframe
from config.settings import BARS_TO_FETCH


def run(asset: str, multi_timeframe: bool = True) -> dict:
    """
    Fetch OHLCV data for an asset.

    Args:
        asset:           e.g. "BTC"
        multi_timeframe: If True, also fetch 15-min data for arbitrage

    Returns:
        dict with keys "5m" (list of bars) and optionally "15m"
    """
    logger.info(f"[DataFetchAgent] Fetching data for {asset} (multi_tf={multi_timeframe})")

    if multi_timeframe:
        data = fetch_multi_timeframe(asset, bars=BARS_TO_FETCH)
        bars_5m = len(data.get("5m", []))
        bars_15m = len(data.get("15m", []))
        logger.success(f"[DataFetchAgent] {asset}: {bars_5m} x 5m bars, {bars_15m} x 15m bars")
    else:
        bars = fetch_ohlcv(asset, bars=BARS_TO_FETCH)
        data = {"5m": bars}
        logger.success(f"[DataFetchAgent] {asset}: {len(bars)} bars fetched")

    return data
