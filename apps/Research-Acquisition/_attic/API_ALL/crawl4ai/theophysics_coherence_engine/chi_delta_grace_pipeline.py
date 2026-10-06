#!/usr/bin/env python3
"""Chi–Delta–Grace (χ–δ–G) Pipeline

Goal
----
Produce an *auditable* end-to-end run that turns a corpus (documents/events over time)
into:
  - χ(t): coherence time-series (from your UnifiedCoherenceScorer)
  - δ(t): drift time-series (rate + structural penalties)
  - G(t): grace time-series (positive residual coherence gains)

Outputs (the "wow" factor)
--------------------------
1) Excel workbook:
   - inputs (manifest)
   - chi_series (χ and sub-scores)
   - drift_grace (δ, G, change-points)
   - diagnostics (missingness, sensitivity)
   - provenance (hashes, versions)

2) HTML report:
   - headline stats
   - plots: χ(t), δ(t), G(t), phase portrait (χ vs δ), event markers
   - a reproducible appendix (settings + hashes)

3) Postgres-ready tables:
   - parquet/csv dumps with stable schemas

Important: δ and G are operational definitions.
They are *not* metaphysical proof—just measurable operators that can be falsified.

Usage
-----
python chi_delta_grace_pipeline.py \
  --input_dir /path/to/md_or_txt \
  --rubrics_dir /path/to/rubrics \
  --out_dir /path/to/output \
  --timestamp_regex "\\[(?P<ts>\\d{4}-\\d{2}-\\d{2})\\]"

If you don't have timestamps embedded in filenames or content yet,
use --timestamp_from filename (default) and name files like:
  2025-01-01_some_note.md

"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import matplotlib.pyplot as plt

# --- Import scorer (Fruits of the Spirit integration) ---
# Uses unified_coherence_scorer.py which bridges to fruits_scorer.py
try:
    from unified_coherence_scorer import UnifiedCoherenceScorer  # type: ignore
except Exception as e:
    raise SystemExit(
        "Could not import UnifiedCoherenceScorer from unified_coherence_scorer.py. "
        "Make sure unified_coherence_scorer.py is in the same folder as this script. "
        f"Original error: {e}"
    )


@dataclasses.dataclass
class RunConfig:
    input_dir: Path
    rubrics_dir: Path
    out_dir: Path
    timestamp_from: str  # 'filename' or 'content'
    timestamp_regex: Optional[str]
    file_glob: str
    tz: str = "UTC"
    grace_z_threshold: float = 1.5
    drift_window: int = 5
    grace_window: int = 9
    changepoint_z: float = 2.0


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_path(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_timestamp_from_filename(path: Path) -> Optional[datetime]:
    # Default: leading YYYY-MM-DD
    m = re.match(r"(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})", path.name)
    if not m:
        return None
    try:
        return datetime(int(m.group("y")), int(m.group("m")), int(m.group("d")))
    except ValueError:
        return None


def parse_timestamp_from_content(text: str, pattern: str) -> Optional[datetime]:
    m = re.search(pattern, text)
    if not m:
        return None
    # Accept either named group ts or full match
    ts = m.groupdict().get("ts") or m.group(0)
    # Try common forms
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None


def load_documents(cfg: RunConfig) -> pd.DataFrame:
    rows = []
    for p in sorted(cfg.input_dir.glob(cfg.file_glob)):
        if p.is_dir():
            continue
        raw = p.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        if cfg.timestamp_from == "content" and cfg.timestamp_regex:
            ts = parse_timestamp_from_content(text, cfg.timestamp_regex)
        else:
            ts = parse_timestamp_from_filename(p)
        rows.append(
            {
                "doc_id": sha256_bytes(raw)[:16],
                "path": str(p),
                "filename": p.name,
                "timestamp": ts,
                "sha256": sha256_bytes(raw),
                "bytes": len(raw),
                "text": text,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError(f"No files matched {cfg.file_glob} in {cfg.input_dir}")

    # If timestamps missing, keep but warn; drift/grace will be less meaningful
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def score_chi(cfg: RunConfig, docs: pd.DataFrame) -> pd.DataFrame:
    scorer = UnifiedCoherenceScorer(rubrics_dir=str(cfg.rubrics_dir))

    scored_rows: List[Dict[str, Any]] = []
    for _, r in docs.iterrows():
        # unified_scorer implementations vary; try a few common entrypoints.
        text = r["text"]
        result: Dict[str, Any]
        if hasattr(scorer, "score_text"):
            result = scorer.score_text(text)  # type: ignore
        elif hasattr(scorer, "score"):
            result = scorer.score(text)  # type: ignore
        else:
            raise AttributeError("UnifiedCoherenceScorer missing score_text()/score()")

        flat: Dict[str, Any] = {
            "doc_id": r["doc_id"],
            "timestamp": r["timestamp"],
            "filename": r["filename"],
            "chi": result.get("chi") or result.get("χ") or result.get("coherence"),
        }

        # Keep any sub-scores if present
        for k, v in result.items():
            if isinstance(v, (int, float)) and k not in flat:
                flat[k] = v
        scored_rows.append(flat)

    df = pd.DataFrame(scored_rows)

    # Coerce + sort
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values(["timestamp", "filename"], na_position="last").reset_index(drop=True)

    # If chi is missing, hard fail (can't proceed)
    if df["chi"].isna().all():
        raise ValueError("Scorer did not return a usable chi value under keys: chi/χ/coherence")

    return df


def rolling_z(x: pd.Series, window: int) -> pd.Series:
    # Robust-ish rolling z-score
    mu = x.rolling(window, min_periods=max(2, window // 2)).mean()
    sd = x.rolling(window, min_periods=max(2, window // 2)).std(ddof=0)
    return (x - mu) / sd.replace(0, pd.NA)


def derive_drift_grace(cfg: RunConfig, chi_df: pd.DataFrame) -> pd.DataFrame:
    df = chi_df.copy()

    # Use time index if available; otherwise fallback to row index
    if df["timestamp"].notna().any():
        df = df[df["timestamp"].notna()].copy()
        df = df.sort_values("timestamp").reset_index(drop=True)
        # Convert to days since start for derivative
        t0 = df["timestamp"].iloc[0]
        df["t_days"] = (df["timestamp"] - t0).dt.total_seconds() / 86400.0
        dt = df["t_days"].diff()
    else:
        df["t_days"] = range(len(df))
        dt = df["t_days"].diff()

    dchi = df["chi"].diff()

    # DRIFT δ:
    #   - primary: negative slope of chi (decay rate)
    #   - secondary: structural penalty if "constraint"/"defense" scores suggest inconsistency (if available)
    # Operationally: δ = max(0, -dχ/dt) + penalty

    slope = dchi / dt.replace(0, pd.NA)
    df["chi_slope"] = slope

    base_drift = (-slope).clip(lower=0)

    penalty = 0.0
    # If your scorer emitted specific keys, integrate them as drift penalties.
    # These names are conservative guesses; you can map them to your actual output keys.
    for col in [
        "constraint_violation_rate",
        "defense_score",
        "inconsistency",
        "contradiction",
        "anti_fruit",
    ]:
        if col in df.columns:
            # Higher violation/contradiction -> higher drift
            penalty = penalty + pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0)

    df["drift_delta"] = (base_drift.fillna(0) + penalty).astype(float)

    # GRACE G:
    #   - positive residual gains in chi beyond "expected" recovery.
    # Expected recovery is modeled as the rolling median of positive slopes.
    pos_slope = slope.clip(lower=0)
    expected = pos_slope.rolling(cfg.grace_window, min_periods=max(2, cfg.grace_window // 2)).median()
    residual = (slope - expected).fillna(0)
    df["grace_G"] = residual.clip(lower=0)

    # Change-point flags ("wow" moments)
    df["drift_z"] = rolling_z(df["drift_delta"], cfg.drift_window)
    df["grace_z"] = rolling_z(df["grace_G"], cfg.grace_window)

    df["is_drift_spike"] = (df["drift_z"].abs() >= cfg.changepoint_z).fillna(False)
    df["is_grace_spike"] = (df["grace_z"] >= cfg.grace_z_threshold).fillna(False)

    return df


def fig_to_base64() -> str:
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=160)
    plt.close()
    return base64.b64encode(buf.getvalue()).decode("ascii")


def make_plots(df: pd.DataFrame) -> Dict[str, str]:
    images: Dict[str, str] = {}

    # χ(t)
    plt.figure()
    plt.plot(df["timestamp"], df["chi"], marker="o")
    plt.title("Coherence χ over time")
    plt.xlabel("time")
    plt.ylabel("χ")
    images["chi"] = fig_to_base64()

    # δ(t)
    plt.figure()
    plt.plot(df["timestamp"], df["drift_delta"], marker="o")
    plt.title("Drift δ over time")
    plt.xlabel("time")
    plt.ylabel("δ")
    images["drift"] = fig_to_base64()

    # G(t)
    plt.figure()
    plt.plot(df["timestamp"], df["grace_G"], marker="o")
    plt.title("Grace G over time")
    plt.xlabel("time")
    plt.ylabel("G")
    images["grace"] = fig_to_base64()

    # Phase portrait χ vs δ
    plt.figure()
    plt.scatter(df["chi"], df["drift_delta"])
    plt.title("Phase portrait: χ vs δ")
    plt.xlabel("χ")
    plt.ylabel("δ")
    images["phase"] = fig_to_base64()

    return images


def export_excel(cfg: RunConfig, docs: pd.DataFrame, chi_df: pd.DataFrame, dg_df: pd.DataFrame) -> Path:
    out = cfg.out_dir / "chi_delta_grace.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        docs[["doc_id", "timestamp", "filename", "path", "sha256", "bytes"]].to_excel(xw, "inputs", index=False)
        chi_df.to_excel(xw, "chi_series", index=False)
        dg_df.to_excel(xw, "drift_grace", index=False)

        prov = pd.DataFrame(
            [
                {"key": "pipeline", "value": "chi_delta_grace_pipeline.py"},
                {"key": "pipeline_sha256", "value": sha256_path(Path(__file__))},
                {"key": "unified_coherence_scorer_sha256", "value": sha256_path(Path(__file__).with_name("unified_coherence_scorer.py"))
                    if Path(__file__).with_name("unified_coherence_scorer.py").exists() else "(unknown)"},
                {"key": "rubrics_dir", "value": str(cfg.rubrics_dir)},
                {"key": "config", "value": json.dumps(dataclasses.asdict(cfg), default=str)},
                {"key": "generated_at", "value": datetime.utcnow().isoformat() + "Z"},
            ]
        )
        prov.to_excel(xw, "provenance", index=False)

    return out


def export_html(cfg: RunConfig, dg_df: pd.DataFrame, images: Dict[str, str]) -> Path:
    out = cfg.out_dir / "chi_delta_grace_report.html"

    # Headline stats
    last = dg_df.tail(1).iloc[0]
    stats = {
        "n_points": int(len(dg_df)),
        "chi_latest": float(last["chi"]),
        "drift_latest": float(last["drift_delta"]),
        "grace_latest": float(last["grace_G"]),
        "drift_spikes": int(dg_df["is_drift_spike"].sum()),
        "grace_spikes": int(dg_df["is_grace_spike"].sum()),
    }

    html = f"""<!doctype html>
