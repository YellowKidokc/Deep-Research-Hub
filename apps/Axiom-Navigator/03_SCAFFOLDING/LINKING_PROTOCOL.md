---
id: SC-1647
phase: scaffolding
role: meta
depends_on: []
authority: human
status: draft
---

# Canonical Linking Protocol

**Purpose:** Establish systematic interlinking across the entire Theophysics canonical structure to create a unified knowledge graph.

**Quick Navigation:**

- [Link Types](#link-types)
- [Linking Rules](#linking-rules)
- [Document-Specific Protocols](#document-specific-protocols)
- [Link Maintenance](#link-maintenance)

---

# Link Types

## 1. Hierarchical Links (Vertical)

**Purpose:** Navigate up/down the conceptual hierarchy

### Parent → Child

- Maps point to all documents they organize
- Tier documents point to individual axioms
- Papers point to sections and axioms they contain

### Child → Parent

- Every axiom links back to its tier
- Every theorem links to the axioms it depends on
- Every definition links to where it's used

**Format:**

```markdown
## Hierarchical Context

**Parent:** [[00_MASTER_MAP]]
**Tier:** [[Tier_2_Divine]]
**Paper:** [[P7_Trinity_Paper]]
```

---

## 2. Dependency Links (Logical)

**Purpose:** Show logical prerequisites and derivations

### Depends On (Prerequisites)

- What must be true before this can be true
- Axioms that this theorem requires
- Definitions needed to understand this

### Feeds Into (Consequences)

- What follows from this axiom
- Theorems that use this axiom
- Papers that build on this

**Format:**

```yaml
depends_on:
  - "[[P0.1_Existence]]"
  - "[[P0.2_Distinction]]"
feeds_into:
  - "[[T1_One_God]]"
  - "[[D1_Naturalism_Impossible]]"
```

---

## 3. Cross-Reference Links (Horizontal)

**Purpose:** Connect related concepts at the same level

### Related Axioms

- Axioms in the same tier
- Parallel concepts in different domains
- Complementary ideas

### Related Theorems

- Theorems using similar logic
- Theorems in the same domain
- Theorems with similar defeat conditions

### Related Evidence

- Empirical support for this claim
- Historical examples
- Scientific parallels

**Format:**

```markdown
## Cross-References

**Related Axioms:** [[O1.1_Information_Substrate]], [[O1.3_Information_Conservation]]
**Related Theorems:** [[T2_Father_God]], [[T3_Son_God]]
**Related Evidence:** [[E_Quantum_Measurement]], [[E_IIT_Studies]]
```

---

## 4. Structural Defense Links

**Purpose:** Connect to defensive architecture

### Loop Resolution

- Which apparent circularity this addresses
- Closure document that proves non-circularity

### Variable Definition

- Which DEF-VAR this uses
- Variable measurement protocol
- Defeat conditions

**Format:**

```yaml
structural_defense: LOOP-2
variable_refs: [DEF-VAR-001, DEF-VAR-004]
defense_doc: "[[DOC-IIT-002_Observer-Without-Collapse]]"
```

---

## 5. Evidence Links (Empirical)

**Purpose:** Connect theory to data

### Supporting Evidence

- Experiments that confirm this
- Historical data supporting this
- Scientific consensus aligned with this

### Defeat Conditions

- What would falsify this
- Empirical tests that could disprove this
- Boundary conditions

**Format:**

```markdown
## Evidence

**Supporting:** [[EV_Fisher_Information_Physics]], [[EV_IIT_Consciousness]]
**Defeat Conditions:**

1. [[DEFEAT_Phi_Sigma_Uncorrelated]]
2. [[DEFEAT_Grace_Independent_Network]]
```

---

# Linking Rules

## Rule 1: Every Document Has a Home

Every document must link to:

1. **Parent map** (where it lives in the hierarchy)
2. **Master map** (the canonical entry point)
3. **At least one sibling** (related document at same level)

## Rule 2: Bidirectional Links Required

If A links to B, then B must link back to A (unless B is a map/index)

**Example:**

- If `T2_Father_God.md` depends on `T1_One_God.md`
- Then `T1_One_God.md` must list `T2_Father_God.md` in "feeds_into"

## Rule 3: Link Depth Limits

- **Minimum:** 3 links per document (parent, 1 dependency, 1 cross-ref)
- **Maximum:** 15 primary links (avoid link spam)
- **Unlimited:** Map/index documents can link to everything they organize

## Rule 4: Link Specificity

Use the most specific link possible:

- ✅ `[[T2_Father_God]]`
- ✅ `[[T2_Father_God#Information-Role]]` (section link)
- ❌ `[[02_THEOREMS]]` (too general when specific theorem exists)

## Rule 5: Link Context

Always provide context for why you're linking:

- ❌ "See [[T1_One_God]]"
- ✅ "Depends on [[T1_One_God|monotheism]] as prerequisite"

## Rule 6: Broken Link Prevention

- Use relative paths for internal links: `[[../01_AXIOMS/file]]`
- Use display text for clarity: `[[long-filename|Short Name]]`
- Check links when moving files

---

# Document-Specific Protocols

## Axioms (01_AXIOMS/)

### Required Links

```yaml
# In YAML frontmatter
depends_on: [list of prerequisite axioms]
feeds_into: [list of derived theorems/axioms]
structural_defense: LOOP-# (if applicable)
variable_refs: [DEF-VAR-###] (if applicable)
tier: # (0-2)
paper: P# (which paper contains this)
```

### Required Sections with Links

```markdown
## Hierarchical Context

**Tier:** [[Tier_#_Name]]
**Paper:** [[P#_Paper_Name]]
**Master Map:** [[00_MASTER_MAP]]

## Logical Dependencies

**Prerequisites:** [[prerequisite axioms]]
**Derived From:** [[parent axioms]]

## Consequences

**Feeds Into:** [[theorems using this]]
**Used In:** [[papers citing this]]

## Cross-References

**Related Axioms:** [[same-tier axioms]]
**Related Definitions:** [[definitions]]
**Related Evidence:** [[evidence files]]

## Defensive Architecture

**Addresses Loop:** [[LOOP-#]] (if applicable)
**Variable Used:** [[DEF-VAR-###]] (if applicable)
**Closure Doc:** [[DOC-XX-###]] (if applicable)
```

---

## Theorems (02_THEOREMS/)

### Required Links

```yaml
# In YAML frontmatter
depends_on: [axioms this requires]
feeds_into: [what follows from this]
domain: [trinity|ontology|grace|etc]
```

### Required Sections with Links

```markdown
## Logical Chain

1. [[prerequisite axiom 1]]
2. [[prerequisite axiom 2]]
3. **This theorem**
4. [[consequence theorem]]

## Proof Structure

**Axioms Used:** [[list all axioms]]
**Definitions Used:** [[list all definitions]]
**Variables Used:** [[DEF-VAR references]]

## Related Theorems

**Same Domain:** [[other theorems in domain]]
**Parallel Logic:** [[theorems with similar structure]]

## Evidence

**Supporting:** [[evidence files]]
**Defeat Conditions:** [[what would falsify this]]
```

---

## Equations (03_EQUATIONS/)

### Required Links

```markdown
## Variable Definitions

- χ: [[DEF-VAR-001_Universal_Coherence]]
- λ: [[DEF-VAR-004_Decay_Rate]]
- G: [[DEF-VAR-006_Grace_Kernel]]

## Axioms This Formalizes

**Primary:** [[axiom being formalized]]
**Supporting:** [[related axioms]]

## Theorems Using This

**Direct:** [[theorems directly using equation]]
**Indirect:** [[theorems using derived forms]]

## Papers

**Introduced In:** [[P#_Paper]]
**Applied In:** [[other papers]]

## Evidence

**Empirical Support:** [[evidence files]]
**Physical Analog:** [[physics papers]]
```

---

## Papers (04_PAPERS/)

### Required Links

```markdown
## Paper Structure

**Master Map:** [[00_MASTER_MAP]]
**Paper Series:** [[Paper_Index]]

## Content Inventory

**Axioms Introduced:** [[list all axioms]]
**Theorems Proven:** [[list all theorems]]
**Equations Derived:** [[list all equations]]
**Definitions Provided:** [[list all definitions]]

## Dependencies

**Requires Papers:** [[prerequisite papers]]
**Builds Toward:** [[subsequent papers]]

## Evidence Base

**Supporting Evidence:** [[evidence files]]
**Historical Context:** [[historical evidence]]
**Scientific Parallels:** [[scientific evidence]]
```

---

## Evidence (05_EVIDENCE/)

### Required Links

```markdown
## What This Supports

**Axioms:** [[axioms this confirms]]
**Theorems:** [[theorems this validates]]
**Equations:** [[equations this fits]]

## Evidence Type

**Empirical:** [description]
**Historical:** [description]
**Scientific:** [description]

## Related Evidence

**Complementary:** [[other evidence supporting same claim]]
**Contradictory:** [[evidence that challenges this]]

## Papers Using This

**Primary:** [[papers citing this as main evidence]]
**Secondary:** [[papers citing this as supporting]]
```

---

## Definitions (08_DEFINITIONS/)

### Required Links

```markdown
## Term Definition

**Canonical Variable:** [[DEF-VAR-###]] (if applicable)
**Introduced In:** [[axiom or paper]]

## Usage

**Axioms Using This:** [[list axioms]]
**Theorems Using This:** [[list theorems]]
**Equations Using This:** [[list equations]]

## Related Definitions

**Prerequisites:** [[definitions needed to understand this]]
**Derived:** [[definitions that build on this]]
**Contrasts:** [[definitions this differs from]]

## Measurement

**Protocol:** [[measurement protocol]]
**Evidence:** [[empirical measurements]]
```

---

# Link Maintenance

## Adding New Documents

**Checklist:**

1. ✅ Add to appropriate folder (01-09)
2. ✅ Create YAML frontmatter with `depends_on` and `feeds_into`
3. ✅ Link to parent map/tier
4. ✅ Link to [[00_MASTER_MAP]]
5. ✅ Add cross-references to related documents
6. ✅ Update parent map to include this document
7. ✅ Update related documents to link back (bidirectional)
8. ✅ Add to paper inventory if applicable
9. ✅ Link to defensive architecture if applicable
10. ✅ Add evidence links if applicable

## Moving Documents

**Checklist:**

1. ✅ Update all internal links in the document
2. ✅ Update parent map to reflect new location
3. ✅ Update all documents that link to this one
4. ✅ Update [[00_MASTER_MAP]] if necessary
5. ✅ Check for broken links with Obsidian link checker
6. ✅ Update paper inventories if applicable

## Archiving Documents

**Checklist:**

1. ✅ Move to `_ARCHIVE/`
2. ✅ Remove from parent map
3. ✅ Update documents that linked to this (mark as archived)
4. ✅ Keep links intact (archived docs still accessible)
5. ✅ Add archive note to [[00_MASTER_MAP]] if significant

---

# Link Templates

## Template: New Axiom

```markdown
---
axiom_id: AX-###
tiered_id: X#.#
uuid: [generate UUID]
title: "Axiom Title"
type: Axiom
tier: #
paper: P#
status: CANONICAL
domain: [domain name]
depends_on: 
  - "[[prerequisite_1]]"
  - "[[prerequisite_2]]"
feeds_into:
  - "[[consequence_1]]"
  - "[[consequence_2]]"
structural_defense: LOOP-# (if applicable)
variable_refs: [DEF-VAR-###] (if applicable)
---

# X#.#: Axiom Title

**Chain Position:** # of 188
**Master Map:** [[00_MASTER_MAP]]
**Tier:** [[Tier_#_Name]]
**Paper:** [[P#_Paper_Name]]

---

## Formal Statement

[Statement]

---

## Logical Dependencies

**Prerequisites:**

- [[prerequisite_1]] - [why needed]
- [[prerequisite_2]] - [why needed]

**Derived From:**

- [[parent_axiom]] - [relationship]

---

## Consequences

**Feeds Into:**

- [[theorem_1]] - [how used]
- [[axiom_2]] - [how used]

**Used In Papers:**

- [[P#_Paper]] - [role in paper]

---

## Cross-References

**Related Axioms:** [[related_1]], [[related_2]]
**Related Definitions:** [[definition_1]]
**Related Evidence:** [[evidence_1]]

---

## Defensive Architecture

**Addresses Loop:** [[LOOP-#]] (if applicable)
**Variable Used:** [[DEF-VAR-###]] (if applicable)
**Closure Doc:** [[DOC-XX-###]] (if applicable)

---

## Evidence

**Supporting:** [[evidence_files]]
**Defeat Conditions:** [what would falsify]
```

---

## Template: New Theorem

```markdown
---
uuid: [generate UUID]
id: T#
title: Theorem Title
type: Theorem
domain: [domain]
status: CANONICAL
paper: P#
depends_on:
  - "[[axiom_1]]"
  - "[[axiom_2]]"
feeds_into:
  - "[[consequence_1]]"
---

# T# — Theorem Title

**Master Map:** [[00_MASTER_MAP]]
**Paper:** [[P#_Paper_Name]]

> **[Theorem statement]**

---

## Logical Chain

1. [[prerequisite_1]] - [role]
2. [[prerequisite_2]] - [role]
3. **This theorem** (T#)
4. [[consequence_1]] - [what follows]

---

## Proof Structure

**Axioms Used:**

- [[axiom_1]] - [how used]
- [[axiom_2]] - [how used]

**Definitions Used:**

- [[definition_1]] - [how used]

**Variables Used:**

- χ: [[DEF-VAR-001]]
- λ: [[DEF-VAR-004]]

---

## Related Theorems

**Same Domain:** [[theorem_in_domain]]
**Parallel Logic:** [[similar_theorem]]

---

## Evidence

**Supporting:** [[evidence_files]]
**Defeat Conditions:** [what would falsify]
```

---

# Link Visualization

## The Link Graph Structure

```
00_MASTER_MAP (Hub)
    ↓
    ├─→ 00_STRUCTURE/ (Defensive Architecture)
    │   ├─→ DOC-FI-001 ←→ LOOP-1 ←→ Axioms using Fisher Info
    │   ├─→ DOC-IIT-002 ←→ LOOP-2 ←→ Consciousness axioms
    │   └─→ DEF-VAR-001 ←→ χ equations ←→ Evidence
    │
    ├─→ 01_AXIOMS/ (Tiered Structure)
    │   ├─→ Tier_0_Primordial/
    │   │   ├─→ P0.1 ←→ feeds_into → O1.1, G1.1
    │   │   └─→ P0.3 ←→ feeds_into → O1.1, equations
    │   ├─→ Tier_1_Ontological/
    │   │   ├─→ O1.1 ←→ depends_on ← P0.1, P0.3
    │   │   └─→ O1.1 ←→ feeds_into → G2.1, theorems
    │   └─→ Tier_2_Divine/
    │       ├─→ G5.2 ←→ feeds_into → T1, T2, T3
    │       └─→ G5.2 ←→ related → Trinity papers
    │
    ├─→ 02_THEOREMS/
    │   ├─→ T1 ←→ depends_on ← G5.2
    │   ├─→ T2 ←→ depends_on ← T1
    │   ├─→ T2 ←→ feeds_into → T3, TI.1
    │   └─→ T2 ←→ related → P7_Trinity
    │
    ├─→ 03_EQUATIONS/
    │   ├─→ E_Master_Equation ←→ variables → DEF-VAR-001, 004, 006
    │   └─→ E_Master_Equation ←→ formalizes → axioms
    │
    ├─→ 04_PAPERS/
    │   ├─→ P1 ←→ contains → axioms list
    │   ├─→ P7_Trinity ←→ contains → T1, T2, T3
    │   └─→ P7_Trinity ←→ evidence → Trinity evidence
    │
    ├─→ 05_EVIDENCE/
    │   ├─→ EV_IIT ←→ supports → consciousness axioms
    │   └─→ EV_Fisher ←→ supports → information axioms
    │
    └─→ 08_DEFINITIONS/
        ├─→ D_Coherence ←→ used_in → axioms, theorems
        └─→ D_Coherence ←→ measured_by → DEF-VAR-001
```

---

# Implementation Priority

## Phase 1: Core Structure (Do First)

1. ✅ Link all axioms to their tiers
2. ✅ Link all axioms to [[00_MASTER_MAP]]
3. ✅ Add `depends_on` and `feeds_into` to all axioms
4. ✅ Link all theorems to their prerequisite axioms

## Phase 2: Cross-References (Do Second)

1. Add related axiom links within tiers
2. Add related theorem links within domains
3. Link equations to variables (DEF-VAR)
4. Link papers to their content inventories

## Phase 3: Defensive Architecture (Do Third)

1. Link axioms to loop resolutions
2. Link variables to defeat conditions
3. Link closure docs to axioms they defend
4. Add structural defense metadata

## Phase 4: Evidence Integration (Do Fourth)

1. Link evidence to axioms it supports
2. Link evidence to theorems it validates
3. Add defeat condition links
4. Add empirical measurement links

---

**Status:** ACTIVE PROTOCOL
**Last Updated:** 2024-12-30
**Maintained By:** Canonical Structure Team
