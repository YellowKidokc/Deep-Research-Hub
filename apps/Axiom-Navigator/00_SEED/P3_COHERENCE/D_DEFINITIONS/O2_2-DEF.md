---
id: SD-5152
phase: seed
role: node
depends_on: []
authority: human
status: draft
---

# Coherence C[χ]

**[o4k1m39n-i47p-4k32-jmm5-8l2o1k9n3p47] | P1 | Definition | Coherence C[χ]**

> Measure of organized information density in the Logos Field.

## Mathematical Form
```
C = 1 - (S_obs/S_max)
```

## Dependencies
- [[O2_2|O2.2]]

## Referenced By

```dataview
LIST
FROM ""
WHERE contains(depends_on, "O2.2-DEF")
   OR contains(enables, "O2.2-DEF")
SORT file.name
```

## Same Domain

```dataview
LIST
FROM #domain/ontology
WHERE file.name != this.file.name
SORT id
```