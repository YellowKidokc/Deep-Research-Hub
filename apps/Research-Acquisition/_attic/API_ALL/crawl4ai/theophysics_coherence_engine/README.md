# Theophysics Coherence Engine

**Operational, auditable, non-circular prediction of societal collapse.**

---

## What This Does

Measures structural invariants that predict whether ANY system (nation, religion, institution) will **survive or collapse**.

### Core Metrics

1. **χ (coherence)**: Structural health via "Fruits of the Spirit"  
   - 12 operational metrics (grace, hope, patience, etc.)
   - Each measures survival capacity, not emotions
   - Score range: 0-1 (normalized from -12 to +12)

2. **δ (drift)**: Internal decay rate  
   - δ₁: Misalignment (claimed purpose vs actual behavior)
   - δ₂: Entropy pressure (losing coherence despite efforts)
   - Computed from: text + behavior + time series

3. **G (grace)**: Exogenous impulses  
   - **Residual analysis**: G = χ_observed - χ_predicted
   - Classified by signature (resource windfall, existential threat, revival)
   - Non-circular: uses published model, anyone can recompute

---

## Key Design Principles

✅ **Operational**: Computable from data  
✅ **Auditable**: Full provenance, hashed inputs  
✅ **Non-circular**: No "grace looks like grace"  
✅ **Domain-agnostic**: Works on religions, nations, institutions  

---

## Architecture

```
theophysics_coherence_engine/
├── core/
│   ├── entities.py          # Entity, ClaimSet, Observations, ModelSpec
│   ├── drift/
│   │   └── drift_scorer.py  # δ₁ (misalignment) + δ₂ (pressure)
│   └── grace/
│       └── grace_scorer.py  # G (residual detection)
├── rubrics/
│   ├── drift_rubric.yaml    # Claim→metric mappings
│   └── grace_rubric.yaml    # Event taxonomy
├── outputs/
│   └── manifests/           # Run manifests (JSON)
└── unified_scorer.py         # Main entry point
```

---

## Usage

### Minimal Example

```python
from unified_scorer import CoherenceEngine
from core import Entity, ClaimSet, Observations

# Create entity
entity = Entity(
    entity_id="usa_test",
    entity_type="nation",
    name="United States (Test)",
    description="Minimal test case"
)

# Add claims (what entity says it does)
entity.claims = ClaimSet(
    entity_id="usa_test",
    source_texts=["constitution.txt"],
    extracted_claims=["equal protection", "promote general welfare"],
    claim_categories={"constitutional": ["equal protection"]}
)

# Add observations (what entity actually does)
entity.observations = Observations(
    entity_id="usa_test",
    time_series={
        "corruption_index": [(1980, 75), (1990, 73), (2000, 76), (2010, 71), (2020, 67)],
        "trust_index": [(1980, 0.45), (1990, 0.40), (2000, 0.35), (2010, 0.32), (2020, 0.29)]
    },
    events=[],
    data_sources={"corruption_index": "Transparency International"}
)

# Run engine
engine = CoherenceEngine(model_version="minimal_v1")
result = engine.run(entity, use_minimal=True)

# Results
print(f"χ trend: {result.diagnostics['chi_trend']:.4f}")
print(f"Average drift: {result.diagnostics['drift_mean']:.3f}")
print(f"Grace events: {result.diagnostics['grace_events_count']}")

# Manifest saved to: outputs/manifests/manifest_{run_id}.json
```

---

## Auditability

Every run produces a **manifest** containing:

- Input hashes (claims, observations, rubrics)
- Model spec (version, methods, parameters)
- Full outputs (χ, δ, G time series)
- Diagnostics and warnings
- Timestamp and runtime

Anyone can:
1. Load the manifest
2. Rerun with same inputs
3. Verify identical outputs

---

## Data Requirements

### For Nations

**Claims** (from founding documents):
- Constitutional principles
- Stated values
- Legal promises

**Observations** (measurable):
- Corruption indices (Transparency International)
- Trust metrics (General Social Survey)
- Rule of law (World Justice Project)
- Poverty, life expectancy, etc.

### For Religions

**Claims** (from doctrine):
- Moral commands
- Community standards
- Theological principles

**Observations** (measurable):
- Charitable giving
- Divorce rates
- Volunteer hours
- Retention rates
- Scandal frequency

---

## Rubric System

### drift_rubric.yaml

Maps claims to metrics:

```yaml
nation:
  constitutional_claims:
    - claim: "equal protection under law"
      metrics:
        - name: "corruption_index"
          expected: "> 70"
          weight: 1.0
```

### grace_rubric.yaml

Defines event types:

```yaml
event_types:
  revival:
    signatures:
      - type: "behavioral"
        indicators:
          - "trust index sudden jump"
          - "fertility rebound"
          - "crime rate drop"
```

---

## Interpretation

### Coherence (χ)

- **> 0.7**: Stable, long-term viable
- **0.5-0.7**: Repairable
- **0.3-0.5**: Incoherent
- **< 0.3**: Entropy-amplifying, will collapse

### Drift (δ)

- **> 0.5**: High entropy pressure, degrading
- **0.2-0.5**: Moderate drift
- **< 0.2**: Stable or improving

### Grace (G)

- **|G| > 0.3**: Major exogenous impulse
- **|G| = 0.1-0.3**: Moderate grace event
- **|G| < 0.1**: On trend, no external factor

---

## Extending the System

### Add New Entity Types

1. Define claim structure in `drift_rubric.yaml`
2. Map claims to measurable metrics
3. Specify data sources

### Add New Grace Types

1. Define signature in `grace_rubric.yaml`
2. Specify indicators
3. Add attribution rules

### Upgrade Prediction Models

Replace minimal versions:
- δ: VAR, diff-in-diff, hierarchical Bayesian
- G: CUSUM, Bayesian changepoint, ruptures

---

## Citation

If using this system, cite:

```
Theophysics Coherence Engine (2026)
Operational prediction of societal collapse via structural invariants.
https://github.com/[your-repo]/theophysics_coherence_engine
```

---

## License

[Your license here]

---

## Contact

For questions about methodology or implementation:
[Your contact info]
