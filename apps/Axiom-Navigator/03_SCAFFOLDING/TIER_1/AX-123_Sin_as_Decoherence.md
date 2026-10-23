---
id: SC-123
phase: scaffolding
role: node
depends_on: []
authority: human
status: draft
---

# AX-123: Sin as Decoherence

**Chain Position:** 123 of 188  
**Domain:** Relational  
**Phase:** V

---

## Formal Statement

**Sin is decoherence: moral evil decreases C[χ], disrupts information flow, increases entropy.**

Sin = coherence destruction.

---

## Type Classification

**🔴 Soteriological** — Central to redemption

Sin is not just moral failing but physical decoherence.

---

## Derivation Path

**From AX-017 and AX-122:**

```
1. Moral realism is true (AX-017)
2. Good = coherence increase
3. Therefore evil = coherence decrease
4. Sin causes decoherence
∴ AX-123
```

Depends on: AX-017 (Moral Realism), AX-122
Enables: AX-124 (Entropy Opposition)

---

## Defeat Conditions

This axiom is falsified if:

1. **Sin has no physical effect**
   - Test: Show sin doesn't affect coherence
   - Prediction: Sin measurably decreases C[χ]
   - Status: 🟡 Testable

---

## Tier -1 Constraints

**DEF-VAR-008: Topological Defects (𝒟)**

- Sin creates topological defects
- Winding number ≠ 0

**DEF-VAR-009: Noether Current (J^μ_χ)**

- Sin = source term: ∂_μ J^μ = σ

---

## Trinity Mapping

**Person:** Son (Redeemer)

**Scripture:**

- **Romans 6:23**: "The wages of sin is death"
- **James 1:15**: "Sin, when it is full-grown, gives birth to death"

---

## Physical Grounding

**Coherence Theory:**

- Sin = decoherence source
- Decreases system coherence
- Increases entropy

**Predictions:**

- **P-SIN-1**: Moral violations decrease measurable coherence
  - Status: 🟡 Testable via coherence field detection

---

## Full Inheritance Chain

This axiom builds on **2 prior axioms**:
This axiom builds on **0 prior axioms**:

- None (Primitive axiom)

---

## What This Enables (Collapse Radius)

If this axiom fails, these axioms die:

- [[AX-124]]

---

## Dataview Queries

### Dependencies (What I Need)

```dataview
LIST
FROM "00_STRUCTURE/TIER_1"
WHERE contains(this.file.depends_on, file.name)
SORT chain_position ASC
```

### Dependents (What Needs Me)

```dataview
LIST
FROM "00_STRUCTURE/TIER_1"
WHERE contains(depends_on, this.file.name)
SORT chain_position ASC
```

---

## Status: 🟡 Template Generated

**Next Steps:**

1. Refine based on usage
2. Add empirical evidence
3. Specify defeat conditions
4. Enhance mathematical formulation

---

## Metadata

**Created:** 2025-12-30  
**Version:** 1.0 (Template)  
**Source:** Batch generated from INTEGRATED-AXIOM-MASTER.md
