import { useState, useEffect, useCallback, useRef } from "react";

// ── Config ──
const DEFAULT_API = "https://stratum-api.theophysics.pro"; // Change after deploy
const PANELS = ["clipboard", "prompts", "links", "ai", "settings"];

// ── Storage hook (persists to localStorage-like via React state for demo) ──
function useApiClient(baseUrl, token) {
  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };

  const get = useCallback(
    async (path) => {
      try {
        const res = await fetch(`${baseUrl}${path}`, { headers });
        if (!res.ok) throw new Error(`${res.status}`);
        return await res.json();
      } catch (e) {
        console.error("API GET error:", e);
        return null;
      }
    },
    [baseUrl, token]
  );

  const post = useCallback(
    async (path, body) => {
      try {
        const res = await fetch(`${baseUrl}${path}`, {
          method: "POST",
          headers,
          body: JSON.stringify(body),
        });
        return await res.json();
      } catch (e) {
        console.error("API POST error:", e);
        return null;
      }
    },
    [baseUrl, token]
  );

  const del = useCallback(
    async (path) => {
      try {
        const res = await fetch(`${baseUrl}${path}`, {
          method: "DELETE",
          headers,
        });
        return await res.json();
      } catch (e) {
        console.error("API DELETE error:", e);
        return null;
      }
    },
    [baseUrl, token]
  );

  return { get, post, del };
}

// ── Bridge hook: detects local AHK bridge ──
function useBridge() {
  const [connected, setConnected] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    function tryConnect() {
      try {
        const socket = new WebSocket("ws://localhost:9877");
        socket.onopen = () => {
          setConnected(true);
          ws.current = socket;
        };
        socket.onclose = () => {
          setConnected(false);
          ws.current = null;
          setTimeout(tryConnect, 5000);
        };
        socket.onerror = () => {
          setConnected(false);
          setTimeout(tryConnect, 10000);
        };
      } catch {
        setTimeout(tryConnect, 10000);
      }
    }
    tryConnect();
    return () => ws.current?.close();
  }, []);

  const send = useCallback(
    (action, payload) => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({ action, ...payload }));
        return true;
      }
      return false;
    },
    []
  );

  return { connected, send };
}

// ── Clipboard Panel ──
function ClipboardPanel({ api, bridge }) {
  const [clips, setClips] = useState([]);
  const [newClip, setNewClip] = useState("");
  const [slots, setSlots] = useState(Array(10).fill(""));
  const [loading, setLoading] = useState(false);

  // Demo data when no API
  useEffect(() => {
    setClips([
      { id: "demo1", content: "Sample clipboard entry — connect your Worker to see real data", pinned: true, source: "manual", created_at: new Date().toISOString() },
      { id: "demo2", content: "χ = ∭(G·M·E·S·T·K·R·Q·F·C)dxdydt", pinned: false, source: "ai", created_at: new Date().toISOString() },
      { id: "demo3", content: "https://faiththruphysics.com", pinned: false, source: "manual", created_at: new Date().toISOString() },
    ]);
  }, []);

  const addClip = () => {
    if (!newClip.trim()) return;
    const clip = {
      id: Date.now().toString(16),
      content: newClip,
      pinned: false,
      source: "manual",
      created_at: new Date().toISOString(),
    };
    setClips((prev) => [clip, ...prev]);
    setNewClip("");
    // api.post('/api/clips', { content: newClip }) when connected
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      // If bridge is connected, it can also push to AHK
      bridge.send?.("clipboard_set", { text });
    } catch {
      // Fallback
    }
  };

  const togglePin = (id) => {
    setClips((prev) =>
      prev.map((c) => (c.id === id ? { ...c, pinned: !c.pinned } : c))
    );
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, height: "100%" }}>
      {/* Input */}
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={newClip}
          onChange={(e) => setNewClip(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addClip()}
          placeholder="Add to clipboard..."
          style={inputStyle}
        />
        <button onClick={addClip} style={btnPrimary}>
          +
        </button>
      </div>

      {/* Hotkey Slots */}
      <div>
        <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 6, fontFamily: "monospace" }}>
          HOTKEY SLOTS (Ctrl+Shift+0-9 save · Ctrl+Alt+0-9 paste)
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 4 }}>
          {slots.map((s, i) => (
            <div
              key={i}
              onClick={() => s && copyToClipboard(s)}
              style={{
                padding: "6px 8px",
                background: s ? "var(--accent-dim)" : "var(--surface-2)",
                borderRadius: 4,
                fontSize: 11,
                fontFamily: "monospace",
                cursor: s ? "pointer" : "default",
                overflow: "hidden",
                whiteSpace: "nowrap",
                textOverflow: "ellipsis",
                color: s ? "var(--text-primary)" : "var(--text-muted)",
                border: "1px solid var(--border)",
              }}
            >
              <span style={{ fontWeight: 700, marginRight: 4 }}>{i}</span>
              {s || "empty"}
            </div>
          ))}
        </div>
      </div>

      {/* History */}
      <div style={{ flex: 1, overflowY: "auto" }}>
        {[...clips]
          .sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0))
          .map((clip) => (
            <div
              key={clip.id}
              style={{
                padding: "10px 12px",
                marginBottom: 6,
                background: clip.pinned ? "var(--accent-dim)" : "var(--surface-2)",
                borderRadius: 6,
                borderLeft: `3px solid ${clip.pinned ? "var(--accent)" : "transparent"}`,
                cursor: "pointer",
                transition: "all 0.15s",
              }}
              onClick={() => copyToClipboard(clip.content)}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                <div
                  style={{
                    fontSize: 13,
                    lineHeight: 1.4,
                    color: "var(--text-primary)",
                    flex: 1,
                    wordBreak: "break-word",
                    whiteSpace: "pre-wrap",
                    maxHeight: 80,
                    overflow: "hidden",
                  }}
                >
                  {clip.content}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    togglePin(clip.id);
                  }}
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    fontSize: 14,
                    padding: "0 4px",
                    opacity: clip.pinned ? 1 : 0.3,
                  }}
                >
                  📌
                </button>
              </div>
              <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 4, fontFamily: "monospace" }}>
                {clip.source} · {new Date(clip.created_at).toLocaleTimeString()}
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}

