"""Deep Research queue: run every job file in a folder, one folder per job's output.

    python drh_queue.py --jobs ../../../../data/jobs --out ../../../../data/deep_research
    python drh_queue.py --jobs ... --out ... --parallel 3
    python drh_queue.py --jobs ... --out ... --dry-run          # validate and list, run nothing
    python drh_queue.py --jobs ... --out ... --retry-failed     # put failed/ jobs back in the queue

Jobs:   <jobs>/<name>.yaml, each merged over <jobs>/_defaults.yaml.
Claim:  a job is moved to <jobs>/running/ before it starts, then to done/ or failed/.
Output: <out>/<name>/<YYYYmmdd-HHMMSS>/
          report.md      the report
          receipt.json   what was read, kept and dropped (gpt_researcher.receipts)
          sources.json   source URLs used and every URL visited
          run.json       the merged job, status, timings, model, costs
          events.jsonl   every streamed log event, timestamped
Ledger: <out>/_ledger/<chapter or name>.jsonl, one line per run. visited_urls_from
        names a ledger; its URLs are passed in so the next run goes wider.

Replaces research_queue.txt + continuous_runner.py.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
import re
import shutil
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent

JOB_TYPES = {"standard", "cold_derive", "prior_art", "hybrid_rule"}
BUILT_TYPES = {"standard"}            # the others arrive with their templates (step 3)
SOURCES = {"web", "local", "hybrid"}
REPORT_TYPES = {"research_report", "detailed_report", "resource_report", "outline_report"}
FIELDS = {
    "query": str, "chapter": str, "job_type": str, "report_source": str, "report_type": str,
    "doc_path": str, "retrievers": list, "model": str, "custom_prompt": str, "tone": str,
    "overrides": dict, "visited_urls_from": (str, list), "meta": dict,
    "timeout_minutes": (int, float),
}
DEFAULTS_EXAMPLE = HERE / "jobs_defaults.example.yaml"


# ------------------------------------------------------------------ setup
def apply_env_file(path: Path) -> None:
    """KEY=VALUE lines; anything already in the environment wins."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = (p.strip() for p in line.split("=", 1))
            if k and v:
                os.environ.setdefault(k, v)


def load_yaml(path: Path) -> dict:
    import yaml
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: expected a mapping at the top level")
    return data


def merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def validate(name: str, job: dict) -> list[str]:
    errs = []
    for k, v in job.items():
        if k not in FIELDS:
            errs.append(f"unknown field {k!r}")
        elif v is not None and not isinstance(v, FIELDS[k]):
            errs.append(f"{k} should be {FIELDS[k]}")
    if not str(job.get("query") or "").strip():
        errs.append("query is required")
    jt = job.get("job_type", "standard")
    if jt not in JOB_TYPES:
        errs.append(f"job_type must be one of {sorted(JOB_TYPES)}")
    elif jt not in BUILT_TYPES:
        errs.append(f"job_type {jt!r}: its template is not built yet (step 3); use standard")
    src = job.get("report_source", "web")
    if src not in SOURCES:
        errs.append(f"report_source must be one of {sorted(SOURCES)}")
    if src in ("local", "hybrid"):
        dp = job.get("doc_path")
        if not dp:
            errs.append(f"report_source {src} needs doc_path")
        elif not Path(dp).is_dir():
            errs.append(f"doc_path is not a folder: {dp}")
    if job.get("report_type", "research_report") not in REPORT_TYPES:
        errs.append(f"report_type must be one of {sorted(REPORT_TYPES)}")
    if job.get("model") and ":" not in job["model"]:
        errs.append("model must be provider:model, e.g. deepseek:deepseek-chat")
    if job.get("timeout_minutes") is not None and not job["timeout_minutes"] > 0:
        errs.append("timeout_minutes must be above 0")
    if job.get("chapter") and not re.fullmatch(r"AX_GI_\d\d", job["chapter"]):
        errs.append("chapter must look like AX_GI_01")
    return [f"{name}: {e}" for e in errs]


def ledger_key(name: str, job: dict) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", job.get("chapter") or name)


