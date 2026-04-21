"""
Kalshi Tool — fetches open prediction markets for a crypto asset.
Docs: https://trading-api.kalshi.com/trade-api/v2
"""

import requests
from loguru import logger
from config.settings import KALSHI_API


def get_crypto_predictions(asset: str) -> dict:
    try:
        resp = requests.get(
            f"{KALSHI_API}/markets",
            params={
                "ticker_contains": asset.upper(),
                "status": "open",
                "limit": 10,
            },
            headers={"accept": "application/json"},
            timeout=10,
        )

        # Kalshi requires auth for /markets — fall back to public /events endpoint
        if resp.status_code == 401:
            logger.warning(f"[Kalshi] Auth required — using public event search for {asset}")
            resp2 = requests.get(
                "https://trading-api.kalshi.com/trade-api/v2/events",
                params={"series_ticker": asset.upper(), "limit": 5},
                headers={"accept": "application/json"},
                timeout=10,
            )
            resp2.raise_for_status()
            events = resp2.json().get("events", [])
            logger.info(f"[Kalshi] {asset}: found {len(events)} events (public)")
            return {"asset": asset, "markets": events[:5], "total_found": len(events)}

        resp.raise_for_status()
        markets = resp.json().get("markets", [])
        logger.info(f"[Kalshi] {asset}: found {len(markets)} open markets")
        return {
            "asset": asset,
            "markets": markets[:5],
            "total_found": len(markets),
        }

    except requests.exceptions.Timeout:
        logger.warning(f"[Kalshi] Timeout fetching {asset}")
        return {"asset": asset, "markets": [], "error": "timeout"}

    except requests.exceptions.HTTPError as e:
        logger.error(f"[Kalshi] HTTP error for {asset}: {e}")
        return {"asset": asset, "markets": [], "error": f"HTTP {e.response.status_code}"}

    except Exception as e:
        logger.error(f"[Kalshi] Unexpected error for {asset}: {e}")
        return {"asset": asset, "markets": [], "error": str(e)}


def parse_yes_price(market: dict) -> float:
    """
    Extract the YES price (≈ probability) from a Kalshi market.
    Returns float 0-1, defaults to 0.5.
    """
    try:
        yes_ask = market.get("yes_ask", 50)
        return float(yes_ask) / 100.0  # Kalshi uses cents (0-100)
    except (TypeError, ValueError):
        return 0.5