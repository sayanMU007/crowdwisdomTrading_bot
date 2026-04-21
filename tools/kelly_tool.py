"""
Kelly Criterion Tool — calculates optimal position sizing.
Reference: https://mintlify.wiki/joicodev/polymarket-bot/risk/kelly-criterion
"""

from loguru import logger
from config.settings import HALF_KELLY, MAX_POSITION_PCT


def kelly_criterion(
    win_prob: float,
    win_payout: float,
    loss_payout: float = 1.0,
) -> dict:
    """
    Calculate Kelly optimal bet fraction.

    Formula: f* = (p * b - q) / b
        where p = win probability
              q = 1 - p (loss probability)
              b = net payout per unit risked on a win

    Args:
        win_prob:    Probability of winning (0.0 to 1.0)
        win_payout:  Net profit per $1 bet on a win (e.g. 0.9 for 90¢ gain)
        loss_payout: Fraction of bet lost on a loss (default 1.0 = full bet)

    Returns:
        dict with kelly_fraction, half_kelly_fraction, recommendation
    """
    if not (0 < win_prob < 1):
        logger.warning(f"[Kelly] Invalid win_prob={win_prob}, returning 0")
        return {
            "kelly_fraction": 0.0,
            "half_kelly_fraction": 0.0,
            "recommended_fraction": 0.0,
            "recommendation": "PASS — invalid probability",
            "win_probability": win_prob,
        }

    loss_prob = 1.0 - win_prob
    kelly = (win_prob * win_payout - loss_prob * loss_payout) / win_payout
    kelly = max(0.0, kelly)  # Never go negative

    # Apply half-Kelly for risk management
    recommended = (kelly / 2.0) if HALF_KELLY else kelly

    # Hard cap at MAX_POSITION_PCT
    recommended = min(recommended, MAX_POSITION_PCT)

    result = {
        "win_probability": round(win_prob, 4),
        "kelly_fraction": round(kelly, 4),
        "half_kelly_fraction": round(kelly / 2.0, 4),
        "recommended_fraction": round(recommended, 4),
        "recommended_pct": f"{round(recommended * 100, 2)}%",
        "recommendation": (
            "PASS — negative edge"
            if kelly == 0
            else f"Bet {round(recommended * 100, 2)}% of bankroll"
        ),
    }

    logger.info(f"[Kelly] {result}")
    return result


def expected_value(win_prob: float, win_payout: float, loss_payout: float = 1.0) -> float:
    """
    Calculate expected value of a bet.
    Positive EV = profitable edge.
    """
    ev = win_prob * win_payout - (1 - win_prob) * loss_payout
    return round(ev, 6)
