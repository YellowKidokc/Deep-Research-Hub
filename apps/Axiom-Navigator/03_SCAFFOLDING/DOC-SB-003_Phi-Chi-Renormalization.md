---
id: SC-1406
phase: scaffolding
role: node
depends_on: []
authority: human
status: draft
---

# DOC-SB-003: Φ→χ as Network Renormalization

## The Apparent Circularity

**Claim:** "Individual coherence (Φ) and social coherence (χ) are mutually dependent - individuals form society, society forms individuals. This is a vicious circle."

## Why This Is Wrong

### Scale Typing Resolution

Φ and χ are NOT the same variable. They are **scale-typed instantiations** of the coherence family:

| Variable | Scale | Domain | Units |
|----------|-------|--------|-------|
| Φ_i | Individual (micro) | Neural/cognitive | bits (IIT) |
| Σ_s / χ | Social (macro) | Network/collective | inverse-entropy |

**Key principle:** Variables at different scales cannot be circularly defined. They can be RELATED via aggregation laws, but that's not circularity.

### Renormalization, Not Recursion

The relationship between Φ and χ is analogous to **renormalization group flow** in physics:

```
χ = R(Σ_i Φ_i, W_ij)
```

Where:
- R = renormalization operator (coarse-graining)
- Φ_i = individual coherence of agent i
- W_ij = relational matrix (network structure)

This is a ONE-WAY aggregation:
1. Start with micro-level Φ values
2. Apply network topology W
3. Coarse-grain to macro-level χ

### Feedback ≠ Circularity

Yes, social coherence χ FEEDS BACK to influence individual Φ:

```
dΦ_i/dt = f(Φ_i, χ, ...)
```

But feedback is DYNAMICAL, not DEFINITIONAL.

| Type | Example | Circular? |
|------|---------|-----------|
| Definitional dependence | "A = B, B = A" | ✅ Yes |
| Causal feedback | Thermostat temperature control | ❌ No |
| Aggregation | Atoms → molecules → cells | ❌ No |

Φ→χ is aggregation + feedback. Neither is circularity.

## Formal Structure

### Micro Level (Individual)

```
Φ_i = max_{partition} [ I_i(whole) - Σ I_i(parts) ]
```

Defined independently per IIT axioms. No reference to χ.

### Meso Level (Relational)

```
W_ij = coupling strength between i and j
```

Network structure. Defined independently by social/communication ties.

### Macro Level (Social)

```
χ = ∫∫ Φ_i · W_ij · Φ_j · dμ(i,j)
```

Or equivalently, the order parameter of the collective:

```
χ = |⟨Φ⟩| / σ(Φ)
```

Mean coherence normalized by variance.

### Dynamics (Feedback Loop)

```
dΦ_i/dt = -λΦ_i + α·χ·W_ij + G_i(t)
```

Individual coherence decays naturally (λ), is boosted by social field (α·χ), and can receive grace (G).

**This is dynamics, not definition.**

## The Aggregation Theorem

**Theorem:** If micro-level Φ_i are defined independently (via IIT), then macro-level χ is DERIVABLE, not circular.

**Proof sketch:**
1. Φ_i requires only system i's causal structure
2. W_ij requires only pairwise interaction data
3. χ = f(Φ, W) is a function of independently-defined quantities
4. Therefore χ is not defined in terms of itself ∎

## Defeat Condition

This resolution fails if:
1. Individual Φ cannot be measured without reference to social χ
2. The aggregation operator R is shown to be ill-defined
3. Scale separation breaks down (micro and macro become indistinguishable)

## Why Scale Typing Matters

This is the same logic physicists use for:
- Temperature (macro) vs. kinetic energy (micro)
- Pressure (macro) vs. momentum transfer (micro)
- Magnetization (macro) vs. spin alignment (micro)

Nobody says temperature and kinetic energy are "circular" just because they're related. They're SCALE-TYPED expressions of the same underlying reality.

Φ and χ work the same way.

## References

- Wilson, K. (1971). Renormalization Group
- Haken, H. (1983). Synergetics
- Kelso, J.A.S. (1995). Dynamic Patterns
- [[DEF-VAR-001]] - Coherence variable spec
- [[A3.2-Coherence-Measure]]

## Cross-Links

- [[RECURSIVE_ONTOLOGY_MAP]] - LOOP-3
- [[LOAD_BEARING_VARIABLES]] - DEF-VAR-001
