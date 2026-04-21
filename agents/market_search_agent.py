"""
Agent 1: Market Search Agent
Searches Polymarket and Kalshi for 5-min crypto prediction markets,
then uses Hermes to summarize the implied probabilities.
"""

import os
from loguru import logger

from tools.polymarket_tool import get_crypto_predictions as poly_pred
from tools.kalshi_tool import get_crypto_predictions as kalshi_pred


def run(asset: str) -> dict:
    """
    Search Polymarket + Kalshi for prediction markets on an asset.

    Args:
        asset: e.g. "BTC" or "ETH"

    Returns:
        dict with polymarket, kalshi, and summary keys
    """
    logger.info(f"[MarketSearchAgent] Searching predictions for {asset}")

    poly = poly_pred(asset)
    kalshi = kalshi_pred(asset)

    # Build a text summary without requiring Hermes (fallback-safe)
    poly_count = len(poly.get("markets", []))
    kalshi_count = len(kalshi.get("markets", []))

    # Try to pull implied probability from first Polymarket market
    implied_prob = None
    if poly.get("markets"):
        try:
            implied_prob = float(poly["markets"][0].get("best_ask", 0.5))
        except Exception:
            implied_prob = 0.5

    summary_text = (
        f"{asset} — Found {poly_count} Polymarket markets and {kalshi_count} Kalshi markets. "
    )
    if implied_prob is not None:
        direction = "UP" if implied_prob > 0.5 else "DOWN"
        summary_text += (
            f"Polymarket best implied probability: {implied_prob:.1%} → market leans {direction}."
        )
    else:
        summary_text += "No clear implied probability available."

    # Optionally enhance summary with Hermes if available
    try:
        from run_agent import AIAgent

        agent = AIAgent(
            model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-4-maverick:free"),
            quiet_mode=True,
            skip_memory=True,
            skip_context_files=True,
        )
        hermes_summary = agent.chat(
            f"Summarize these prediction market results for {asset} in 2-3 sentences. "
            f"Focus on: implied up/down probability, best odds, and any notable signals.\n\n"
            f"Polymarket data: {poly}\n\nKalshi data: {kalshi}"
        )
        summary_text = hermes_summary
        logger.success(f"[MarketSearchAgent] Hermes summary generated for {asset}")
    except ImportError:
        logger.warning("[MarketSearchAgent] Hermes not installed, using basic summary")
    except Exception as e:
        logger.warning(f"[MarketSearchAgent] Hermes summary failed: {e}, using basic summary")

    result = {
        "asset": asset,
        "polymarket": poly,
        "kalshi": kalshi,
        "implied_probability": implied_prob,
        "summary": summary_text,
    }

    logger.success(f"[MarketSearchAgent] Done for {asset}: {poly_count} poly + {kalshi_count} kalshi markets")
    return result
