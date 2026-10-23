---
id: SC-1584
phase: scaffolding
role: map
depends_on: []
authority: human
status: draft
---

# Axiom Browser

**Static HTML Graph Explorer for Canonical Theophysics Axiom System**

---

## What This Is

A **read-only, static HTML interface** for browsing the canonical axiom database.

- **Zero server cost** - Pure HTML/CSS/JS
- **Zero installation** - Works in any browser
- **Zero login** - Open access
- **UUID-based** - Click any axiom to see full details
- **Inspectable** - View source, export data, verify claims

---

## Design Principles

1. **Database is source of truth** - Browser is a disposable view
2. **Professional, not promotional** - Standards body aesthetic
3. **Text-only canonical nodes** - No images in axiom definitions
4. **Inspectable structure** - Every claim is verifiable
5. **Free and portable** - Works offline, no dependencies

---

## Files

### Data Files (JSON)

- `elements.json` - All 188 axioms with full content
- `relationships.json` - 389 typed relationships (DEPENDS_ON, ENABLES)
- `graph.json` - Graph structure for visualization
- `master_chain.json` - Linear ordering (chain position 1-188)
- `metadata.json` - System statistics and metadata

### Data Files (CSV)

- `master_evidence_chain.csv` - Linear chain for academic review
- `elements.csv` - All axioms in tabular format
- `relationships.csv` - All relationships in tabular format

### Interface

- `index.html` - Main browser interface

---

## Features

### Current (v1.0)

✅ **Search** - Full-text search across axioms  
✅ **Filter** - By domain, tier, quality  
✅ **Click to expand** - See full axiom details  
✅ **Dependencies** - View what each axiom depends on  
✅ **Enables** - See what each axiom enables  
✅ **UUID display** - Canonical identifiers visible  
✅ **Master Chain view** - Linear ordering  
✅ **CSV exports** - Academic-friendly data

### Future (Optional)

⚪ Graph visualization (D3.js or similar)  
⚪ Evidence Constellation toggle  
⚪ Export to PDF  
⚪ Permalink to specific axioms  
⚪ Dark mode

---

## Usage

### Local Viewing

1. Open `index.html` in any modern browser
2. All data loads from JSON files (no server needed)
3. Search, filter, click to explore

### Hosting (Optional)

**GitHub Pages:**

```bash
# Push AXIOM_BROWSER folder to GitHub
# Enable GitHub Pages in repo settings
# Access at: https://yourusername.github.io/axiom-browser/
```

**Cloudflare Pages:**

- Drag and drop AXIOM_BROWSER folder
- Instant deployment
- Free tier sufficient

**Local Server (for development):**

```bash
# Python
python -m http.server 8000

# Node.js
npx http-server

# Then open: http://localhost:8000
```

---

## Data Freshness

To update the browser with latest database content:

```bash
cd O:\00_CANONICAL\01_AXIOMS\00_STRUCTURE
python export_for_browser.py
```

This regenerates all JSON and CSV files from the PostgreSQL canonical schema.

---

## Architecture

```
PostgreSQL (canonical schema)
    ↓
export_for_browser.py
    ↓
JSON files (elements, relationships, graph)
    ↓
index.html (static browser)
    ↓
User's browser (client-side rendering)
```

**Key insight:** The database is the product. The browser is a disposable view.

---

## What This Is NOT

❌ **Not an editor** - Read-only by design  
❌ **Not a social platform** - No comments, no accounts  
❌ **Not a chatbot** - No AI interpretation (yet)  
❌ **Not the source of truth** - Database is canonical  
❌ **Not promotional** - Standards body, not manifesto

---

## For Academics

The CSV files are designed for academic review:

- `master_evidence_chain.csv` - Complete linear ordering
- `elements.csv` - All axioms with UUIDs
- `relationships.csv` - Dependency graph

These are:

- Git-friendly (text-based)
- Archivable (standard format)
- Auditable (no proprietary encoding)
- Future-proof (will work in 50 years)

---

## Core Principle

> **"Canonical truth does not grow by accumulation.  
> Evidence grows by accumulation."**

The 188 axioms (Iron Chain) are frozen.  
Evidence Constellations orbit them, optional and flexible.

---

## Technical Details

**Browser Compatibility:**

- Chrome/Edge: ✅
- Firefox: ✅
- Safari: ✅
- Mobile: ✅

**File Size:**

- elements.json: ~150 KB
- relationships.json: ~20 KB
- Total: < 200 KB (fast load)

**No Dependencies:**

- Pure HTML/CSS/JS
- No frameworks
- No build step
- No npm packages

---

## Status

**Version:** 1.0  
**Date:** 2025-12-30  
**Axioms:** 188  
**Relationships:** 389  
**Status:** Production Ready

---

## Next Steps (Optional)

1. **Add graph visualization** - D3.js force-directed graph
2. **Evidence Constellation layer** - Toggle evidence items
3. **Export to PDF** - Generate printable version
4. **Permalink support** - Share specific axioms
5. **Search improvements** - Fuzzy search, regex

But remember: **The database is the product. Interfaces are disposable views.**

---

## License

The canonical axiom data is the intellectual property of the system creator.  
This browser interface is a reference implementation for viewing that data.

---

## Contact

**System:** Theophysics Canonical Axiom Database  
**Version:** 1.0  
**Browser:** Static HTML Graph Explorer
