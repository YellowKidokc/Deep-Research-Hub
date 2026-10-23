import { useEffect, useState } from "react";
import { api } from "../../api.js";
import Log from "../../components/Log.jsx";

const WORKER = "deepcrawl.server";
const time = (s) => (s ? new Date(s * 1000).toLocaleString() : "");

// One form per tab. Each runs a hub launch entry; output lands in data/<folder>/.
const TABS = {
  Scrape: {
    launch: "acquire.scrape", folder: "crawl", needsWorker: true, button: "Scrape",
    blurb: "One page to clean markdown (title, description, body) via the local Deepcrawl worker.",
    fields: [{ name: "url", placeholder: "https://…", grow: true }],
  },
  Links: {
    launch: "acquire.links", folder: "links", needsWorker: true, button: "Get links",
    blurb: "Every link on a page, internal and external (a page's citations), plus Deepcrawl's tree of the site. Writes links.txt, links.json, tree.json.",
    fields: [{ name: "url", placeholder: "https://…", grow: true }],
  },
  Crawl: {
    launch: "acquire.crawl", folder: "crawl", needsWorker: true, button: "Crawl",
    blurb: "Walk a site breadth-first on the same host and save each page as markdown, with links.json and an index.",
    fields: [
      { name: "url", placeholder: "https://…", grow: true },
      { name: "pages", placeholder: "pages (1)", narrow: true },
      { name: "depth", placeholder: "depth (3)", narrow: true },
    ],
  },
  Search: {
    launch: "search.marginalia", folder: "search", needsWorker: false, button: "Search",
    blurb: "Result links from Marginalia Search (the independent, small-web engine) through its official API. "
      + "\"read\" also pulls the top N results to markdown through Deepcrawl. "
      + "The shared public key is often busy; set MARGINALIA_API_KEY (free personal key: kontakt@marginalia.nu) before starting the hub.",
    fields: [
      { name: "query", placeholder: "search words", grow: true },
      { name: "count", placeholder: "results (30)", narrow: true },
      { name: "read", placeholder: "read top N", narrow: true },
    ],
  },
};

export default function Acquisition({ tab }) {
  const cfg = TABS[tab] || TABS.Scrape;
  const [procs, setProcs] = useState([]);
  const [error, setError] = useState("");

  const refresh = () => api("/procs").then(setProcs).catch((e) => setError(e.message));
  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 2000);
    return () => clearInterval(t);
  }, []);

  const worker = procs.find((p) => p.launch_id === WORKER && p.status === "running");
  return (
    <div>
      <h1>Acquisition — {tab}</h1>
      <Worker running={worker} onError={setError} refresh={refresh} needed={cfg.needsWorker} />
      {error && <p className="error">{error}</p>}
      <RunForm key={tab} cfg={cfg} runs={procs.filter((p) => p.launch_id === cfg.launch)} refresh={refresh} />
    </div>
  );
}

function Worker({ running, needed, onError, refresh }) {
  const start = async () => {
    onError("");
    try {
      await api(`/launch/${WORKER}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
      refresh();
    } catch (e) {
      onError(e.message);
    }
  };
  return (
    <p className="row">
      <span>Deepcrawl worker (127.0.0.1:8080):</span>
      {running ? <span className="st-running">running (#{running.id})</span>
        : <>
            <span className={needed ? "st-failed" : "dim"}>not started{needed ? " — needed for this tab" : ""}</span>
            <button onClick={start}>Start worker</button>
          </>}
    </p>
  );
}

function RunForm({ cfg, runs, refresh }) {
  const [vals, setVals] = useState({});
  const [sel, setSel] = useState(null);
  const [error, setError] = useState("");
  const first = cfg.fields[0].name;

  const run = async (e) => {
    e.preventDefault();
    setError("");
    const params = Object.fromEntries(cfg.fields.map((f) => [f.name, (vals[f.name] || "").trim()]));
    try {
      const rec = await api(`/launch/${cfg.launch}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ params }),
      });
      setSel(rec.id);
      setVals({});
      refresh();
    } catch (e) {
      setError(e.message);
    }
  };

  const shown = sel ?? runs[0]?.id;
  return (
    <>
      <p className="dim">{cfg.blurb} Output: data/{cfg.folder}/.</p>
      <form onSubmit={run} className="row">
        {cfg.fields.map((f) => (
          <input key={f.name} className={f.grow ? "grow" : f.narrow ? "narrow" : ""} placeholder={f.placeholder}
                 value={vals[f.name] || ""} onChange={(e) => setVals({ ...vals, [f.name]: e.target.value })} />
        ))}
        <button type="submit" disabled={!(vals[first] || "").trim()}>{cfg.button}</button>
      </form>
      {error && <p className="error">{error}</p>}

      <h2>Runs</h2>
      <table>
        <thead><tr><th>#</th><th>Input</th><th>Status</th><th>Started</th><th>Ended</th></tr></thead>
        <tbody>
          {runs.map((p) => (
            <tr key={p.id} className={p.id === shown ? "active" : ""} onClick={() => setSel(p.id)}>
              <td>{p.id}</td>
              <td className="mono">
                {p.params?.[first]}
                {cfg.fields.slice(1).map((f) => (p.params?.[f.name] ? `  ${f.name} ${p.params[f.name]}` : "")).join("")}
              </td>
              <td className={`st-${p.status}`}>{p.status}</td>
              <td>{time(p.started)}</td>
              <td>{time(p.ended)}</td>
            </tr>
          ))}
          {runs.length === 0 && <tr><td colSpan="5" className="dim">No runs yet.</td></tr>}
        </tbody>
      </table>
      {shown != null && <Log id={shown} />}
    </>
  );
}