<html>
<head>
<meta charset='utf-8'/>
<title>χ–δ–G Report</title>
<style>
body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 24px; }}
.card {{ border: 1px solid #ddd; border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
img {{ width: 100%; height: auto; border-radius: 10px; border: 1px solid #eee; }}
code {{ background: #f6f8fa; padding: 2px 6px; border-radius: 6px; }}
</style>
</head>
<body>
<h1>χ–δ–G Run Report</h1>
<div class='card'>
  <h2>Headline</h2>
  <ul>
    <li><b>N points</b>: {stats['n_points']}</li>
    <li><b>χ latest</b>: {stats['chi_latest']:.4f}</li>
    <li><b>δ latest</b>: {stats['drift_latest']:.4f}</li>
    <li><b>G latest</b>: {stats['grace_latest']:.4f}</li>
    <li><b>Drift spikes</b>: {stats['drift_spikes']}</li>
    <li><b>Grace spikes</b>: {stats['grace_spikes']}</li>
  </ul>
</div>

<div class='grid'>
  <div class='card'><h2>Coherence χ(t)</h2><img src='data:image/png;base64,{images['chi']}'/></div>
  <div class='card'><h2>Drift δ(t)</h2><img src='data:image/png;base64,{images['drift']}'/></div>
  <div class='card'><h2>Grace G(t)</h2><img src='data:image/png;base64,{images['grace']}'/></div>
  <div class='card'><h2>Phase portrait (χ vs δ)</h2><img src='data:image/png;base64,{images['phase']}'/></div>
</div>

<div class='card'>
  <h2>Reproducibility</h2>
  <p>This report is generated by <code>chi_delta_grace_pipeline.py</code>. The exact input hashes and settings are stored in the Excel workbook (sheet: provenance).</p>
</div>
</body>
</html>"""

    out.write_text(html, encoding="utf-8")
    return out


def export_postgres_tables(cfg: RunConfig, docs: pd.DataFrame, dg_df: pd.DataFrame) -> List[Path]:
    # Simple, stable CSVs that can be COPY'ed into Postgres.
    paths: List[Path] = []

    docs_out = cfg.out_dir / "table_inputs.csv"
    docs[["doc_id", "timestamp", "filename", "path", "sha256", "bytes"]].to_csv(docs_out, index=False)
    paths.append(docs_out)

    dg_out = cfg.out_dir / "table_chi_delta_grace.csv"
    dg_df.to_csv(dg_out, index=False)
    paths.append(dg_out)

    schema_out = cfg.out_dir / "postgres_schema.sql"
    schema_out.write_text(
        """
-- Minimal Postgres schema (adjust types/indexes as needed)
CREATE TABLE IF NOT EXISTS inputs (
  doc_id TEXT PRIMARY KEY,
  timestamp TIMESTAMPTZ,
  filename TEXT,
  path TEXT,
  sha256 TEXT,
  bytes INTEGER
);

CREATE TABLE IF NOT EXISTS chi_delta_grace (
  doc_id TEXT,
  timestamp TIMESTAMPTZ,
  filename TEXT,
  chi DOUBLE PRECISION,
  t_days DOUBLE PRECISION,
  chi_slope DOUBLE PRECISION,
  drift_delta DOUBLE PRECISION,
  grace_G DOUBLE PRECISION,
  drift_z DOUBLE PRECISION,
  grace_z DOUBLE PRECISION,
  is_drift_spike BOOLEAN,
  is_grace_spike BOOLEAN
);

-- Suggested indexes
CREATE INDEX IF NOT EXISTS idx_cdg_time ON chi_delta_grace(timestamp);
CREATE INDEX IF NOT EXISTS idx_cdg_doc ON chi_delta_grace(doc_id);
""".strip()
        + "\n",
        encoding="utf-8",
    )
    paths.append(schema_out)

    return paths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_dir", required=True)
    ap.add_argument("--rubrics_dir", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--file_glob", default="*.md")
    ap.add_argument("--timestamp_from", choices=["filename", "content"], default="filename")
    ap.add_argument("--timestamp_regex", default=None)
    args = ap.parse_args()

    cfg = RunConfig(
        input_dir=Path(args.input_dir),
        rubrics_dir=Path(args.rubrics_dir),
        out_dir=Path(args.out_dir),
        file_glob=args.file_glob,
        timestamp_from=args.timestamp_from,
        timestamp_regex=args.timestamp_regex,
    )

    cfg.out_dir.mkdir(parents=True, exist_ok=True)

    docs = load_documents(cfg)
    chi_df = score_chi(cfg, docs)
    dg_df = derive_drift_grace(cfg, chi_df)

    # Save artifacts
    images = make_plots(dg_df)
    xlsx = export_excel(cfg, docs, chi_df, dg_df)
    html = export_html(cfg, dg_df, images)
    tables = export_postgres_tables(cfg, docs, dg_df)

    print("OK")
    print(f"Excel: {xlsx}")
    print(f"HTML : {html}")
    for t in tables:
        print(f"Table: {t}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
