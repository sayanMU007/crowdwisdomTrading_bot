"""
Kronos Wrapper — directional prediction model for crypto price movements.
Based on: https://github.com/shiyu-coder/Kronos

This wrapper provides a clean interface. The predict_next_move() function
uses a momentum + volatility signal as a baseline. To integrate the full
Kronos model, replace the signal computation block with your Kronos inference.
"""

import pandas as pd
import numpy as np
from loguru import logger


def _load_dataframe(ohlcv_bars: list) -> pd.DataFrame | None:
    """Convert raw OHLCV list to a clean DataFrame."""
    if not ohlcv_bars:
        return None

    df = pd.DataFrame(ohlcv_bars)

    # Normalize column names — Apify/Binance may return different casings
    df.columns = [c.lower().strip() for c in df.columns]

    # Find close price column
    close_col = next(
        (c for c in df.columns if "close" in c),
        None,
    )
    if close_col is None:
        logger.error("[Kronos] No 'close' column found in OHLCV data")
        return None

    df = df.rename(columns={close_col: "close"})
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["close"])
    return df


def predict_next_move(ohlcv_bars: list, lookback: int = 50) -> dict:
    """
    Predict next candle direction (UP / DOWN) from OHLCV data.

    Uses a normalized momentum signal over the last `lookback` bars.
    High |signal| → higher confidence.

    To use the full Kronos model:
        1. Clone https://github.com/shiyu-coder/Kronos
        2. Install its requirements
        3. Replace the signal computation below with Kronos inference

    Args:
        ohlcv_bars: List of OHLCV dicts (from Apify)
        lookback:   Number of recent bars to use for signal

    Returns:
        dict with direction, confidence, signal, momentum, volatility
    """
    if not ohlcv_bars or len(ohlcv_bars) < 20:
        logger.warning("[Kronos] Not enough bars to make a prediction")
        return {
            "direction": "UNKNOWN",
            "confidence": 0.0,
            "signal": 0.0,
            "error": f"Need at least 20 bars, got {len(ohlcv_bars)}",
        }

    df = _load_dataframe(ohlcv_bars)
    if df is None:
        return {"direction": "UNKNOWN", "confidence": 0.0, "signal": 0.0, "error": "Invalid data"}

    try:
        closes = df["close"].values[-lookback:]

        # === Signal computation (replace this block with Kronos model) ===
        returns = np.diff(closes) / closes[:-1]

        short_momentum = np.mean(returns[-5:])    # 5-bar momentum
        long_momentum = np.mean(returns[-20:])    # 20-bar momentum
        volatility = np.std(returns[-20:])        # 20-bar realized vol

        # Combined signal: short momentum weighted vs long momentum
        combined = 0.7 * short_momentum + 0.3 * long_momentum
        signal = combined / (volatility + 1e-9)   # Sharpe-like normalization
        # === End signal computation ===

        # Map signal to confidence (sigmoid-like, capped at 95%)
        raw_confidence = abs(signal) * 2.0
        confidence = float(0.5 + min(raw_confidence * 0.45, 0.45))
        direction = "UP" if signal > 0 else "DOWN"

        result = {
            "direction": direction,
            "confidence": round(confidence, 4),
            "signal": round(float(signal), 6),
            "short_momentum": round(float(short_momentum), 6),
            "long_momentum": round(float(long_momentum), 6),
            "volatility": round(float(volatility), 6),
            "bars_used": len(closes),
        }

        logger.info(f"[Kronos] Prediction: {direction} | confidence={confidence:.2%} | signal={signal:.4f}")
        return result

    except Exception as e:
        logger.error(f"[Kronos] Prediction failed: {e}")
        return {"direction": "UNKNOWN", "confidence": 0.0, "signal": 0.0, "error": str(e)}


def predict_multi_timeframe(bars_5m: list, bars_15m: list) -> dict:
    """
    Run predictions on both 5-min and 15-min data.
    Used for cross-timeframe arbitrage signal detection.

    Returns:
        dict with "5m" and "15m" prediction dicts, plus an "arbitrage" flag
    """
    pred_5m = predict_next_move(bars_5m, lookback=50)
    pred_15m = predict_next_move(bars_15m, lookback=50)

    # Arbitrage: short-term disagrees with longer-term trend
    arbitrage_detected = (
        pred_5m.get("direction") != pred_15m.get("direction")
        and pred_5m.get("confidence", 0) > 0.6
        and pred_15m.get("confidence", 0) > 0.6
    )

    return {
        "5m": pred_5m,
        "15m": pred_15m,
        "arbitrage_signal": arbitrage_detected,
        "arbitrage_note": (
            f"5m says {pred_5m.get('direction')} but 15m says {pred_15m.get('direction')} — "
            "potential mean-reversion opportunity"
            if arbitrage_detected
            else "No cross-timeframe divergence detected"
        ),
    }
