import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";

// Tails data/procs/<id>.log through the hub, by byte offset.
export default function Log({ id }) {
  const [text, setText] = useState("");
  const [status, setStatus] = useState("");
  const next = useRef(0);
  const pre = useRef(null);

  useEffect(() => {
    setText("");
    next.current = 0;
    let stop = false;
    const tick = async () => {
      try {
        const r = await api(`/procs/${id}/log?from=${next.current}`);
        if (stop) return;
        if (r.text) setText((t) => t + r.text);
        next.current = r.next;
        setStatus(r.status);
        if (r.status === "running") setTimeout(tick, 1000);
      } catch {
        if (!stop) setTimeout(tick, 2000);
      }
    };
    tick();
    return () => { stop = true; };
  }, [id]);

  useEffect(() => {
    if (pre.current) pre.current.scrollTop = pre.current.scrollHeight;
  }, [text]);

  return (
    <>
      <h2>Output #{id} <span className={`st-${status}`}>{status}</span></h2>
      <pre className="log" ref={pre}>{text || " "}</pre>
    </>
  );
}
