"""
Agent 3: Prediction Agent
Runs Kronos-style directional prediction on OHLCV data.
Supports both single-timeframe and cross-timeframe arbitrage detection.
"""

from loguru import logger
from models.kronos_wrapper import predict_next_move, predict_multi_timeframe
from config.settings import MIN_CONFIDENCE


def run(asset: str, ohlcv_data: dict) -> dict:
    """
    Predict next price direction for an asset.

    Args:
        asset:       e.g. "BTC"
        ohlcv_data:  dict with keys "5m" and optionally "15m" (lists of OHLCV bars)

    Returns:
        dict with direction, confidence, signal, and optional arbitrage info
    """
    logger.info(f"[PredictionAgent] Running prediction for {asset}")

    bars_5m = ohlcv_data.get("5m", [])
    bars_15m = ohlcv_data.get("15m", [])

    # Run multi-timeframe if 15m data is available
    if bars_15m:
        result = predict_multi_timeframe(bars_5m, bars_15m)
        primary = result["5m"]  # Primary signal from 5-min
    else:
        primary = predict_next_move(bars_5m)
        result = {"5m": primary, "15m": None, "arbitrage_signal": False}

    # Flag low-confidence predictions
    confidence = primary.get("confidence", 0)
    if confidence < MIN_CONFIDENCE:
        logger.warning(
            f"[PredictionAgent] {asset} confidence {confidence:.1%} < threshold {MIN_CONFIDENCE:.1%} — LOW CONFIDENCE"
        )
        primary["low_confidence_warning"] = True
    else:
        primary["low_confidence_warning"] = False

    primary["asset"] = asset
    result["primary"] = primary

    logger.info(
        f"[PredictionAgent] {asset}: {primary.get('direction')} | "
        f"confidence={confidence:.1%} | "
        f"arbitrage={result.get('arbitrage_signal', False)}"
    )

    return result