// ── Prompts Panel ──
function PromptsPanel({ api, bridge }) {
  const [prompts, setPrompts] = useState([
    { id: "p1", name: "Fix Grammar", content: "Fix the grammar and spelling in this text. Keep the meaning and tone identical. Return only the corrected text.", category: "rewrite", hotkey: "ctrl+shift+1" },
    { id: "p2", name: "Summarize", content: "Summarize the following text in 2-3 clear sentences:", category: "summarize", hotkey: "ctrl+shift+2" },
    { id: "p3", name: "Professional Tone", content: "Rewrite this text in a professional, formal tone. Keep the meaning identical:", category: "rewrite", hotkey: "ctrl+shift+3" },
    { id: "p4", name: "Simplify", content: "Simplify this text to a 9th-grade reading level without losing any meaning:", category: "rewrite", hotkey: "ctrl+shift+4" },
    { id: "p5", name: "Expand", content: "Expand this into a more detailed explanation, adding relevant context:", category: "expand", hotkey: "ctrl+shift+5" },
    { id: "p6", name: "Theophysics Voice", content: "Rewrite this in the Theophysics explanatory voice — human anchor first, principle revealed, core insight, direct and earned. No academic hedging.", category: "custom", hotkey: null },
  ]);
  const [editing, setEditing] = useState(null);
  const [editName, setEditName] = useState("");
  const [editContent, setEditContent] = useState("");

  const startEdit = (p) => {
    setEditing(p.id);
    setEditName(p.name);
    setEditContent(p.content);
  };

  const saveEdit = () => {
    setPrompts((prev) =>
      prev.map((p) =>
        p.id === editing ? { ...p, name: editName, content: editContent } : p
      )
    );
    setEditing(null);
  };

  const usePrompt = async (prompt) => {
    // Copy prompt to clipboard
    try {
      await navigator.clipboard.writeText(prompt.content);
    } catch {}
    // If bridge connected, trigger the rewrite flow
    bridge.send?.("run_prompt", { prompt_id: prompt.id, content: prompt.content });
  };

  const catColors = {
    rewrite: "#4a9eff",
    summarize: "#9b59b6",
    expand: "#2ecc71",
    custom: "#e67e22",
    general: "#95a5a6",
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, height: "100%" }}>
      <div style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "monospace" }}>
        QUICK PROMPTS — click to copy, Ctrl+Space to run on selected text
      </div>
      <div style={{ flex: 1, overflowY: "auto" }}>
        {prompts.map((p) => (
          <div key={p.id} style={{ marginBottom: 8 }}>
            {editing === p.id ? (
              <div style={{ padding: 12, background: "var(--surface-2)", borderRadius: 6, border: "1px solid var(--accent)" }}>
                <input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  style={{ ...inputStyle, marginBottom: 8 }}
                />
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  rows={4}
                  style={{ ...inputStyle, resize: "vertical", fontFamily: "monospace", fontSize: 12 }}
                />
                <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                  <button onClick={saveEdit} style={btnPrimary}>Save</button>
                  <button onClick={() => setEditing(null)} style={btnGhost}>Cancel</button>
                </div>
              </div>
            ) : (
              <div
                style={{
                  padding: "10px 12px",
                  background: "var(--surface-2)",
                  borderRadius: 6,
                  cursor: "pointer",
                  borderLeft: `3px solid ${catColors[p.category] || catColors.general}`,
                  transition: "all 0.15s",
                }}
                onClick={() => usePrompt(p)}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontWeight: 600, fontSize: 13, color: "var(--text-primary)" }}>{p.name}</span>
                    <span
                      style={{
                        fontSize: 10,
                        padding: "1px 6px",
                        borderRadius: 3,
                        background: catColors[p.category] + "22",
                        color: catColors[p.category],
                        fontFamily: "monospace",
                      }}
                    >
                      {p.category}
                    </span>
                  </div>
                  <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                    {p.hotkey && (
                      <span style={{ fontSize: 10, color: "var(--text-muted)", fontFamily: "monospace", background: "var(--surface-3)", padding: "2px 6px", borderRadius: 3 }}>
                        {p.hotkey}
                      </span>
                    )}
                    <button
                      onClick={(e) => { e.stopPropagation(); startEdit(p); }}
                      style={{ ...btnGhost, fontSize: 12, padding: "2px 6px" }}
                    >
                      ✏️
                    </button>
                  </div>
                </div>
                <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4, lineHeight: 1.3, maxHeight: 40, overflow: "hidden" }}>
                  {p.content}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Links Panel ──
function LinksPanel() {
  const [links, setLinks] = useState([
    { id: "l1", title: "Faith Through Physics", url: "https://faiththruphysics.com", icon: "⛪", category: "sites" },
    { id: "l2", title: "Theophysics Dashboard", url: "https://theophysics-dashboard.pages.dev", icon: "📊", category: "tools" },
    { id: "l3", title: "Comms Hub", url: "https://comms.dlowehomelab.com", icon: "📡", category: "tools" },
    { id: "l4", title: "Cloudflare Dashboard", url: "https://dash.cloudflare.com", icon: "☁️", category: "tools" },
    { id: "l5", title: "GitHub", url: "https://github.com", icon: "🐙", category: "dev" },
    { id: "l6", title: "Claude", url: "https://claude.ai", icon: "🤖", category: "ai" },
    { id: "l7", title: "ChatGPT", url: "https://chat.openai.com", icon: "💬", category: "ai" },
    { id: "l8", title: "Kimi", url: "https://kimi.moonshot.cn", icon: "🌙", category: "ai" },
  ]);

  const categories = [...new Set(links.map((l) => l.category))];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, height: "100%" }}>
      {categories.map((cat) => (
        <div key={cat}>
          <div style={{ fontSize: 11, fontFamily: "monospace", color: "var(--text-muted)", marginBottom: 6, textTransform: "uppercase" }}>
            {cat}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 8 }}>
            {links
              .filter((l) => l.category === cat)
              .map((link) => (
                <a
                  key={link.id}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    padding: "10px 12px",
                    background: "var(--surface-2)",
                    borderRadius: 6,
                    textDecoration: "none",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    transition: "all 0.15s",
                    border: "1px solid var(--border)",
                  }}
                >
                  <span style={{ fontSize: 18 }}>{link.icon}</span>
                  <span style={{ fontSize: 13, color: "var(--text-primary)", fontWeight: 500 }}>{link.title}</span>
                </a>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── AI Panel ──
function AIPanel({ api }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEnd = useRef(null);

  const scrollToBottom = () => messagesEnd.current?.scrollIntoView({ behavior: "smooth" });

  useEffect(() => scrollToBottom(), [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    // In production: api.post('/api/ai', { messages: [...messages, userMsg] })
    // Demo: show placeholder
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Connect the Worker API to enable AI responses. Your Claude API key stays server-side — the PWA never sees it.\n\nTo deploy:\n1. wrangler d1 create stratum\n2. wrangler d1 execute stratum --file=schema.sql\n3. wrangler secret put CLAUDE_API_KEY\n4. wrangler secret put STRATUM_AUTH_TOKEN\n5. wrangler deploy",
        },
      ]);
      setLoading(false);
    }, 800);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", gap: 12 }}>
      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8, paddingRight: 4 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>🤖</div>
            <div style={{ fontSize: 13 }}>AI assistant — runs through your Worker, key stays server-side</div>
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              padding: "10px 14px",
              borderRadius: 8,
              maxWidth: "85%",
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              background: m.role === "user" ? "var(--accent)" : "var(--surface-2)",
              color: m.role === "user" ? "#fff" : "var(--text-primary)",
              fontSize: 13,
              lineHeight: 1.5,
              whiteSpace: "pre-wrap",
            }}
          >
            {m.content}
          </div>
        ))}
        {loading && (
          <div style={{ padding: "10px 14px", borderRadius: 8, background: "var(--surface-2)", alignSelf: "flex-start", fontSize: 13, color: "var(--text-muted)" }}>
            thinking...
          </div>
        )}
        <div ref={messagesEnd} />
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
          placeholder="Ask anything..."
          style={{ ...inputStyle, flex: 1 }}
        />
        <button onClick={sendMessage} disabled={loading} style={btnPrimary}>
          →
        </button>
      </div>
    </div>
  );
}

