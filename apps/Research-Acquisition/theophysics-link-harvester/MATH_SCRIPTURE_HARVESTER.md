# Mathematical Scripture / Theology Harvester

This is the provenance-first discovery lane for mathematical material involving God, Jesus Christ, Scripture, Christian doctrine, moral structure, and proposed physics bridges.

## What it searches

- Crossref scholarly metadata
- Semantic Scholar paper metadata
- arXiv open-paper metadata
- Optional local SearXNG web discovery (`--providers searxng`)

It does not bypass paywalls or bulk-copy arbitrary webpages. The first pass saves metadata, abstracts supplied by scholarly indexes, identifiers, URLs, query provenance, and SHA-256 content hashes.

## Run safely

Dry run—shows every query without using the network:

```powershell
python math_scripture_harvester.py
```

Self-test:

```powershell
python math_scripture_harvester.py --self-test
```

Small live pilot:

```powershell
python math_scripture_harvester.py --run --providers crossref,arxiv --max-queries 3 --max-results 5
```

Full configured discovery:

```powershell
python math_scripture_harvester.py --run --providers crossref,arxiv --max-results 10 --delay 1
```

Optional local web discovery through SearXNG:

```powershell
python math_scripture_harvester.py --run --providers searxng --max-results 10
```

Semantic Scholar is supported with `--providers semantic_scholar`, but its
unauthenticated endpoint may return HTTP 429. It is not in the default launcher.

Optional local Ollama advisory screening:

```powershell
python math_scripture_harvester.py --run --providers crossref --lanes jesus_christ --max-queries 2 --max-results 5 --ollama --ollama-model qwen3:4b-instruct --ollama-max-items 10
```

Ollama output is stored separately in `ollama_assessment`. It never overwrites
the deterministic evidence grade, claim lane, or candidate status.

## Outputs

- `output_math_scripture/candidates.jsonl` — machine-readable candidate ledger
- `output_math_scripture/harvest_report.md` — human screening report
- `output_math_scripture/run_manifest.json` — provider, query, error, and run receipt

Every result remains `CANDIDATE`. Mathematical keywords, citation counts, or local-AI judgments never promote a claim to established evidence.

## Evidence grades

- **A:** strong metadata receipt, abstract, DOI, and high intersection relevance
- **B:** identifiable scholarly work with meaningful intersection relevance
- **C:** plausible bridge candidate requiring close reading
- **D:** background/noisy result

Grades concern acquisition quality and relevance, not truth.

## Important boundary

The script distinguishes formal mathematics, empirical work, theological bridge material, challenges, and background. It does not call an analogy an isomorphism, a mathematical model a physical derivation, or a theological interpretation an empirical result.
