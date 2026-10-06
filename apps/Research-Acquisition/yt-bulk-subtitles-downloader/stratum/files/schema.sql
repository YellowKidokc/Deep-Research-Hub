-- Stratum Cloud D1 Schema
-- Syncs clipboard, prompts, links, shortcuts across all devices

CREATE TABLE IF NOT EXISTS clips (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  content TEXT NOT NULL,
  source TEXT DEFAULT 'manual',        -- manual | hotkey | ai | bridge
  pinned INTEGER DEFAULT 0,
  tags TEXT DEFAULT '[]',              -- JSON array
  slot INTEGER,                        -- 0-9 for hotkey slots, NULL for history
  device_id TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS prompts (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  name TEXT NOT NULL,
  content TEXT NOT NULL,
  category TEXT DEFAULT 'general',     -- general | rewrite | summarize | expand | custom
  hotkey TEXT,                         -- e.g. "ctrl+shift+1"
  usage_count INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS links (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  category TEXT DEFAULT 'general',
  hotkey TEXT,
  icon TEXT,                           -- emoji or icon name
  usage_count INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS shortcuts (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  trigger_key TEXT NOT NULL,           -- "ctrl+alt+g", "ctrl+space", etc.
  action TEXT NOT NULL,                -- "open_panel" | "rewrite" | "paste_slot" | "run_prompt" | "open_link"
  target TEXT,                         -- panel name, prompt id, link id, slot number
  enabled INTEGER DEFAULT 1,
  device_scope TEXT DEFAULT 'all',     -- all | local_only | cloud_only
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ai_history (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  input_text TEXT NOT NULL,
  output_text TEXT NOT NULL,
  model TEXT DEFAULT 'claude-sonnet-4-6',
  prompt_id TEXT,                      -- which prompt template was used
  tokens_in INTEGER,
  tokens_out INTEGER,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sync_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id TEXT NOT NULL,
  table_name TEXT NOT NULL,
  record_id TEXT NOT NULL,
  action TEXT NOT NULL,                -- insert | update | delete
  synced_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_clips_slot ON clips(slot);
CREATE INDEX IF NOT EXISTS idx_clips_pinned ON clips(pinned);
CREATE INDEX IF NOT EXISTS idx_clips_created ON clips(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category);
CREATE INDEX IF NOT EXISTS idx_shortcuts_trigger ON shortcuts(trigger_key);
CREATE INDEX IF NOT EXISTS idx_sync_device ON sync_log(device_id, synced_at DESC);
