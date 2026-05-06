---
name: ollama-cloud-usage
description: "Check your Ollama Cloud Pro/Max subscription usage — session and weekly limits, plan tier, and reset timers."
version: 2.0.0
author: Rabil
license: MIT
metadata:
  hermes:
    tags: [ollama, cloud, usage, monitor]
    related_skills: []
---

# Ollama Cloud Usage

Check your Ollama Cloud Pro/Max subscription usage directly from Hermes.

Since Ollama Cloud has no public usage API (see [ollama/ollama#12532](https://github.com/ollama/ollama/issues/12532)), this skill scrapes the dashboard at `https://ollama.com/settings` using your authenticated session cookie.

## When to Use

- User asks about their Ollama Cloud usage, limits, or remaining quota
- User wants to know their plan tier (Pro/Max) or when their session/weekly usage resets
- User asks "how much Ollama Cloud do I have left?"

## Setup

Set `OLLAMA_CLOUD_COOKIE` in `~/.hermes/.env`:

```bash
# ~/.hermes/.env
OLLAMA_CLOUD_COOKIE="auth=xxx; other=yyy"
```

### Getting your cookie

1. Open a browser and log in to https://ollama.com/settings
2. Open DevTools → **Application** (or **Storage** on Firefox) → **Cookies**
3. Copy all cookies for `ollama.com` as a single string (e.g. `auth=xxx; other=yyy`)
4. Paste into `~/.hermes/.env` as shown above
5. Restart Hermes or run `/reset` if mid-session

If the cookie expires, repeat steps 2–4.

## Usage

Run the script via terminal:

```bash
python3 ~/.hermes/skills/automation/ollama-cloud-usage/scripts/ollama_cloud_usage.py
```

Or use `execute_code` / `terminal` to invoke it. The script reads `OLLAMA_CLOUD_COOKIE` from the environment.

## Output

The script returns JSON:

```json
{
  "plan": "Pro",
  "session_percent": 0.1,
  "session_resets_in": "3 hours",
  "weekly_percent": 13.3,
  "weekly_resets_in": "4 days",
  "session_bar": "█░░░░░░░░░░░░░░░░░░░",
  "weekly_bar": "███░░░░░░░░░░░░░░░░░"
}
```

Present results to the user in a readable format, e.g.:

- **Plan:** Pro
- **Session:** 0.1% used, resets in 3 hours
- **Weekly:** 13.3% used, resets in 4 days

## Common Pitfalls

1. **Cookie expires.** The session cookie is short-lived. If the script returns an error about parsing, re-extract the cookie and update `.env`.
2. **No usage data found.** This means either the cookie is invalid/expired, or Ollama changed their dashboard HTML. Check the cookie first, then open an issue on the skill repo.
3. **Don't hardcode the cookie.** Always use the `OLLAMA_CLOUD_COOKIE` env var so it can be updated in one place.