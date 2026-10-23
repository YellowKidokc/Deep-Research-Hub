---
id: SC-100
phase: scaffolding
role: node
depends_on: []
authority: human
status: draft
---

# AX-100: Original Sin

**Chain Position:** 100 of 188
**Domain:** Human
**Phase:** IV

---

## Formal Statement

**Original Sin: All humans inherit a corrupted nature from Adam — a disposition toward sin, spiritual death, and separation from God that affects every person from conception.**

- **Epistemic Status:** THEOLOGICAL AXIOM (from Romans 5)
- **Dependency:** AX-099 (Human Dignity)
- **Bridge:** Theology → Psychology (universal fallenness)

---

## Type Classification

**🟣 Theological** — Inherited corruption.

Original sin is not personal guilt for Adam's act but inherited corruption — a nature inclined toward sin, unable to save itself, spiritually dead toward God. All are "in Adam" and share his fallen condition. Only grace can remedy this universal human predicament.

---

## Derivation Path

Depends on: AX-099 (Human Dignity)
Enables: AX-101 (Total Depravity)

**Logic:**
```
1. Adam sinned (Genesis 3)
2. Adam is federal head of humanity
3. Sin spreads to all descendants
4. Not just imitation but inheritance
5. All born with corrupted nature
6. Universal need for redemption
∴ AX-100
```

---

## Defeat Conditions

This axiom is falsified if:

1. **Show humans are naturally innocent**
2. **Prove some need no redemption**
3. **Demonstrate moral perfection possible without grace**
4. **Find Scripture teaching natural human goodness**

**Status:** Unfalsified — Universal human sinfulness is empirically and biblically evident.

---

## Tier -1 Constraints

**DEF-VAR-009: Noether Current (J^μ_χ)**
- Sin corrupts coherence current flow
- Inherited dysfunction in current patterns

**DEF-VAR-010: Vacuum Expectation Value (⟨χ⟩₀)**
- Fallen VEV lower than original
- Decoherence tendency inherited

---

## Trinity Mapping

**Person:** Son (Primarily) — Second Adam

**Theological Role:**
- Father: Allows fall, plans redemption
- Son: Second Adam reverses first Adam
- Spirit: Regenerates from inherited death

**Scripture:**
- Romans 5:12: "Sin entered the world through one man, and death through sin"
- Romans 5:19: "Through the disobedience of the one man the many were made sinners"
- Psalm 51:5: "Surely I was sinful at birth"
- Ephesians 2:3: "By nature deserving of wrath"
- 1 Corinthians 15:22: "In Adam all die"

---

## Physical Grounding

**Psychology Bridge:**
- Universal moral failure
- Persistent selfishness
- Developmental psychology of lying

**Biology Bridge:**
- Inherited traits
- Epigenetic transmission
- Evolutionary selfishness

**Sociology Bridge:**
- Universal cultural sin patterns
- No utopia has succeeded
- Persistent human conflict

**Evidence:**
- No one achieves moral perfection
- Universal experience of moral failure
- Children don't need to be taught to lie
- Every culture has concept of moral wrongdoing

**Cross-Domain Isomorphism:**
| Domain | Original Sin Analog |
|--------|-------------------|
| Computing | Inherited bug in codebase |
| Medicine | Genetic disease |
| Law | Inherited debt |
| Biology | Corrupted DNA |

**Transfer Principle:** All humans inherit corrupted nature from Adam. This original sin explains universal moral failure and the necessity of grace for salvation.

---


## Full Inheritance Chain

This axiom builds on **0 prior axioms**:

- None (Primitive axiom)

---

## What This Enables (Collapse Radius)

If this axiom fails, these axioms die:

- [[AX-101]]

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