// ── Settings Panel ──
function SettingsPanel({ bridge, apiUrl, setApiUrl, authToken, setAuthToken }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div>
        <div style={sectionHeader}>CONNECTION</div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              background: bridge.connected ? "#2ecc71" : "#e74c3c",
              boxShadow: bridge.connected ? "0 0 6px #2ecc71" : "none",
            }}
          />
          <span style={{ fontSize: 13, color: "var(--text-primary)" }}>
            Local Bridge: {bridge.connected ? "Connected (ws://localhost:9877)" : "Not detected"}
          </span>
        </div>
        <div style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.5 }}>
          {bridge.connected
            ? "AHK hotkeys active. Shortcuts will execute locally."
            : "No local bridge detected. Shortcuts will copy to clipboard instead. Run bridge.py on your Windows machine to enable AHK integration."}
        </div>
      </div>

      <div>
        <div style={sectionHeader}>API</div>
        <label style={labelStyle}>Worker URL</label>
        <input value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} style={inputStyle} placeholder="https://stratum-api.theophysics.pro" />
        <label style={{ ...labelStyle, marginTop: 12 }}>Auth Token</label>
        <input value={authToken} onChange={(e) => setAuthToken(e.target.value)} type="password" style={inputStyle} placeholder="Bearer token" />
      </div>

      <div>
        <div style={sectionHeader}>SHORTCUTS</div>
        <div style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.7, fontFamily: "monospace" }}>
          Ctrl+Alt+G → Open Stratum{"\n"}
          Ctrl+Alt+C → Clipboard{"\n"}
          Ctrl+Alt+P → Prompts{"\n"}
          Ctrl+Alt+L → Links{"\n"}
          Ctrl+Space → Rewrite selected text{"\n"}
          Ctrl+Shift+1-5 → Quick prompts{"\n"}
          Ctrl+Shift+0-9 → Save to slot{"\n"}
          Ctrl+Alt+0-9 → Paste from slot
        </div>
      </div>

      <div>
        <div style={sectionHeader}>ABOUT</div>
        <div style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.5 }}>
          Stratum Cloud v1.0{"\n"}
          PWA + Cloudflare Workers + D1{"\n"}
          Local bridge for AHK integration{"\n"}
          POF 2828
        </div>
      </div>
    </div>
  );
}

