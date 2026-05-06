#!/usr/bin/env python3
"""Check Ollama Cloud subscription usage by scraping the settings page."""

import json
import os
import re
import sys
import urllib.request


def _parse_duration(raw: str) -> str:
    """Clean up human-readable duration text."""
    return raw.strip().replace("\n", " ").replace("  ", " ")


def _make_progress_bar(percent: float, width: int = 20) -> str:
    filled = int(round(percent / 100.0 * width))
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def _fetch_usage(cookie: str) -> dict:
    req = urllib.request.Request(
        "https://ollama.com/settings",
        headers={
            "Cookie": cookie,
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    # Plan tier badge (e.g. Pro, Max)
    plan = "Unknown"
    plan_match = re.search(
        r'<span[^>]*class="[^"]*(?:inline-flex|rounded|badge)[^"]*"[^>]*>(Pro|Max)</span>',
        html,
        re.IGNORECASE,
    )
    if not plan_match:
        plan_match = re.search(
            r'class="[^"]*(?:inline-flex|rounded)[^"]*"[^>]*>\s*(Pro|Max)\s*</span>',
            html,
            re.IGNORECASE,
        )
    if plan_match:
        plan = plan_match.group(1).strip()

    result = {
        "plan": plan,
        "session": {},
        "weekly": {},
    }

    # Session usage
    session_label_match = re.search(
        r'<div[^>]*>\s*Session usage\s*</div>\s*<div[^>]*>\s*([\d.]+%)\s*used\s*</div>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if not session_label_match:
        session_near = re.search(
            r'Session usage\s*</div>\s*<div[^>]*>\s*([\d.]+%)\s*used',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if session_near:
            session_label_match = session_near

    if session_label_match:
        pct = float(session_label_match.group(1).replace("%", ""))
        result["session"]["percent"] = pct

        reset_match = re.search(
            r'Session usage.*?Resets?\s+in\s+([^<]+)',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if reset_match:
            result["session"]["resets_in"] = _parse_duration(reset_match.group(1))

    # Weekly usage
    weekly_label_match = re.search(
        r'<div[^>]*>\s*Weekly usage\s*</div>\s*<div[^>]*>\s*([\d.]+%)\s*used\s*</div>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if not weekly_label_match:
        weekly_near = re.search(
            r'Weekly usage\s*</div>\s*<div[^>]*>\s*([\d.]+%)\s*used',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if weekly_near:
            weekly_label_match = weekly_near

    if weekly_label_match:
        pct = float(weekly_label_match.group(1).replace("%", ""))
        result["weekly"]["percent"] = pct

        reset_match = re.search(
            r'Weekly usage.*?Resets?\s+in\s+([^<]+)',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if reset_match:
            result["weekly"]["resets_in"] = _parse_duration(reset_match.group(1))

    # Fallback: generic percentage search if structured parsing failed
    if not result["session"] or not result["weekly"]:
        all_percents = re.findall(r"([\d.]+%)\s*used", html, re.IGNORECASE)
        all_resets = re.findall(r"Resets?\s+in\s+([^<\n]+)", html, re.IGNORECASE)
        if len(all_percents) >= 2 and not result["session"]:
            result["session"]["percent"] = float(all_percents[0].replace("%", ""))
            if len(all_resets) >= 1:
                result["session"]["resets_in"] = _parse_duration(all_resets[0])
        if len(all_percents) >= 2 and not result["weekly"]:
            result["weekly"]["percent"] = float(all_percents[1].replace("%", ""))
            if len(all_resets) >= 2:
                result["weekly"]["resets_in"] = _parse_duration(all_resets[1])

    if not result["session"] and not result["weekly"]:
        raise RuntimeError(
            "Could not parse usage data from Ollama Cloud dashboard. "
            "The page layout may have changed, or the cookie may be invalid/expired."
        )

    return result


def _load_cookie_from_env_file() -> str:
    """Read OLLAMA_CLOUD_COOKIE from ~/.hermes/.env as a fallback."""
    env_path = os.path.expanduser("~/.hermes/.env")
    if not os.path.isfile(env_path):
        return ""
    with open(env_path) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("OLLAMA_CLOUD_COOKIE="):
                val = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                return val
    return ""


def main():
    cookie = os.getenv("OLLAMA_CLOUD_COOKIE", "").strip()
    if not cookie:
        cookie = _load_cookie_from_env_file()
    if not cookie:
        print(json.dumps({"error": "OLLAMA_CLOUD_COOKIE not set in env or ~/.hermes/.env"}))
        sys.exit(1)

    try:
        data = _fetch_usage(cookie)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    session_pct = data.get("session", {}).get("percent", 0.0)
    session_reset = data.get("session", {}).get("resets_in", "?")
    weekly_pct = data.get("weekly", {}).get("percent", 0.0)
    weekly_reset = data.get("weekly", {}).get("resets_in", "?")

    print(json.dumps({
        "plan": data.get("plan", "Unknown"),
        "session_percent": session_pct,
        "session_resets_in": session_reset,
        "weekly_percent": weekly_pct,
        "weekly_resets_in": weekly_reset,
        "session_bar": _make_progress_bar(session_pct),
        "weekly_bar": _make_progress_bar(weekly_pct),
    }, indent=2))


if __name__ == "__main__":
    main()