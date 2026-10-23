---
id: MO-3439
phase: motion
role: node
depends_on: []
authority: human
status: draft
---

# Trinity Information Roles

**[z1v8x06y-t14a-1v19-uxx2-5w9z8v6y0a14] | P7 | Definition | Trinity Information Roles**

> Father=Source Entropy, Son=Channel Capacity, Spirit=Mutual Info

## Dependencies
- [[T1-T8|T1-T8]]

## Referenced By

```dataview
LIST
FROM ""
WHERE contains(depends_on, "TI.1")
   OR contains(enables, "TI.1")
SORT file.name
```

## Same Domain

```dataview
LIST
FROM #domain/trinity-information
WHERE file.name != this.file.name
SORT id
```