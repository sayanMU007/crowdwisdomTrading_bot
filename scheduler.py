"""
Scheduler — Auto-runs the pipeline every 5 minutes.

Usage:
    python scheduler.py

Press Ctrl+C to stop.
"""

import time
import schedule
from loguru import logger
from dotenv import load_dotenv

load_dotenv()


def job():
    logger.info("⏰ Scheduler triggered — running pipeline...")
    try:
        from main import run_pipeline
        run_pipeline()
    except Exception as e:
        logger.error(f"Scheduled run failed: {e}")


if __name__ == "__main__":
    logger.info("CrowdWisdomTrading Scheduler started — runs every 5 minutes.")
    logger.info("Press Ctrl+C to stop.\n")

    # Run immediately on start, then every 5 minutes
    job()
    schedule.every(5).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(10)
