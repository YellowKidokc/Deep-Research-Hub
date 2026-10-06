# Production Pipeline - Quick Start Guide

**Complete χ–δ–G Analysis with Auditable Outputs**

---

## What This Does

Turns a corpus of documents into:

✅ **χ(t)**: Coherence time series (Fruits of the Spirit)  
✅ **δ(t)**: Drift time series (decay rate + structural penalties)  
✅ **G(t)**: Grace time series (exogenous positive impulses)  

Plus:
- Excel workbook (multi-sheet with provenance)
- HTML report (plots + audit trail)
- Postgres-ready CSVs
- Phase portraits (χ vs δ state space)

---

## Installation

### 1. Prerequisites

```bash
pip install pandas matplotlib openpyxl pyyaml numpy
```

### 2. File Structure

```
theophysics_coherence_engine/
├── chi_delta_grace_pipeline.py      ✅ Main pipeline (from you!)
├── unified_coherence_scorer.py      ✅ Adapter to fruits_scorer.py
├── rubrics/                          ✅ YAML config (drift, grace)
│   ├── drift_rubric.yaml
│   └── grace_rubric.yaml
└── outputs/                          (created automatically)
```

---

## Usage

### Basic Run

```bash
cd D:\GitHub\crawl4ai\theophysics_coherence_engine

python chi_delta_grace_pipeline.py \
  --input_dir "D:\path\to\your\corpus" \
  --rubrics_dir "rubrics" \
  --out_dir "outputs/run_$(date +%Y%m%d)"
```

### With Date Parsing

If your files are named like `2025-01-15_document.md`:

```bash
python chi_delta_grace_pipeline.py \
  --input_dir "corpus" \
  --rubrics_dir "rubrics" \
  --out_dir "outputs" \
  --file_glob "*.md" \
  --timestamp_from filename
```

If dates are in the content:

```bash
python chi_delta_grace_pipeline.py \
  --input_dir "corpus" \
  --rubrics_dir "rubrics" \
  --out_dir "outputs" \
  --timestamp_from content \
  --timestamp_regex "\[(?P<ts>\d{4}-\d{2}-\d{2})\]"
```

---

## Outputs

### 1. Excel Workbook (`chi_delta_grace.xlsx`)

**Sheets:**

- **inputs**: Document manifest (paths, hashes, timestamps)
- **chi_series**: χ scores + fruit breakdown per document
- **drift_grace**: δ, G, change-points, z-scores
- **provenance**: Full audit trail (hashes, versions, parameters)

**Why this matters**: Anyone can verify your results by checking hashes.

---

### 2. HTML Report (`chi_delta_grace_report.html`)

Interactive report with:

- Headline stats (latest χ, δ, G)
- 4 plots:
  - χ(t) time series
  - δ(t) time series
  - G(t) time series
  - **Phase portrait** (χ vs δ) ← The "wow" visual
- Reproducibility notes

Open in browser to share with stakeholders.

---

### 3. Postgres Tables

**Files:**
- `table_inputs.csv`: Documents table
- `table_chi_delta_grace.csv`: Full time series
- `postgres_schema.sql`: CREATE TABLE statements

**Load into Postgres:**

```sql
-- Create schema
\i postgres_schema.sql

-- Load data
COPY inputs FROM '/path/to/table_inputs.csv' CSV HEADER;
COPY chi_delta_grace FROM '/path/to/table_chi_delta_grace.csv' CSV HEADER;

-- Query examples
SELECT timestamp, chi, drift_delta, grace_G 
FROM chi_delta_grace 
WHERE is_grace_spike = true
ORDER BY grace_z DESC
LIMIT 10;
```

---

## Interpretation Guide

### χ (Coherence)

- **> 0.7**: Structurally stable, long-term viable
- **0.5-0.7**: Repairable, needs attention
- **0.3-0.5**: Incoherent, at risk
- **< 0.3**: Entropy-amplifying, will collapse

### δ (Drift)

- **> 0.5**: High entropy pressure, actively degrading
- **0.2-0.5**: Moderate drift, needs correction
- **< 0.2**: Stable or improving

**Formula**: `δ = max(0, -dχ/dt) + structural_penalties`

### G (Grace)

- **|G| > 0.3**: Major exogenous impulse
- **|G| = 0.1-0.3**: Moderate grace event
- **|G| < 0.1**: On trend (no external factor)

**Formula**: `G = (dχ/dt - expected_recovery).clip(lower=0)`

