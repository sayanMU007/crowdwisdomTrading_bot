"""
Agent 5: Orchestrator — LLM Feedback Loop
Uses Groq API (free, no credit card) for LLM recommendations.
Sign up at https://console.groq.com
"""

import os
import requests
from loguru import logger


SYSTEM_PROMPT = """You are a quantitative crypto trading analyst reviewing a prediction pipeline output.

For each asset in the results:
1. Give a clear BUY / SELL / PASS recommendation with one-line rationale
2. State the suggested position size as % of bankroll (use the Kelly fraction provided)
3. Flag any cross-timeframe arbitrage opportunities
4. Warn if confidence is below 60% or expected value is negative

Be concise, direct, and structured. Use this format:

ASSET: [name]
RECOMMENDATION: [BUY/SELL/PASS]
POSITION SIZE: [X% of bankroll]
RATIONALE: [one line]
WARNINGS: [any flags, or "None"]
---

End with a 2-sentence overall market summary."""


def _format_results_for_prompt(results: list[dict]) -> str:
    lines = []
    for r in results:
        asset = r.get("asset", "?")
        pred = r.get("prediction", {}).get("primary", {})
        risk = r.get("risk", {})
        market = r.get("market_summary", {})

        lines.append(f"=== {asset} ===")
        lines.append(f"Direction: {pred.get('direction', 'N/A')}")
        lines.append(f"Confidence: {pred.get('confidence', 0):.1%}")
        lines.append(f"Signal: {pred.get('signal', 'N/A')}")
        lines.append(f"Kelly fraction: {risk.get('kelly', {}).get('recommended_fraction', 0):.1%}")
        lines.append(f"Expected value: {risk.get('expected_value', 0):+.4f}")
        lines.append(f"Arbitrage signal: {r.get('prediction', {}).get('arbitrage_signal', False)}")
        if r.get("prediction", {}).get("arbitrage_signal"):
            lines.append(f"Arbitrage note: {r.get('prediction', {}).get('arbitrage_note', '')}")
        lines.append(f"Market summary: {market.get('summary', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


def _call_groq(prompt_body: str) -> str:
    """Call Groq API — completely free, no credit card needed."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in .env — get one free at https://console.groq.com")

    models = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-groq-8b-8192-tool-use-preview",
    "meta-llama/llama-4-scout-17b-16e-instruct",
   ]
    last_error = None
    for model in models:
        try:
            logger.info(f"[Orchestrator] Trying Groq model: {model}")
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"{SYSTEM_PROMPT}\n\nHere are the pipeline results:\n\n{prompt_body}",
                        },
                    ],
                    "max_tokens": 500,
                    "temperature": 0.3,
                },
                timeout=30,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            logger.success(f"[Orchestrator] Groq success with model: {model}")
            return content

        except requests.exceptions.HTTPError as e:
            logger.warning(
                f"[Orchestrator] Groq model {model} failed: "
                f"{e.response.status_code} | {e.response.text} — trying next"
            )
            last_error = e
            continue
        except Exception as e:
            logger.warning(f"[Orchestrator] Groq model {model} error: {e} — trying next")
            last_error = e
            continue

    raise Exception(f"All Groq models failed. Last error: {last_error}")


def run_feedback_loop(results: list[dict]) -> str:
    logger.info("[Orchestrator] Starting feedback loop via Groq (free)")

    prompt_body = _format_results_for_prompt(results)

    try:
        feedback = _call_groq(prompt_body)
        logger.success("[Orchestrator] Groq feedback complete")
        return feedback

    except ValueError as e:
        logger.error(f"[Orchestrator] Config error: {e} — using fallback")
    except Exception as e:
        logger.error(f"[Orchestrator] Groq failed: {e} — using fallback")

    return _fallback_summary(results)


def _fallback_summary(results: list[dict]) -> str:
    lines = ["=== TRADE RECOMMENDATIONS (rule-based fallback) ===", ""]

    for r in results:
        asset = r.get("asset", "?")
        risk = r.get("risk", {})
        pred = r.get("prediction", {}).get("primary", {})

        direction = pred.get("direction", "UNKNOWN")
        confidence = pred.get("confidence", 0)
        kelly_pct = risk.get("kelly", {}).get("recommended_pct", "0%")
        ev = risk.get("expected_value", 0)

        rec = "PASS" if direction == "UNKNOWN" or confidence < 0.55 else direction
        lines.append(f"ASSET: {asset}")
        lines.append(f"RECOMMENDATION: {rec}")
        lines.append(f"POSITION SIZE: {kelly_pct}")
        lines.append(f"RATIONALE: confidence={confidence:.1%}, EV={ev:+.4f}")
        lines.append(f"WARNINGS: {'Low confidence' if confidence < 0.6 else 'None'}")
        lines.append("---")

    return "\n".join(lines)