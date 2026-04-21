"""
CrowdWisdomTrading — Main Pipeline Entry Point

Runs the full multi-agent pipeline:
  1. MarketSearchAgent  — Polymarket + Kalshi predictions
  2. DataFetchAgent     — Apify OHLCV data
  3. PredictionAgent    — Kronos-style directional model
  4. RiskAgent          — Kelly criterion position sizing
  5. Orchestrator       — Hermes feedback loop + final recommendations

Usage:
    python main.py
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

# ── Load environment variables ──────────────────────────────────────────────
load_dotenv()

# ── Logging setup ────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
LOG_FILE = os.getenv("LOG_FILE", "logs/trading.log")

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
)
logger.add(
    LOG_FILE,
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
)

# ── Validate required env vars ───────────────────────────────────────────────
def _check_env():
    missing = []
    if not os.getenv("GROQ_API_KEY"):
        missing.append("GROQ_API_KEY")
    if not os.getenv("APIFY_TOKEN"):
        missing.append("APIFY_TOKEN")
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please copy .env.example to .env and fill in your keys.")
        sys.exit(1)

# ── Agent imports ────────────────────────────────────────────────────────────
from config.settings import ASSETS
from agents import (
    market_search_agent,
    data_fetch_agent,
    prediction_agent,
    risk_agent,
    orchestrator,
)


def run_pipeline() -> list[dict]:
    """
    Run the full CrowdWisdomTrading pipeline for all configured assets.
    Returns the list of per-asset result dicts.
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("  CrowdWisdomTrading Pipeline — START")
    logger.info(f"  Assets: {ASSETS}")
    logger.info(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    all_results = []

    for asset in ASSETS:
        logger.info(f"\n{'─' * 50}")
        logger.info(f"  Processing: {asset}")
        logger.info(f"{'─' * 50}")

        # ── Agent 1: Market Search ───────────────────────────────────────────
        logger.info(f"[1/4] Market search for {asset}...")
        try:
            market_data = market_search_agent.run(asset)
        except Exception as e:
            logger.error(f"MarketSearchAgent failed for {asset}: {e}")
            market_data = {"asset": asset, "polymarket": {}, "kalshi": {}, "summary": "Error", "error": str(e)}

        # ── Agent 2: Data Fetch ──────────────────────────────────────────────
        logger.info(f"[2/4] Fetching OHLCV data for {asset}...")
        try:
            ohlcv_data = data_fetch_agent.run(asset, multi_timeframe=True)
        except Exception as e:
            logger.error(f"DataFetchAgent failed for {asset}: {e}")
            ohlcv_data = {"5m": [], "15m": []}

        # ── Agent 3: Prediction ──────────────────────────────────────────────
        logger.info(f"[3/4] Running prediction for {asset}...")
        try:
            prediction = prediction_agent.run(asset, ohlcv_data)
        except Exception as e:
            logger.error(f"PredictionAgent failed for {asset}: {e}")
            prediction = {"primary": {"direction": "UNKNOWN", "confidence": 0.0}, "arbitrage_signal": False}

        # ── Agent 4: Risk Management ─────────────────────────────────────────
        logger.info(f"[4/4] Sizing position for {asset}...")
        try:
            risk = risk_agent.run(asset, prediction, market_data)
        except Exception as e:
            logger.error(f"RiskAgent failed for {asset}: {e}")
            risk = {"asset": asset, "action": "PASS — error in risk calculation", "error": str(e)}

        # ── Collect results ──────────────────────────────────────────────────
        asset_result = {
            "asset": asset,
            "timestamp": datetime.now().isoformat(),
            "market_summary": market_data,
            "ohlcv_bars_fetched": {k: len(v) for k, v in ohlcv_data.items()},
            "prediction": prediction,
            "risk": risk,
        }
        all_results.append(asset_result)

        # ── Per-asset summary log ────────────────────────────────────────────
        primary = prediction.get("primary", {})
        logger.info(
            f"\n  ✓ {asset} Summary:\n"
            f"    Direction  : {primary.get('direction', 'N/A')}\n"
            f"    Confidence : {primary.get('confidence', 0):.1%}\n"
            f"    Action     : {risk.get('action', 'N/A')}\n"
            f"    Arbitrage  : {prediction.get('arbitrage_signal', False)}"
        )

    # ── Agent 5: Orchestrator Feedback Loop ──────────────────────────────────
    logger.info(f"\n{'=' * 60}")
    logger.info("  Orchestrator — Hermes Feedback Loop")
    logger.info(f"{'=' * 60}")

    try:
        feedback = orchestrator.run_feedback_loop(all_results)
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}")
        feedback = "Orchestrator error — check logs for details."

    # ── Print final recommendations ───────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  FINAL RECOMMENDATIONS")
    print("=" * 60)
    print(feedback)
    print("=" * 60)

    # ── Save results to JSON ──────────────────────────────────────────────────
    output_path = f"logs/results_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w") as f:
        json.dump(
            {"timestamp": start_time.isoformat(), "results": all_results, "feedback": feedback},
            f,
            indent=2,
            default=str,
        )

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.success(f"\n  Pipeline COMPLETE in {elapsed:.1f}s — results saved to {output_path}")

    return all_results


if __name__ == "__main__":
    _check_env()
    run_pipeline()
