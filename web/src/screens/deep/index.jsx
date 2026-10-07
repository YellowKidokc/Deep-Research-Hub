import { useEffect, useState } from "react";
import { api } from "../../api.js";
import Log from "../../components/Log.jsx";

const time = (s) => (s ? new Date(s * 1000).toLocaleString() : "");

export default function DeepResearch({ tab }) {
  return tab === "Runs" ? <Runs /> : <Queue />;
}

// data/jobs/*.yaml -> drh_queue.py -> data/deep_research/<job>/<stamp>/
function Queue() {
  const [jobs, setJobs] = useState(null);
  const [procs, setProcs] = useState([]);
  const [parallel, setParallel] = useState("");
  const [sel, setSel] = useState(null);
  const [error, setError] = useState("");

  const refresh = () => {
    api("/deep/jobs").then(setJobs).catch((e) => setError(e.message));
    api("/procs").then((all) => setProcs(all.filter((p) => p.launch_id.startsWith("deep.")))).catch(() => {});
  };
  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, []);

  const start = async (id, params = {}) => {
    setError("");
    try {
      const rec = await api(`/launch/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ params }),
      });
      setSel(rec.id);
      refresh();
    } catch (e) {
      setError(e.message);
    }
  };

  if (!jobs) return <p className="dim">{error || "Loading…"}</p>;
  const shown = sel ?? procs[0]?.id;
  const section = (title, list) => (
    <>
      <h2>{title} <span className="dim">{list.length}</span></h2>
      {list.length > 0 && (
        <table>
          <tbody>
            {list.map((j) => <tr key={j.name}><td className="mono">{j.name}</td><td>{j.query}</td></tr>)}
          </tbody>
        </table>
      )}
    </>
  );

  return (
    <div>
      <h1>Deep Research — Queue</h1>
      <p className="dim mono">{jobs.dir}{jobs.has_defaults ? "" : "   (no _defaults.yaml yet: the first run creates it)"}</p>
      <div className="row">
        <button onClick={() => start("deep.check")}>Check</button>
        <button onClick={() => start("deep.retry")} disabled={!jobs.failed.length}>Retry {jobs.failed.length} failed</button>
        <input className="narrow" placeholder="parallel" value={parallel} onChange={(e) => setParallel(e.target.value)} />
        <button onClick={() => start("deep.queue", { parallel: parallel.trim() })} disabled={!jobs.pending.length}>
          Run {jobs.pending.length} job{jobs.pending.length === 1 ? "" : "s"}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {section("Pending", jobs.pending)}
      {section("Running", jobs.running)}
      {section("Failed", jobs.failed)}
      {section("Done", jobs.done)}

      <h2>Queue runs</h2>
      <table>
        <tbody>
          {procs.map((p) => (
            <tr key={p.id} className={p.id === shown ? "active" : ""} onClick={() => setSel(p.id)}>
              <td>{p.id}</td><td>{p.label}</td><td className={`st-${p.status}`}>{p.status}</td><td>{time(p.started)}</td>
            </tr>
          ))}
          {procs.length === 0 && <tr><td className="dim">Not run yet.</td></tr>}
        </tbody>
      </table>
      {shown != null && <Log id={shown} />}
    </div>
  );
}

function Runs() {
  const [runs, setRuns] = useState(null);
  const [sel, setSel] = useState(null);
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/deep/runs").then(setRuns).catch((e) => setError(e.message));
  }, []);

  const open = async (r, name) => {
    setSel(r);
    setError("");
    try {
      setFile(await api(`/deep/file?job=${encodeURIComponent(r.job)}&stamp=${encodeURIComponent(r.stamp)}&name=${name}`));
    } catch (e) {
      setFile(null);
      setError(e.message);
    }
  };

  if (!runs) return <p className="dim">{error || "Loading…"}</p>;
  const rc = (r) => {
    const x = r.receipt;
    if (!x) return "";
    if (r.job_type === "fork_map") {
      const missing = (x.legs_expected_not_found || []).join(", ");
      return `${x.forks ?? 0} forks · ${x.legs_expected_found ?? 0}/${x.expected_legs ?? 0} expected legs sourced`
        + (x.legs_found_not_expected ? ` · +${x.legs_found_not_expected} unexpected` : "")
        + (missing ? ` · no source: ${missing}` : "") + ` · ${x.passages ?? 0} passages`;
    }
    return `${x.files_loaded}/${x.files_found} files · ${x.chunks_returned}/${x.chunks_produced} chunks`;
  };
  const FORK_FILES = [["forks.md", "forks"], ["premise.json", "premise"], ["triage.json", "triage"],
    ["passages.json", "passages"], ["pipeline.json", "pipeline"]];

  return (
    <div>
      <h1>Deep Research — Runs</h1>
      <p className="dim mono">{runs.dir}</p>
      {error && <p className="error">{error}</p>}
      <table>
        <thead><tr><th>Job</th><th>Run</th><th>Status</th><th>Query</th><th>Read</th><th>Seconds</th><th></th></tr></thead>
        <tbody>
          {runs.runs.map((r) => (
            <tr key={r.job + r.stamp} className={sel === r ? "active" : ""}>
              <td className="mono">{r.job}</td>
              <td className="mono">{r.stamp}</td>
              <td className={`st-${r.status}`} title={r.error || ""}>{r.status}</td>
              <td>{r.query}</td>
              <td className="dim">{rc(r)}</td>
              <td>{r.seconds}</td>
              <td className="links">
                <a onClick={() => open(r, r.status === "done" ? "report.md" : "error.txt")}>{r.status === "done" ? "report" : "error"}</a>
                {r.job_type === "fork_map"
                  ? FORK_FILES.map(([f, label]) => <span key={f}>{" · "}<a onClick={() => open(r, f)}>{label}</a></span>)
                  : <>{" · "}<a onClick={() => open(r, "receipt.json")}>receipt</a></>}
                {" · "}<a onClick={() => open(r, "sources.json")}>sources</a>
              </td>
            </tr>
          ))}
          {runs.runs.length === 0 && <tr><td colSpan="7" className="dim">No runs yet.</td></tr>}
        </tbody>
      </table>
      {file && (
        <>
          <h2 className="mono">{file.path}</h2>
          <pre className="log doc">{file.text}</pre>
        </>
      )}
    </div>
  );
}