// ── Main App ──
export default function StratumApp() {
  const [activePanel, setActivePanel] = useState("clipboard");
  const [apiUrl, setApiUrl] = useState(DEFAULT_API);
  const [authToken, setAuthToken] = useState("");

  const api = useApiClient(apiUrl, authToken);
  const bridge = useBridge();

  const panelIcons = {
    clipboard: "📋",
    prompts: "⚡",
    links: "🔗",
    ai: "🤖",
    settings: "⚙️",
  };

  return (
    <div
      style={{
        "--accent": "#4a9eff",
        "--accent-dim": "#4a9eff15",
        "--surface-1": "#0d1117",
        "--surface-2": "#161b22",
        "--surface-3": "#21262d",
        "--text-primary": "#e6edf3",
        "--text-muted": "#8b949e",
        "--border": "#30363d",
        fontFamily: "'Inter', -apple-system, sans-serif",
        background: "var(--surface-1)",
        color: "var(--text-primary)",
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 16px",
          borderBottom: "1px solid var(--border)",
          background: "var(--surface-2)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div
            style={{
              width: 28,
              height: 28,
              background: "linear-gradient(135deg, #4a9eff 0%, #9b59b6 100%)",
              borderRadius: 6,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 14,
              fontWeight: 800,
              color: "#fff",
            }}
          >
            S
          </div>
          <span style={{ fontWeight: 700, fontSize: 15, letterSpacing: "-0.3px" }}>STRATUM</span>
          <span style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "monospace" }}>cloud</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: bridge.connected ? "#2ecc71" : "#e74c3c",
              boxShadow: bridge.connected ? "0 0 4px #2ecc71" : "none",
            }}
          />
          <span style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "monospace" }}>
            {bridge.connected ? "bridge" : "cloud"}
          </span>
        </div>
      </div>

      {/* Tab Bar */}
      <div
        style={{
          display: "flex",
          borderBottom: "1px solid var(--border)",
          background: "var(--surface-2)",
        }}
      >
        {PANELS.map((p) => (
          <button
            key={p}
            onClick={() => setActivePanel(p)}
            style={{
              flex: 1,
              padding: "10px 0",
              background: "transparent",
              border: "none",
              borderBottom: activePanel === p ? "2px solid var(--accent)" : "2px solid transparent",
              color: activePanel === p ? "var(--text-primary)" : "var(--text-muted)",
              cursor: "pointer",
              fontSize: 12,
              fontWeight: activePanel === p ? 600 : 400,
              transition: "all 0.15s",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 2,
            }}
          >
            <span style={{ fontSize: 16 }}>{panelIcons[p]}</span>
            <span style={{ textTransform: "capitalize" }}>{p}</span>
          </button>
        ))}
      </div>

      {/* Panel Content */}
      <div style={{ flex: 1, overflow: "auto", padding: 16 }}>
        {activePanel === "clipboard" && <ClipboardPanel api={api} bridge={bridge} />}
        {activePanel === "prompts" && <PromptsPanel api={api} bridge={bridge} />}
        {activePanel === "links" && <LinksPanel />}
        {activePanel === "ai" && <AIPanel api={api} />}
        {activePanel === "settings" && (
          <SettingsPanel
            bridge={bridge}
            apiUrl={apiUrl}
            setApiUrl={setApiUrl}
            authToken={authToken}
            setAuthToken={setAuthToken}
          />
        )}
      </div>
    </div>
  );
}

// ── Shared Styles ──
const inputStyle = {
  width: "100%",
  padding: "8px 12px",
  background: "var(--surface-2)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  color: "var(--text-primary)",
  fontSize: 13,
  outline: "none",
  boxSizing: "border-box",
  fontFamily: "inherit",
};

const btnPrimary = {
  padding: "8px 16px",
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
  fontWeight: 600,
  fontSize: 14,
  whiteSpace: "nowrap",
};

const btnGhost = {
  padding: "6px 12px",
  background: "transparent",
  color: "var(--text-muted)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: 12,
};

const sectionHeader = {
  fontSize: 11,
  fontFamily: "monospace",
  color: "var(--text-muted)",
  marginBottom: 10,
  letterSpacing: "0.5px",
};

const labelStyle = {
  display: "block",
  fontSize: 12,
  color: "var(--text-muted)",
  marginBottom: 4,
};
