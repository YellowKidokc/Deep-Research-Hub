# Stratum Cloud — Architecture & Deployment

## Architecture

```
┌─────────────────────────────────────────────┐
│  Stratum PWA (React)                        │
│  Cloudflare Pages — installable anywhere    │
│                                             │
│  ┌──────┐ ┌──────┐ ┌────┐ ┌──┐ ┌────────┐ │
│  │Clips │ │Prompt│ │Link│ │AI│ │Settings│ │
│  └──┬───┘ └──┬───┘ └──┬─┘ └┬─┘ └────────┘ │
│     │        │        │    │               │
└─────┼────────┼────────┼────┼───────────────┘
      │        │        │    │
      ▼        ▼        ▼    ▼
┌─────────────────────────────────────────────┐
│  Stratum Worker (Cloudflare Workers)        │
│  REST API + Claude AI Proxy                 │
│  API key stays server-side                  │
│                                             │
│  ┌──────────────┐  ┌────────────────────┐  │
│  │  D1 Database  │  │  Claude API Proxy  │  │
│  │  clips        │  │  /api/ai           │  │
│  │  prompts      │  │  key never exposed │  │
│  │  links        │  └────────────────────┘  │
│  │  shortcuts    │                          │
│  │  ai_history   │                          │
│  └──────────────┘                           │
└─────────────────────────────────────────────┘

      ▲ (auto-detected WebSocket, optional)
      │
┌─────┴───────────────────────────────────────┐
│  Local Bridge (Windows only)                │
│  bridge.py — ws://localhost:9877            │
│                                             │
│  ┌─────────────────┐  ┌──────────────────┐ │
│  │  Clipboard R/W   │  │  AHK Execution   │ │
│  │  pyperclip       │  │  hotkeys, macros │ │
│  └─────────────────┘  └──────────────────┘ │
│                                             │
│  Bridge not found? PWA works fine —         │
│  shortcuts just copy to clipboard           │
└─────────────────────────────────────────────┘
```

## Deployment Steps

### 1. Create D1 Database

```bash
cd worker/
wrangler d1 create stratum
# Copy the database_id into wrangler.toml
```

### 2. Initialize Schema

```bash
wrangler d1 execute stratum --file=schema.sql
```

### 3. Set Secrets

```bash
wrangler secret put CLAUDE_API_KEY
# Paste your Anthropic API key

wrangler secret put STRATUM_AUTH_TOKEN
# Pick a strong token, e.g.: stratum-cloud-2026-<random>
```

### 4. Deploy Worker

```bash
wrangler deploy
# Note the URL — update it in the React app config
```

### 5. Deploy React PWA to Pages

```bash
cd app/
npm install
npm run build
wrangler pages deploy dist --project-name=stratum
# Or connect to GitHub for auto-deploy
```

### 6. Custom Domain (optional)

In Cloudflare dashboard:
- Worker route: `stratum-api.theophysics.pro/*`
- Pages custom domain: `stratum.theophysics.pro`

### 7. Install as PWA

Open `stratum.theophysics.pro` in Chrome/Edge → "Install app"
Works on Windows, Mac, Android, iOS.

### 8. Local Bridge (Windows only)

```bash
cd bridge/
pip install websockets pyperclip
pythonw bridge.py
# Or add to Windows startup
```

## Sync Flow

1. You add a prompt on your phone → D1 stores it
2. Your desktop PWA refreshes → sees new prompt
3. You hit Ctrl+Alt+P → AHK opens the prompt panel
4. The prompt is right there, synced from your phone

## What Codex Handles

- Migrating existing Stratum content (prompts, links, hotstrings) into the D1 schema
- Wiring the AHK layer to call bridge.py instead of the old FastAPI server
- Any existing action scripts (clean_dictation, rewrite, etc.) → bridge actions
- GitHub repo setup + CI/CD to Cloudflare Pages

## What This Replaces

- pywebview → React PWA (universal, installable)
- FastAPI on port 3456 → Cloudflare Worker (cloud-synced)
- Local-only storage → D1 (everywhere)
- API key in env var → Cloudflare secret (never exposed)
