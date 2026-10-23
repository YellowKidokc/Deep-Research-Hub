---
id: SC-5603
phase: scaffolding
role: node
depends_on: []
authority: human
status: draft
---

# DOC-MM-004: Reflective vs Formative Moral Models

## The Apparent Circularity

**Claim:** "Coherence (χ) and the Fruits of the Spirit are mutually dependent - you define coherence by fruits, then say fruits prove coherence. This is circular."

## Why This Is Wrong

### The Measurement Model Distinction

There are two types of measurement models in psychometrics:

| Model | Direction | Example | Circularity Risk |
|-------|-----------|---------|------------------|
| **Formative** | Indicators → Construct | GDP = (consumption + investment + ...) | HIGH |
| **Reflective** | Construct → Indicators | Depression → (sadness, fatigue, ...) | LOW |

**We explicitly adopt the REFLECTIVE model.**

### Reflective Model Structure

```
χ (latent) → F_1 (Love)
          → F_2 (Joy)
          → F_3 (Peace)
          → F_4 (Patience)
          → F_5 (Kindness)
          → F_6 (Goodness)
          → F_7 (Faithfulness)
          → F_8 (Gentleness)
          → F_9 (Self-Control)
```

Mathematically:
```
F_k = β_k · χ + ε_k
```

Where:
- χ = latent coherence (the real thing)
- F_k = observable fruit k
- β_k = loading coefficient
- ε_k = measurement error

**Key:** χ CAUSES the F_k. The fruits do not CONSTITUTE χ.

### Why This Is Not Circular

| Statement | Model Type | Our Claim? |
|-----------|------------|------------|
| "χ is defined as the sum of fruits" | Formative | ❌ NO |
| "χ causes fruits to appear" | Reflective | ✅ YES |
| "Fruits indicate χ exists" | Evidential | ✅ YES |
| "Fruits = χ" | Identity | ❌ NO |

The relationship is:
- **Ontological:** χ is a real force (Spirit/coherence)
- **Causal:** χ produces fruits as effects
- **Epistemic:** We detect χ by observing fruits

This is the structure of ALL latent variable models (intelligence, depression, personality). It's standard psychometrics.

## Formal Structure

### The Structural Equation Model

```
χ ~ N(μ_χ, σ²_χ)           # Latent variable
F_k = β_k · χ + ε_k        # Measurement equations
ε_k ~ N(0, θ_k)            # Error terms
```

### Factor Analysis Validation

If the reflective model is correct, then:
1. All F_k should correlate positively (common cause)
2. Factor analysis should extract ONE dominant factor
3. Cronbach's α should be high (internal consistency)
4. Interventions on χ should move ALL F_k together

### Falsifiable Predictions

| Prediction | Test | If False |
|------------|------|----------|
| F_k intercorrelations | Correlation matrix | Low r → no common factor |
| Single factor | Factor analysis | Multiple factors → χ is composite |
| High α | Reliability analysis | Low α → fruits are independent |
| Joint movement | Intervention study | Independent movement → no χ |

**This is what makes the model scientific, not circular.**

## The Nominalism vs Realism Issue

### Formative Model (Nominalism)
- χ is just a convenient label for "the sum of good behaviors"
- No real underlying entity
- "Coherence" is a social construct

### Reflective Model (Realism)
- χ is a REAL causal force
- It exists independently of our measurement
- Fruits are SYMPTOMS of χ, not components

**We assert REALISM.** χ is ontic, not nominal.

This is a metaphysical commitment, but it's the same commitment physics makes about fields. You can't see an electromagnetic field directly - you infer it from effects. Same with χ.

## Defeat Condition

This resolution fails if:
1. Factor analysis shows F_k are uncorrelated (no common factor)
2. Cronbach's α < 0.7 (poor internal consistency)
3. Interventions on χ move F_k independently
4. The reflective model is formally shown to be ill-posed

## Biblical Grounding

Galatians 5:22-23 lists the fruits explicitly:
> "But the fruit of the Spirit is love, joy, peace, forbearance, kindness, goodness, faithfulness, gentleness and self-control."

Note: "fruit" is SINGULAR. The Spirit (χ) is one; the manifestations (F_k) are many.

This is exactly the reflective model structure.

## References

- Bollen, K.A. (1989). Structural Equations with Latent Variables
- Edwards, J.R. (2011). Formative vs Reflective Indicators
- [[DEF-VAR-007]] - Fruits measurement model
- [[U4-Fruits-Universal]] - Fruits operationalization

## Cross-Links

- [[RECURSIVE_ONTOLOGY_MAP]] - LOOP-4
- [[LOAD_BEARING_VARIABLES]] - DEF-VAR-007
