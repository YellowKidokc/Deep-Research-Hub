# Page 3: The Nine Domains of Social Coherence

### The Measurement Problem

To measure social coherence (χ), we need component variables that:

1. **Span the space** - Cover the full range of pro-social behavior
2. **Are orthogonal** - Measure distinct phenomena, not redundant signals
3. **Are stable** - Definitions do not drift with cultural fashion
4. **Are measurable** - Empirical proxies exist across the time period

Modern sociological categories fail criterion 3. Terms like "well-being," "social capital," and "civic health" shift meaning decade to decade. A 1950 survey and a 2020 survey using the same words measure different things.

### The Solution: An Ancient Taxonomy

We adopt a taxonomy that has remained semantically stable for two millennia: the nine attributes listed in Galatians 5:22-23, traditionally called the "Fruits of the Spirit."

**This is not a theological claim. It is a methodological choice.**

These categories were defined in Greek with precise meanings that have not drifted. They decompose human behavioral coherence into distinct, measurable components. They predate modern ideology and are therefore immune to left-right contamination.

We treat them as **coordinate axes**, not moral prescriptions.

### The Nine Components

|Component|Greek|Definition|What It Measures|
|---|---|---|---|
|**Love**|ἀγάπη (agape)|Sacrificial commitment to others' good|Bond formation and maintenance|
|**Joy**|χαρά (chara)|Internal coherence and stability|Psychological integration|
|**Peace**|εἰρήνη (eirene)|Absence of destructive conflict|System stability, low variance|
|**Patience**|μακροθυμία (makrothumia)|Willingness to defer gratification|Time preference, long-term orientation|
|**Kindness**|χρηστότης (chrestotes)|Voluntary pro-social behavior|Cooperation without coercion|
|**Goodness**|ἀγαθωσύνη (agathosune)|Norm adherence without enforcement|Internalized standards|
|**Faithfulness**|πίστις (pistis)|Reliability of commitments|Trust, promise-keeping|
|**Gentleness**|πραΰτης (prautes)|Low-force conflict resolution|Restraint of aggression|
|**Self-Control**|ἐγκράτεια (egkrateia)|Internalized constraint|Impulse regulation|

### Mapping to Empirical Metrics

Each component maps to measurable proxies:

|Component|Primary Metric|Secondary Metrics|
|---|---|---|
|**Love**|Family intactness rate|Charitable giving, volunteer hours|
|**Joy**|Life satisfaction index|Suicide rate (inv.), depression prevalence (inv.)|
|**Peace**|Violent crime rate (inv.)|Social unrest indices, volatility measures|
|**Patience**|Personal savings rate|Debt-to-income, time preference studies|
|**Kindness**|Generalized trust index|Civic participation, volunteerism|
|**Goodness**|Property crime rate (inv.)|Fraud indices, corruption measures|
|**Faithfulness**|Marriage duration|Institutional trust, contract enforcement|
|**Gentleness**|Assault rate (inv.)|Domestic violence (inv.), dispute resolution|
|**Self-Control**|Addiction prevalence (inv.)|Obesity rate (inv.), impulse-crime rates|

_(inv.) = inverse relationship: lower values indicate higher coherence_

### Computing χ

For each component i, we compute a normalized score:

```
zᵢ(t) = [xᵢ(t) - μᵢ] / σᵢ
```

Where:

- xᵢ(t) = raw metric value at time t
- μᵢ = mean during baseline period (1940-1949)
- σᵢ = standard deviation during baseline period

Social coherence is then:

```
χ(t) = (1/9) · Σᵢ zᵢ(t)
```

**Interpretation:**

- χ > 0 → System more coherent than baseline
- χ = 0 → System at baseline coherence
- χ < 0 → System less coherent than baseline

### Why Equal Weighting?

We use equal weights for three reasons:

1. **Parsimony** - No arbitrary choices to defend
2. **Robustness** - Results are invariant under reasonable reweighting
3. **Transparency** - Anyone can replicate

Factor analysis and PCA alternatives are provided in Appendix B. The core findings do not depend on weighting scheme.

### The Baseline Period: 1940-1949

We select 1940-1949 as the reference period because it represents a **stable ordered phase far from criticality**:

- Post-Depression recovery complete
- Pre-counterculture
- High institutional trust (>70%)
- Low family disruption (<5% out-of-wedlock births)
- No major constraint removal events
- Low cross-domain volatility

This is not a claim that the 1940s were "good." It is a claim that the system was in **high-coherence equilibrium** - the appropriate reference state for measuring subsequent change.

---

_[Page 4: The Empirical Evidence]_