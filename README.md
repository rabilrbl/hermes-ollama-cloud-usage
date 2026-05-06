# Hermes Plugin: Ollama Cloud Usage

Check your Ollama Cloud Pro / Max subscription usage right inside Hermes Agent.

Since Ollama Cloud does not expose a public usage API (see [ollama/ollama#12532](https://github.com/ollama/ollama/issues/12532)), this plugin scrapes your usage stats from `https://ollama.com/settings` using your authenticated session cookie.

## Install

```bash
hermes plugins install https://github.com/rabilrbl/hermes-ollama-cloud-usage
```

During installation you will be prompted to enter your Ollama Cloud session cookie (`OLLAMA_CLOUD_COOKIE`). The value is saved to `~/.hermes/.env`.

## Getting your cookie

1. Open a browser and log in to [https://ollama.com/settings](https://ollama.com/settings).
2. Open DevTools → **Application** (or **Storage** on Firefox) → **Cookies**.
3. Copy all cookies for `ollama.com` (e.g. `auth=xxx; other=yyy`).
4. Paste the raw cookie string when prompted during install, or set it manually:

```bash
# ~/.hermes/.env
OLLAMA_CLOUD_COOKIE="auth=xxx; other=yyy"
```

Then restart Hermes or run `/reset` to reload.

## Usage

Ask Hermes about your Ollama Cloud usage:

```
Check my Ollama Cloud usage
```

The tool returns:
- Plan tier (Pro / Max)
- Session usage % and reset timer
- Weekly usage % and reset timer
- Simple ASCII progress bars

## Example output

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

## Limitations

- Works for **Pro** and **Max** tiers shown on the Ollama Cloud settings page.
- Requires a valid browser session cookie. If the cookie expires, re-copy it and update `~/.hermes/.env`.
- Scrapes HTML, so the parser may need updates if Ollama changes the dashboard layout.

## License

MIT
