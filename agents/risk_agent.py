"""
Agent 4: Risk Management Agent
Applies the Kelly Criterion to size positions based on prediction confidence
and available market odds from Polymarket/Kalshi.
"""

from loguru import logger
from tools.kelly_tool import kelly_criterion, expected_value
from config.settings import MIN_CONFIDENCE


def _extract_best_payout(market_data: dict) -> float:
    """
    Try to extract the best available win payout from market data.
    Falls back to 0.9 (10% fee assumption) if unavailable.
    """
    # Try Polymarket first
    poly_markets = market_data.get("polymarket", {}).get("markets", [])
    if poly_markets:
        try:
            price = float(poly_markets[0].get("best_ask", 0.5))
            if 0 < price < 1:
                # If you bet on YES at price p, you win (1-p)/p per dollar
                return round((1 - price) / price, 4)
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    # Try Kalshi
    kalshi_markets = market_data.get("kalshi", {}).get("markets", [])
    if kalshi_markets:
        try:
            yes_ask = float(kalshi_markets[0].get("yes_ask", 50)) / 100.0
            if 0 < yes_ask < 1:
                return round((1 - yes_ask) / yes_ask, 4)
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    return 0.9  # Default: assume 90¢ win per $1 bet (conservative)


def run(asset: str, prediction: dict, market_data: dict) -> dict:
    """
    Calculate Kelly position size for a predicted trade.

    Args:
        asset:       e.g. "BTC"
        prediction:  Output from prediction_agent.run() — needs direction + confidence
        market_data: Output from market_search_agent.run() — for odds extraction

    Returns:
        dict with kelly sizing, EV, and a plain-English action string
    """
    logger.info(f"[RiskAgent] Sizing position for {asset}")

    primary = prediction.get("primary", prediction)
    direction = primary.get("direction", "UNKNOWN")
    confidence = primary.get("confidence", 0.0)

    # Skip sizing if direction is unknown or confidence too low
    if direction == "UNKNOWN" or confidence < MIN_CONFIDENCE:
        result = {
            "asset": asset,
            "direction": direction,
            "confidence": confidence,
            "kelly": {"recommendation": "PASS — insufficient confidence"},
            "expected_value": 0.0,
            "action": f"PASS {asset} — confidence {confidence:.1%} below threshold",
        }
        logger.warning(f"[RiskAgent] {asset}: PASS (confidence too low)")
        return result

    win_payout = _extract_best_payout(market_data)
    kelly = kelly_criterion(win_prob=confidence, win_payout=win_payout)
    ev = expected_value(win_prob=confidence, win_payout=win_payout)

    arbitrage = prediction.get("arbitrage_signal", False)
    arb_note = prediction.get("arbitrage_note", "")

    result = {
        "asset": asset,
        "direction": direction,
        "confidence": confidence,
        "win_payout": win_payout,
        "kelly": kelly,
        "expected_value": ev,
        "arbitrage_signal": arbitrage,
        "arbitrage_note": arb_note if arbitrage else None,
        "action": f"{direction} {asset} — {kelly['recommendation']} | EV={ev:+.4f}",
    }

    logger.success(f"[RiskAgent] {asset}: {result['action']}")
    return result
