import { useEffect, useState } from "react";
import { api } from "../../api.js";
import Log from "../../components/Log.jsx";

const time = (s) => (s ? new Date(s * 1000).toLocaleString() : "");

export default function TargetedResearch({ tab }) {
  return tab === "Facts" ? <Facts /> : <Battery />;
}

// One topic -> drh_targeted.py -> data/targeted/<topic>/<stamp>/facts.json
function Battery() {
  const [battery, setBattery] = useState(null);
  const [topic, setTopic] = useState("");
  const [picked, setPicked] = useState({});
  const [procs, setProcs] = useState([]);
  const [sel, setSel] = useState(null);
  const [error, setError] = useState("");

  const refresh = () =>
    api("/procs").then((all) => setProcs(all.filter((p) => p.launch_id === "targeted.run"))).catch(() => {});
  useEffect(() => {
    api("/targeted/battery")
      .then((b) => {
        setBattery(b);
        setPicked(Object.fromEntries(b.items.map((i) => [i.id, !!i.default && !i.needs])));
      })
      .catch((e) => setError(e.message));
    refresh();
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, []);

  const run = async () => {
    setError("");
    const items = battery.items.filter((i) => picked[i.id]).map((i) => i.id);
    const defaults = battery.items.filter((i) => i.default && !i.needs).map((i) => i.id);
    const same = items.length === defaults.length && items.every((i) => defaults.includes(i));
    try {
      const rec = await api("/launch/targeted.run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ params: { topic: topic.trim(), items: same ? "" : items.join(",") } }),
      });
      setSel(rec.id);
      refresh();
    } catch (e) {
      setError(e.message);
    }
  };

  if (!battery) return <p className="dim">{error || "Loading…"}</p>;
  const chosen = battery.items.filter((i) => picked[i.id]).length;
  const shown = sel ?? procs[0]?.id;

  return (
    <div>
      <h1>Targeted Research — Battery</h1>
      <p className="dim">{battery.description}</p>
      <div className="row">
        <input className="grow" placeholder="Topic, e.g. privatio boni" value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && topic.trim() && chosen && run()} />
        <button onClick={run} disabled={!topic.trim() || !chosen}>Run {chosen} item{chosen === 1 ? "" : "s"}</button>
      </div>
      {error && <p className="error">{error}</p>}
      <table>
        <tbody>
          {battery.items.map((i) => (
            <tr key={i.id} className={i.needs ? "dim" : ""}>
              <td>
                <input type="checkbox" checked={!!picked[i.id]} disabled={!!i.needs}
                  onChange={(e) => setPicked({ ...picked, [i.id]: e.target.checked })} />
              </td>
              <td>{i.label}</td>
              <td>{i.question}</td>
              <td className="dim">
                {i.needs ? `needs ${i.needs}` : (i.requires || []).length ? `must state: ${i.requires.join(", ")}` : ""}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Runs</h2>
      <table>
        <tbody>
          {procs.map((p) => (
            <tr key={p.id} className={p.id === shown ? "active" : ""} onClick={() => setSel(p.id)}>
              <td>{p.id}</td><td>{p.params?.topic}</td><td className={`st-${p.status}`}>{p.status}</td><td>{time(p.started)}</td>
            </tr>
          ))}
          {procs.length === 0 && <tr><td className="dim">Not run yet.</td></tr>}
        </tbody>
      </table>
      {shown != null && <Log id={shown} />}
    </div>
  );
}

function Facts() {
  const [runs, setRuns] = useState(null);
  const [sel, setSel] = useState(null);
  const [facts, setFacts] = useState(null);
  const [raw, setRaw] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/targeted/runs").then(setRuns).catch((e) => setError(e.message));
  }, []);

  const q = (r, name) =>
    `/targeted/file?topic_dir=${encodeURIComponent(r.topic_dir)}&stamp=${encodeURIComponent(r.stamp)}&name=${name}`;
  const open = async (r) => {
    setSel(r);
    setError("");
    setRaw(null);
    try {
      setFacts(JSON.parse((await api(q(r, "facts.json"))).text));
    } catch (e) {
      setFacts(null);
      try { setRaw(await api(q(r, "error.txt"))); } catch { setError(e.message); }
    }
  };
  const show = async (r, name) => {
    try { setRaw(await api(q(r, name))); } catch (e) { setError(e.message); }
  };

  if (!runs) return <p className="dim">{error || "Loading…"}</p>;
  const counts = (s) => (s ? Object.values(s).reduce((m, v) => ({ ...m, [v]: (m[v] || 0) + 1 }), {}) : {});

  return (
    <div>
      <h1>Targeted Research — Facts</h1>
      <p className="dim mono">{runs.dir}</p>
      {error && <p className="error">{error}</p>}
      <table>
        <thead><tr><th>Topic</th><th>Run</th><th>Status</th><th>Items</th><th>Findings</th><th></th></tr></thead>
        <tbody>
          {runs.runs.map((r) => {
            const c = counts(r.summary);
            return (
              <tr key={r.topic_dir + r.stamp} className={sel === r ? "active" : ""}>
                <td>{r.topic || r.topic_dir}</td>
                <td className="mono">{r.stamp}</td>
                <td className={`st-${r.status}`}>{r.status}</td>
                <td className="dim">{Object.entries(c).map(([k, v]) => `${v} ${k}`).join(" · ")}</td>
                <td>{r.findings ?? ""}{r.rejected ? <span className="dim"> ({r.rejected} rejected)</span> : null}</td>
                <td className="links">
                  <a onClick={() => open(r)}>facts</a>
                  {" · "}<a onClick={() => show(r, "facts.md")}>md</a>
                  {" · "}<a onClick={() => show(r, "run.json")}>run</a>
                </td>
              </tr>
            );
          })}
          {runs.runs.length === 0 && <tr><td colSpan="6" className="dim">No runs yet.</td></tr>}
        </tbody>
      </table>

      {raw && (
        <>
          <h2 className="mono">{raw.path}</h2>
          <pre className="log doc">{raw.text}</pre>
        </>
      )}
      {!raw && facts && (
        <>
          <h2>{facts.topic}</h2>
          {Object.values(facts.items).map((it) => (
            <section key={it.id} className="fact">
              <h3>{it.label} <span className={`st-${it.status === "found" ? "done" : it.status === "failed" ? "failed" : "dim"} badge`}>{it.status}</span></h3>
              <p className="dim">{it.question}</p>
              {it.note && <p>{it.note}</p>}
              <ol>
                {(it.findings || []).map((f, n) => (
                  <li key={n}>
                    <b>{f.claim}</b>
                    {[f.who, f.when, f.where].filter(Boolean).length > 0 && (
                      <span className="dim"> — {[f.who, f.when, f.where].filter(Boolean).join(" · ")}</span>
                    )}
                    {f.note && <div className="dim">{f.note}</div>}
                    {f.passages.map((p) => (
                      <blockquote key={p.id}>
                        “{p.quote}” <a href={p.url} target="_blank" rel="noreferrer">{p.title || p.url}</a>
                      </blockquote>
                    ))}
                  </li>
                ))}
              </ol>
              {(it.rejected || []).length > 0 && (
                <details>
                  <summary className="dim">{it.rejected.length} rejected</summary>
                  <ul>
                    {it.rejected.map((r, n) => (
                      <li key={n}>{r.finding.claim} <span className="error">— {r.reasons.join("; ")}</span></li>
                    ))}
                  </ul>
                </details>
              )}
              {it.searched && (
                <p className="dim small">
                  {it.searched.queries} queries · {it.searched.urls} results · {it.searched.pages_read} pages read ·{" "}
                  {it.searched.passages} passages · {it.searched.quotes_not_verbatim} quotes not verbatim
                </p>
              )}
            </section>
          ))}
        </>
      )}
    </div>
  );
}