---

## Phase Portrait (χ vs δ)

The scatter plot of χ (x-axis) vs δ (y-axis) shows the system's **state space trajectory**.

**Key regions:**

- **Top-left** (low χ, high δ): Death spiral
- **Bottom-right** (high χ, low δ): Stable flourishing
- **Sudden jumps**: Grace events (colored)
- **Slow drift down**: Decay without recovery

This is the **"one picture"** that tells the story.

---

## Example: USA 1970-2020

### Corpus Preparation

```
corpus/
├── 1980-01-01_state_of_union.md
├── 1985-01-01_state_of_union.md
├── 1990-01-01_state_of_union.md
...
```

Each file contains:
- Public documents from that year
- Policy statements
- Cultural indicators (articles, surveys)

### Run

```bash
python chi_delta_grace_pipeline.py \
  --input_dir "corpus_usa" \
  --rubrics_dir "rubrics" \
  --out_dir "outputs/usa_1970_2020"
```

### Expected Results

- **χ trend**: Declining from ~0.65 (1980) to ~0.45 (2020)
- **δ spikes**: 2008 (financial crisis), 2020 (COVID)
- **G events**: 1991 (Gulf War unity?), 2001 (post-9/11 spike?)

### Validation

Compare with known metrics:
- Trust indices (GSS)
- Marriage rates (CDC)
- Corruption (Transparency International)

If χ trend matches external data → system validated.

---

## Advanced: Bootstrap Validation

To test stability of results:

1. **Resample corpus** with replacement (bootstrap)
2. **Rerun pipeline** 1,000 times
3. **Check**:
   - Sign of χ trend consistent? (≥ 95%)
   - δ spikes in same years? (≥ 80%)
   - G events replicate? (≥ 70%)

If these hold → results are robust.

---

## Troubleshooting

### "Could not import UnifiedCoherenceScorer"

**Fix**: Make sure `unified_coherence_scorer.py` is in the same directory.

Or add to path:

```python
import sys
sys.path.insert(0, '/path/to/theophysics_coherence_engine')
```

### "Scorer did not return a usable chi value"

**Check**: Your documents might be too short.

Minimum: ~100 words per document.

### "No files matched *.md"

**Fix**: Check `--file_glob` parameter.

For .txt files: `--file_glob "*.txt"`

### Timestamps are all NaN

**Fix**: Either:
1. Name files with dates: `YYYY-MM-DD_name.md`
2. Use `--timestamp_from content` and provide regex

---

## Next Steps

### 1. Obsidian Integration

Each grace/drift event becomes a note:

```markdown
---
type: grace_event
timestamp: 2001-09-15
z_score: 2.3
chi_before: 0.45
chi_after: 0.52
---

# Grace Event: Post-9/11 Unity Spike

**Type**: Existential Threat → Paradoxical Coherence Gain

**Evidence**:
- Trust index jumped 15%
- Volunteer hours doubled
- Partisan polarization temporarily reduced

**Duration**: ~6 months before reverting to trend

**Source**: [[2001-09-15_corpus_doc]]
```

### 2. Comparative Analysis

Run on multiple entities:

```bash
for entity in USA China Rome_350AD Christianity_US; do
  python chi_delta_grace_pipeline.py \
    --input_dir "corpus/$entity" \
    --out_dir "outputs/$entity"
done
```

Then compare χ trends, δ patterns, G signatures.

### 3. Real-Time Dashboard

Postgres + Grafana:

```sql
-- Latest coherence
SELECT timestamp, chi FROM chi_delta_grace ORDER BY timestamp DESC LIMIT 1;

-- Drift alert
SELECT COUNT(*) FROM chi_delta_grace WHERE drift_delta > 0.5;
```

Set up alerts when δ spikes or χ drops below threshold.

---

## Citation

```
Theophysics Coherence Engine (2026)
χ–δ–G Pipeline for Societal Collapse Prediction
Operational, Auditable, Non-Circular Metrics
https://github.com/[your-repo]/theophysics_coherence_engine
```

---

## Support

Questions? Check:

1. `README.md` - Full system documentation
2. `SYSTEM_SUMMARY.md` - Implementation details
3. `rubrics/*.yaml` - Metric definitions

---

**Ready to run!** 🚀

The pipeline is production-ready with full auditability.

Test it on a small corpus first (~10-20 documents), verify the outputs look sane, then scale to your full dataset.
