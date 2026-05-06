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

## Prerequisites

Requires the `OLLAMA_CLOUD_COOKIE` environment variable in your Hermes environment config.

### Getting your cookie

1. Open a browser and log in to https://ollama.com/settings
2. Open DevTools → **Application** (or **Storage** on Firefox) → **Cookies**
3. Copy all cookies for `ollama.com` as a single string (e.g. `auth=xxx; other=yyy`)
4. Add to your Hermes env config file (located in your Hermes home directory, under the filename `.env`):
   ```
   OLLAMA_CLOUD_COOKIE="auth=xxx; other=yyy"
   ```
5. Restart Hermes or run `/reset` if mid-session

If the cookie expires, repeat steps 2–4.

## How to Check Usage

Use `execute_code` with the following Python snippet. It uses only stdlib (no pip installs needed). Reads the cookie from `~/.hermes/.env` if not in the environment:

```python
import os, json, re, urllib.request

cookie = os.getenv("OLLAMA_CLOUD_COOKIE", "").strip()
if not cookie:
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip().startswith("OLLAMA_CLOUD_COOKIE="):
                    cookie = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                    break
if not cookie:
    print(json.dumps({"error": "OLLAMA_CLOUD_COOKIE not set in env or ~/.hermes/.env"}))
    raise SystemExit(1)

def parse_duration(raw):
    return raw.strip().replace("\n", " ").replace("  ", " ")

def progress_bar(pct, w=20):
    f = max(0, min(w, int(round(pct / 100.0 * w))))
    return chr(9608)*f + chr(9617)*(w-f)

req = urllib.request.Request("https://ollama.com/settings", headers={
    "Cookie": cookie,
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})
with urllib.request.urlopen(req, timeout=30) as resp:
    html = resp.read().decode("utf-8", errors="replace")

plan = "Unknown"
pm = re.search(r'<span[^>]*class="[^"]*(?:inline-flex|rounded|badge)[^"]*"[^>]*>(Pro|Max)</span>', html, re.I)
if not pm:
    pm = re.search(r'class="[^"]*(?:inline-flex|rounded)[^"]*"[^>]*>\s*(Pro|Max)\s*</span>', html, re.I)
if pm:
    plan = pm.group(1).strip()

session, weekly = {}, {}
# Session usage
sm = re.search(r'Session usage\s*</div>\s*<div[^>]*>\s*([\d.]+%)\s*used', html, re.I|re.S)
if not sm:
    sm = re.search(r'<div[^>]*>\s*Session usage\s*</div>\s*<div[^>]*>\s*([\d.]+%)\s*used', html, re.I|re.S)
if sm:
    session["percent"] = float(sm.group(1).replace("%",""))
    rm = re.search(r'Session usage.*?Resets?\s+in\s+([^<]+)', html, re.I|re.S)
    if rm: session["resets_in"] = parse_duration(rm.group(1))

# Weekly usage
wm = re.search(r'Weekly usage\s*</div>\s*<div[^>]*>\s*([\d.]+%)\s*used', html, re.I|re.S)
if not wm:
    wm = re.search(r'<div[^>]*>\s*Weekly usage\s*</div>\s*<div[^>]*>\s*([\d.]+%)\s*used', html, re.I|re.S)
if wm:
    weekly["percent"] = float(wm.group(1).replace("%",""))
    rm = re.search(r'Weekly usage.*?Resets?\s+in\s+([^<]+)', html, re.I|re.S)
    if rm: weekly["resets_in"] = parse_duration(rm.group(1))

# Fallback
if not session or not weekly:
    ap = re.findall(r'([\d.]+%)\s*used', html, re.I)
    ar = re.findall(r'Resets?\s+in\s+([^<\n]+)', html, re.I)
    if len(ap) >= 2 and not session:
        session["percent"] = float(ap[0].replace("%",""))
        if ar: session["resets_in"] = parse_duration(ar[0])
    if len(ap) >= 2 and not weekly:
        weekly["percent"] = float(ap[1].replace("%",""))
        if len(ar) >= 2: weekly["resets_in"] = parse_duration(ar[1])

if not session and not weekly:
    print(json.dumps({"error": "Could not parse usage data. Cookie may be invalid/expired or page layout changed."}))
    raise SystemExit(1)

sp = session.get("percent", 0.0)
wp = weekly.get("percent", 0.0)
print(json.dumps({
    "plan": plan,
    "session_percent": sp,
    "session_resets_in": session.get("resets_in", "?"),
    "weekly_percent": wp,
    "weekly_resets_in": weekly.get("resets_in", "?"),
    "session_bar": progress_bar(sp),
    "weekly_bar": progress_bar(wp),
}, indent=2))
```

## Presenting Results

Format the JSON output for the user in a readable way, e.g.:

- **Plan:** Pro
- **Session:** 0.1% used, resets in 3 hours ▏█░░░░░░░░░░░░░░░░░░░
- **Weekly:** 13.3% used, resets in 4 days ▏███░░░░░░░░░░░░░░░░░

## Common Pitfalls

1. **Cookie expires.** Session cookies are short-lived. If parsing fails, re-extract the cookie and update the env var.
2. **No usage data found.** Either the cookie is invalid/expired, or Ollama changed their dashboard HTML. Check the cookie first.
3. **Cookie not in environment.** The script falls back to reading `~/.hermes/.env` directly, so it works in `execute_code` even if the env var isn't exported to the subprocess.