"""
Polymarket Tool — fetches active prediction markets for a crypto asset.
Docs: https://docs.polymarket.com
"""

import requests
from loguru import logger
from config.settings import POLYMARKET_API


def get_crypto_predictions(asset: str) -> dict:
    """
    Fetch next 5-min up/down prediction markets for a crypto asset.

    Args:
        asset: e.g. "BTC" or "ETH"

    Returns:
        dict with keys: asset, markets (list), error (optional)
    """
    try:
        resp = requests.get(
            f"{POLYMARKET_API}/markets",
            params={"query": f"{asset} price", "active": "true"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        markets = data.get("data", [])

        # Filter to most relevant markets containing the asset name
        relevant = [
            m for m in markets
            if asset.upper() in m.get("question", "").upper()
        ]

        logger.info(f"[Polymarket] {asset}: found {len(relevant)} relevant markets")
        return {
            "asset": asset,
            "markets": relevant[:5],
            "total_found": len(relevant),
        }

    except requests.exceptions.Timeout:
        logger.warning(f"[Polymarket] Timeout fetching {asset}")
        return {"asset": asset, "markets": [], "error": "timeout"}

    except requests.exceptions.HTTPError as e:
        logger.error(f"[Polymarket] HTTP error for {asset}: {e}")
        return {"asset": asset, "markets": [], "error": f"HTTP {e.response.status_code}"}

    except Exception as e:
        logger.error(f"[Polymarket] Unexpected error for {asset}: {e}")
        return {"asset": asset, "markets": [], "error": str(e)}


def parse_implied_probability(market: dict) -> float:
    """
    Extract the implied UP probability from a Polymarket market dict.
    Returns a float between 0 and 1, or 0.5 if unavailable.
    """
    try:
        ask = float(market.get("best_ask", 0.5))
        return ask  # On Polymarket, price ≈ probability
    except (TypeError, ValueError):
        return 0.5
