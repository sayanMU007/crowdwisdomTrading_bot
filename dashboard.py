"""
Dashboard — FastAPI web interface for viewing pipeline results.

Usage:
    python dashboard.py
    Then open http://localhost:8000 in your browser.
"""

import os
import json
import glob
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="CrowdWisdomTrading Dashboard")


def load_latest_results() -> dict | None:
    """Load the most recent results JSON from the logs directory."""
    files = sorted(glob.glob("logs/results_*.json"), reverse=True)
    if not files:
        return None
    with open(files[0]) as f:
        return json.load(f)


def load_all_results() -> list[dict]:
    """Load all results JSONs sorted newest-first."""
    files = sorted(glob.glob("logs/results_*.json"), reverse=True)
    results = []
    for f in files[:10]:  # Show last 10 runs
        with open(f) as fh:
            results.append(json.load(fh))
    return results


@app.get("/", response_class=HTMLResponse)
def index():
    data = load_latest_results()
    if not data:
        return "<h2>No results yet. Run <code>python main.py</code> first.</h2>"

    ts = data.get("timestamp", "unknown")
    feedback = data.get("feedback", "No feedback available.")
    assets = data.get("results", [])

    rows = ""
    for r in assets:
        asset = r.get("asset", "?")
        pred = r.get("prediction", {}).get("primary", {})
        risk = r.get("risk", {})
        direction = pred.get("direction", "N/A")
        confidence = pred.get("confidence", 0)
        action = risk.get("action", "N/A")
        arb = r.get("prediction", {}).get("arbitrage_signal", False)

        dir_color = "#2ecc71" if direction == "UP" else "#e74c3c" if direction == "DOWN" else "#95a5a6"
        rows += f"""
        <tr>
            <td><strong>{asset}</strong></td>
            <td style="color:{dir_color};font-weight:bold">{direction}</td>
            <td>{confidence:.1%}</td>
            <td>{'⚡ YES' if arb else 'No'}</td>
            <td>{action}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>CrowdWisdomTrading Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #0f0f1a; color: #e0e0e0; margin: 0; padding: 20px; }}
        h1 {{ color: #7c5cbf; border-bottom: 2px solid #7c5cbf; padding-bottom: 10px; }}
        h2 {{ color: #a88fd4; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
        th {{ background: #1e1e3a; color: #a88fd4; padding: 12px; text-align: left; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #2a2a4a; }}
        tr:hover td {{ background: #1e1e3a; }}
        .feedback {{ background: #1e1e3a; border-left: 4px solid #7c5cbf; padding: 16px; white-space: pre-wrap; border-radius: 4px; }}
        .timestamp {{ color: #888; font-size: 0.85em; }}
        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; background: #2a2a4a; }}
    </style>
</head>
<body>
    <h1>🤖 CrowdWisdomTrading Dashboard</h1>
    <p class="timestamp">Last run: {ts} &nbsp;|&nbsp; Auto-refreshes every 30s</p>

    <h2>Asset Predictions</h2>
    <table>
        <thead>
            <tr>
                <th>Asset</th>
                <th>Direction</th>
                <th>Confidence</th>
                <th>Arbitrage</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>

    <h2>Orchestrator Recommendations</h2>
    <div class="feedback">{feedback}</div>
</body>
</html>"""
    return html


@app.get("/api/results")
def api_results():
    """JSON API endpoint for latest results."""
    return load_latest_results() or {"error": "No results yet"}


@app.get("/api/history")
def api_history():
    """JSON API endpoint for last 10 runs."""
    return load_all_results()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
