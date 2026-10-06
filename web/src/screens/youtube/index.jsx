import { useEffect, useState } from "react";
import { api } from "../../api.js";
import Log from "../../components/Log.jsx";

const LAUNCH = "youtube.grab";
const time = (s) => (s ? new Date(s * 1000).toLocaleString() : "");
const kb = (n) => `${Math.max(1, Math.round(n / 1024))} KB`;

export default function YouTube({ tab }) {
  return tab === "Library" ? <Library /> : <Intake />;
}

// Paste a video or channel URL -> ytgrab.py writes data/youtube/<Channel>/<Title>.md,
// then slot Y/1 appends the baseline summary to each new file.
function Intake() {
  const [url, setUrl] = useState("");
  const [limit, setLimit] = useState("");
  const [runs, setRuns] = useState([]);
  const [sel, setSel] = useState(null);
  const [error, setError] = useState("");

  const refresh = () =>
    api("/procs")
      .then((all) => setRuns(all.filter((p) => p.launch_id === LAUNCH)))
      .catch((e) => setError(e.message));

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 2000);
    return () => clearInterval(t);
  }, []);

  const kind = /youtu\.be\/|[?&]v=|\/shorts\//.test(url) ? "this video"
    : /\/@|\/channel\/|\/c\/|\/user\//.test(url) ? "whole channel"
    : /list=/.test(url) ? "playlist" : "";

  const run = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const rec = await api(`/launch/${LAUNCH}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ params: { url: url.trim(), limit: limit.trim() } }),
      });
      setSel(rec.id);
      setUrl("");
      refresh();
    } catch (e) {
      setError(e.message);
    }
  };

  const shown = sel ?? runs[0]?.id;

  return (
    <div>
      <h1>YouTube — Intake</h1>
      <p className="dim">
        A video link grabs that video; a channel link (@name, /channel/…) grabs the whole channel.
        Files land in data/youtube/&lt;Channel&gt;/ and already-saved videos are skipped.
      </p>
      <form onSubmit={run} className="row">
        <input className="grow" placeholder="https://www.youtube.com/watch?v=…  or  https://www.youtube.com/@channel"
               value={url} onChange={(e) => setUrl(e.target.value)} />
        <input className="narrow" placeholder="limit" value={limit} onChange={(e) => setLimit(e.target.value)} />
        <button type="submit" disabled={!url.trim()}>Grab</button>
        <span className="dim">{kind}</span>
      </form>
      {error && <p className="error">{error}</p>}

      <h2>Runs</h2>
      <table>
        <thead><tr><th>#</th><th>URL</th><th>Status</th><th>Started</th><th>Ended</th></tr></thead>
        <tbody>
          {runs.map((p) => (
            <tr key={p.id} className={p.id === shown ? "active" : ""} onClick={() => setSel(p.id)}>
              <td>{p.id}</td>
              <td className="mono">{p.params?.url}{p.params?.limit ? `  (limit ${p.params.limit})` : ""}</td>
              <td className={`st-${p.status}`}>{p.status}</td>
              <td>{time(p.started)}</td>
              <td>{time(p.ended)}</td>
            </tr>
          ))}
          {runs.length === 0 && <tr><td colSpan="5" className="dim">No runs yet.</td></tr>}
        </tbody>
      </table>
      {shown != null && <Log id={shown} />}
    </div>
  );
}

function Library() {
  const [lib, setLib] = useState(null);
  const [channel, setChannel] = useState("");
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/youtube/library").then(setLib).catch((e) => setError(e.message));
  }, []);

  const open = async (name) => {
    setError("");
    try {
      setFile(await api(`/youtube/file?channel=${encodeURIComponent(channel)}&name=${encodeURIComponent(name)}`));
    } catch (e) {
      setError(e.message);
    }
  };

  if (!lib) return <p className="dim">{error || "Loading…"}</p>;
  const ch = lib.channels.find((c) => c.name === channel);
  const count = (c, f) => c.videos.filter(f).length;

  return (
    <div>
      <h1>YouTube — Library</h1>
      <p className="dim mono">{lib.root}</p>
      {error && <p className="error">{error}</p>}
      <table>
        <thead><tr><th>Channel</th><th>Videos</th><th>Summarized</th><th>Failed / none</th></tr></thead>
        <tbody>
          {lib.channels.map((c) => (
            <tr key={c.name} className={c.name === channel ? "active" : ""}
                onClick={() => { setChannel(c.name); setFile(null); }}>
              <td>{c.name}</td>
              <td>{c.videos.length}</td>
              <td>{count(c, (v) => v.summarized)}</td>
              <td>{count(c, (v) => v.state !== "ok")}</td>
            </tr>
          ))}
          {lib.channels.length === 0 && <tr><td colSpan="4" className="dim">Nothing downloaded yet.</td></tr>}
        </tbody>
      </table>

      {ch && (
        <>
          <h2>{ch.name}</h2>
          <table>
            <thead><tr><th>File</th><th>State</th><th>Summary</th><th>Size</th><th>Modified</th></tr></thead>
            <tbody>
              {ch.videos.map((v) => (
                <tr key={v.name} className={file?.path?.endsWith(v.name) ? "active" : ""} onClick={() => open(v.name)}>
                  <td>{v.name}</td>
                  <td className={v.state === "ok" ? "" : "st-failed"}>{v.state}</td>
                  <td>{v.summarized ? "yes" : ""}</td>
                  <td>{kb(v.bytes)}</td>
                  <td>{time(v.modified)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {file && (
        <>
          <h2 className="mono">{file.path}</h2>
          <pre className="log doc">{file.text}</pre>
        </>
      )}
    </div>
  );
}
