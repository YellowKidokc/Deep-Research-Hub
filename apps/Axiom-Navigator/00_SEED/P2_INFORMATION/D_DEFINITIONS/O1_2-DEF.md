---
id: SD-3775
phase: seed
role: node
depends_on: []
authority: human
status: draft
---

# Logos Field χ(x,t)

**[k0g7i95j-e03l-0g98-fii1-4h8k7g5j9l03] | P1 | Definition | Logos Field χ(x,t)**

> The self-grounding informational substrate of reality.

## Mathematical Form
```
χ = ∫(G·K)dΩ
```

## Dependencies
- [[O1_2|O1.2]]

## Referenced By

```dataview
LIST
FROM ""
WHERE contains(depends_on, "O1.2-DEF")
   OR contains(enables, "O1.2-DEF")
SORT file.name
```

## Same Domain

```dataview
LIST
FROM #domain/ontology
WHERE file.name != this.file.name
SORT id
```