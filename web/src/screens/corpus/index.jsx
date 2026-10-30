import { useEffect, useState } from "react";
import { api, post } from "../../api.js";

const CORPUS_URL = "http://127.0.0.1:8501";
const LAUNCH_ID = "corpus.search";

export default function CorpusScreen() {
  const [procs, setProcs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = async () => {
    try {
      const list = await api("/procs");
      setProcs(list);
      return list;
    } catch (e) {
      setError(e.message);
      return [];
    }
  };

  useEffect(() => {
    let mounted = true;

    const startIfNeeded = async () => {
      const list = await refresh();
      if (!mounted) return;

      const running = list.find(
        (p) => p.launch_id === LAUNCH_ID && p.status === "running"
      );

      if (!running) {
        try {
          await post(`/launch/${encodeURIComponent(LAUNCH_ID)}`);
          await refresh();
        } catch (e) {
          setError((err) => err || e.message);
        }
      }
      setLoading(false);
    };

    startIfNeeded();
    const t = setInterval(refresh, 3000);
    return () => {
      mounted = false;
      clearInterval(t);
    };
  }, []);

  const running = procs.find(
    (p) => p.launch_id === LAUNCH_ID && p.status === "running"
  );

  return (
    <div className="corpus-screen" style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div className="top" style={{ padding: "0.5rem 1rem", borderBottom: "1px solid #333" }}>
        <strong>YouTube Apologetics Corpus Search</strong>
        {loading && <span className="dim" style={{ marginLeft: "1rem" }}>Starting server…</span>}
        {!loading && running && <span className="dim" style={{ marginLeft: "1rem" }}>Running on {CORPUS_URL}</span>}
        {!loading && !running && (
          <span className="error" style={{ marginLeft: "1rem" }}>
            Server not running. <button onClick={() => post(`/launch/${encodeURIComponent(LAUNCH_ID)}`).then(refresh)}>Start</button>
          </span>
        )}
        {error && <span className="error" style={{ marginLeft: "1rem" }}>{error}</span>}
      </div>

      {running ? (
        <iframe
          src={CORPUS_URL}
          title="YouTube Apologetics Corpus Search"
          style={{ flex: 1, border: 0, width: "100%", minHeight: 0 }}
          allow="clipboard-read; clipboard-write"
        />
      ) : (
        <div style={{ flex: 1, padding: "2rem", color: "#888" }}>
          {loading ? "Waiting for the corpus server to start…" : "The corpus server is not running."}
        </div>
      )}
    </div>
  );
}