def read_ledger_urls(ledger_dir: Path, keys) -> set[str]:
    urls: set[str] = set()
    for key in [keys] if isinstance(keys, str) else (keys or []):
        p = ledger_dir / f"{re.sub(r'[^A-Za-z0-9_.-]+', '_', key)}.jsonl"
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    urls.update(json.loads(line).get("visited_urls", []))
    return urls


class EventLog:
    """Stands in for the websocket: every streamed event is kept, timestamped."""

    def __init__(self, path: Path):
        self.f = open(path, "a", encoding="utf-8")

    async def send_json(self, data):
        self.f.write(json.dumps({"t": round(time.time(), 3), **data}, ensure_ascii=False, default=str) + "\n")
        self.f.flush()

    def close(self):
        self.f.close()


# -------------------------------------------------------------------- run
async def run_job(name: str, job: dict, jobs: Path, out: Path, claimed: Path) -> bool:
    from gpt_researcher import GPTResearcher

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = out / name / stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    events = EventLog(run_dir / "events.jsonl")
    ledger_dir = out / "_ledger"
    started = time.time()
    record = {"job_name": name, "job": job, "status": "running",
              "started": dt.datetime.now().isoformat(timespec="seconds")}
    researcher = None
    print(f"[start] {name}: {job['query'][:90]}", flush=True)
    try:
        seed_urls = read_ledger_urls(ledger_dir, job.get("visited_urls_from"))
        headers = {"retrievers": ",".join(job["retrievers"])} if job.get("retrievers") else {}
        researcher = GPTResearcher(
            query=job["query"],
            report_type=job.get("report_type", "research_report"),
            report_source=job.get("report_source", "web"),
            doc_path=job.get("doc_path"),
            config_overrides=job.get("overrides"),
            headers=headers,
            visited_urls=set(seed_urls),
            websocket=events,
            verbose=True,
        )
        if job.get("model"):
            cfg = researcher.cfg
            cfg.fast_llm = cfg.smart_llm = cfg.strategic_llm = job["model"]
            cfg._set_llm_attributes()
        record["model"] = f"{researcher.cfg.smart_llm_provider}:{researcher.cfg.smart_llm_model}"
        record["retrievers"] = [r.__name__ for r in researcher.retrievers]
        record["seeded_visited_urls"] = len(seed_urls)

        async def work():
            await researcher.conduct_research()
            return await researcher.write_report(custom_prompt=job.get("custom_prompt") or "")

        # A dead provider makes GPT Researcher retry for a long time; one job
        # must not hold up the queue.
        limit = float(job.get("timeout_minutes") or 60) * 60
        try:
            report = await asyncio.wait_for(work(), timeout=limit)
        except asyncio.TimeoutError:
            raise TimeoutError(f"timed out after {limit / 60:g} min") from None
        (run_dir / "report.md").write_text(str(report), encoding="utf-8")
        record["status"] = "done"
    except Exception as e:
        record["status"] = "failed"
        record["error"] = f"{type(e).__name__}: {e}"
        (run_dir / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
    finally:
        events.close()

    record["ended"] = dt.datetime.now().isoformat(timespec="seconds")
    record["seconds"] = round(time.time() - started, 1)
    summary = None
    if researcher is not None:
        researcher.write_read_receipt(str(run_dir / "receipt.json"))
        summary = researcher.get_read_receipt()["summary"]
        visited = sorted(researcher.visited_urls)
        (run_dir / "sources.json").write_text(json.dumps({
            "source_urls": researcher.get_source_urls(), "visited_urls": visited}, indent=2), encoding="utf-8")
        record["costs"] = researcher.get_costs()
        ledger_dir.mkdir(parents=True, exist_ok=True)
        with open(ledger_dir / f"{ledger_key(name, job)}.jsonl", "a", encoding="utf-8") as lf:
            lf.write(json.dumps({
                "time": record["ended"], "job": name, "status": record["status"],
                "query": job["query"], "run_dir": str(run_dir), "visited_urls": visited,
                "receipt": summary}, ensure_ascii=False) + "\n")
    record["receipt_summary"] = summary
    (run_dir / "run.json").write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    dest = jobs / ("done" if record["status"] == "done" else "failed")
    dest.mkdir(exist_ok=True)
    shutil.move(str(claimed), str(dest / f"{stamp}_{name}.yaml"))
    tail = f"{summary['files_loaded']} files, {summary['chunks_returned']} chunks used" if summary else ""
    print(f"[{record['status']}] {name} in {record['seconds']}s {tail} -> {run_dir}"
          + (f"\n        {record['error']}" if record.get("error") else ""), flush=True)
    return record["status"] == "done"


async def main_async(args) -> int:
    jobs, out = Path(args.jobs).resolve(), Path(args.out).resolve()
    jobs.mkdir(parents=True, exist_ok=True)
    defaults_path = jobs / "_defaults.yaml"
    if not defaults_path.exists() and DEFAULTS_EXAMPLE.exists():
        shutil.copy(DEFAULTS_EXAMPLE, defaults_path)
        print(f"created {defaults_path} from {DEFAULTS_EXAMPLE.name}")
    defaults = load_yaml(defaults_path) if defaults_path.exists() else {}

    if args.retry_failed:
        moved = 0
        for p in sorted((jobs / "failed").glob("*.yaml")) if (jobs / "failed").is_dir() else []:
            name = re.sub(r"^\d{8}-\d{6}_", "", p.name)   # drop the run stamp
            if (jobs / name).exists():
                print(f"  ! {name} is already pending; left {p.name} in failed/")
                continue
            p.rename(jobs / name)
            moved += 1
        print(f"{moved} failed job(s) moved back to the queue")
        return 0

    stale = sorted((jobs / "running").glob("*.yaml")) if (jobs / "running").is_dir() else []
    if stale:
        print(f"note: {len(stale)} job(s) in running/ from an earlier run that did not finish; "
              "move them back to rerun: " + ", ".join(p.name for p in stale))

    pending = sorted(p for p in jobs.glob("*.yaml") if not p.name.startswith("_"))
    if args.only:
        pending = [p for p in pending if p.stem in set(args.only)]
    planned, errors = [], []
    for p in pending:
        try:
            job = merge(defaults, load_yaml(p))
        except Exception as e:
            errors.append(f"{p.stem}: {e}")
            continue
        errs = validate(p.stem, job)
        errors.extend(errs)
        if not errs:
            planned.append((p, job))

    print(f"{len(pending)} job file(s): {len(planned)} ready, {len(errors)} problem(s)")
    for e in errors:
        print(f"  ! {e}")
    for p, job in planned:
        print(f"  - {p.stem}: [{job.get('job_type', 'standard')}/{job.get('report_source', 'web')}] {job['query'][:80]}")
    if args.dry_run or not planned:
        return 1 if errors else 0

    sem = asyncio.Semaphore(max(1, args.parallel))
    (jobs / "running").mkdir(exist_ok=True)

    async def one(p: Path, job: dict):
        async with sem:
            claimed = jobs / "running" / p.name
            try:
                p.rename(claimed)       # claim: another runner can't take it now
            except OSError:
                print(f"[skip] {p.stem}: taken by another runner")
                return None
            return await run_job(p.stem, job, jobs, out, claimed)

    results = await asyncio.gather(*(one(p, j) for p, j in planned))
    ok = sum(1 for r in results if r)
    failed = sum(1 for r in results if r is False)
    print(f"queue finished: {ok} done, {failed} failed, {len(errors)} not run (problems above)")
    return 0 if not failed and not errors else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jobs", required=True, help="folder of <name>.yaml job files")
    ap.add_argument("--out", required=True, help="output root (one folder per job)")
    ap.add_argument("--parallel", type=int, default=1, help="jobs at once (default 1)")
    ap.add_argument("--only", nargs="*", help="run just these job names")
    ap.add_argument("--dry-run", action="store_true", help="validate and list; run nothing")
    ap.add_argument("--retry-failed", action="store_true", help="move failed/ jobs back into the queue, then stop")
    args = ap.parse_args()
    # Providers and research profile before gpt_researcher is imported: some
    # of its modules read the environment at import time.
    apply_env_file(HERE / "PROVIDERS.env")
    apply_env_file(HERE / "RESEARCH_PROFILE.env")
    sys.path.insert(0, str(HERE))
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
