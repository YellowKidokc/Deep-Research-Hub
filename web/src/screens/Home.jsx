import { useEffect, useState } from "react";
import { api, post } from "../api.js";
import Log from "../components/Log.jsx";

const time = (s) => (s ? new Date(s * 1000).toLocaleString() : "");

export default function Home() {
  const [launch, setLaunch] = useState([]);
  const [procs, setProcs] = useState([]);
  const [apps, setApps] = useState([]);
  const [sel, setSel] = useState(null);
  const [error, setError] = useState("");

  const refresh = () => api("/procs").then(setProcs).catch((e) => setError(e.message));

  useEffect(() => {
    api("/launch").then(setLaunch).catch((e) => setError(e.message));
    api("/apps").then(setApps).catch((e) => setError(e.message));
    refresh();
    const t = setInterval(refresh, 2000);
    return () => clearInterval(t);
  }, []);

  const run = async (id) => {
    setError("");
    try {
      const rec = await post(`/launch/${encodeURIComponent(id)}`);
      setSel(rec.id);
      refresh();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div>
      <h1>Home</h1>
      <p className="dim">
        Suggested order: 1 → 2 → 3/4/5 → 6 → 7. Nothing enforces it.
      </p>
      {error && <p className="error">{error}</p>}

      <h2>Launch</h2>
      <table>
        <thead><tr><th>Entry</th><th>App</th><th>Command</th><th></th></tr></thead>
        <tbody>
          {launch.map((l) => (
            <tr key={l.id}>
              <td>{l.label}</td>
              <td>{l.app}/{l.cwd === "." ? "" : l.cwd}</td>
              <td className="mono">{[l.program, ...l.args].join(" ")}</td>
              <td>
                {l.params?.length
                  ? <a href={`#/${l.id.split(".")[0]}`} className="dim">needs input</a>
                  : <button onClick={() => run(l.id)}>Run</button>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Processes</h2>
      <table>
        <thead><tr><th>#</th><th>Entry</th><th>Status</th><th>Exit</th><th>Started</th><th>Ended</th><th></th></tr></thead>
        <tbody>
          {procs.map((p) => (
            <tr key={p.id} className={p.id === sel ? "active" : ""} onClick={() => setSel(p.id)}>
              <td>{p.id}</td>
              <td>{p.label}</td>
              <td className={`st-${p.status}`}>{p.status}</td>
              <td>{p.exit_code ?? ""}</td>
              <td>{time(p.started)}</td>
              <td>{time(p.ended)}</td>
              <td>
                {p.status === "running" && (
                  <button onClick={(e) => { e.stopPropagation(); post(`/procs/${p.id}/stop`).then(refresh); }}>Stop</button>
                )}
              </td>
            </tr>
          ))}
          {procs.length === 0 && <tr><td colSpan="7" className="dim">Nothing has run yet.</td></tr>}
        </tbody>
      </table>

      {sel != null && <Log id={sel} />}

      <h2>Apps</h2>
      <table>
        <thead><tr><th>Folder</th><th>UPSTREAM.md</th></tr></thead>
        <tbody>
          {apps.map((a) => (
            <tr key={a.name}><td>{a.name}</td><td className="dim">{a.upstream.split("\n")[0]}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
