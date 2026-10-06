"""
Theophysics Vault Deep Analytics & Research Scanner
--------------------------------------------------
A high-performance, non-blocking, resumable analytics engine for Obsidian vaults.
Scans local markdown files, extracts equations, axioms, biblical citations,
wikilink network graphs, and computes mathematical & theological density.

Designed to handle 10,000+ files politely without freezing the machine.
State is saved in SQLite after every chunk, allowing graceful pause and resume.
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Configuration
WORKSPACE_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = WORKSPACE_ROOT / "obsidian_analytics_output"
DB_PATH = OUTPUT_DIR / "vault_analytics_state.db"
VAULT_REPORTS_DIR = Path(r"Z:\Theophysics_Vault\07_System_and_Operations\Vault_Analytics")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# DOMAIN REGEX PATTERNS
# -----------------------------------------------------------------------------
# 1. Equations: inline $...$, display $$...$$, and LaTeX environments
EQUATION_REGEX = re.compile(
    r"\$\$[\s\S]+?\$\$|"
    r"\$[^$\n]{2,120}\$|"
    r"\\begin\{(?:equation|align|gather|multline)\}[\s\S]+?\\end\{(?:equation|align|gather|multline)\}",
    re.MULTILINE
)

# 2. Axioms & Formal Theophysics Tokens
AXIOM_REGEX = re.compile(
    r"\b(A[0-9]{1,3}|TK-[0-9]{1,3}|Axiom\s+[0-9]{1,3}|Truth\s+Kernel\s+[0-9]{1,3}|"
    r"PMM|Chi\s+Delta\s+Grace|Triune\s+Observer|Generative\s+Grammar|First\s+Atom|"
    r"Watcher\s+Direction|Master\s+Equation|Moral\s+Absolute)\b",
    re.IGNORECASE
)

# 3. Biblical Citations (e.g. Gen 1:1, John 3:16, 1 Cor 15:3-4, Leviticus 19:17)
BIBLE_CITE_REGEX = re.compile(
    r"\b(?:(?:1|2|3)\s+)?(?:Gen(?:esis)?|Exod(?:us)?|Lev(?:iticus)?|Num(?:bers)?|Deut(?:eronomy)?|"
    r"Josh(?:ua)?|Judg(?:es)?|Ruth|Sam(?:uel)?|Kgs|Kings|Chron(?:icles)?|Ezra|Neh(?:emiah)?|Esth(?:er)?|"
    r"Job|Ps(?:alm)?s?|Prov(?:erbs)?|Eccl(?:esiastes)?|Song|Isa(?:iah)?|Jer(?:emiah)?|Lam(?:entations)?|"
    r"Ezek(?:iel)?|Dan(?:iel)?|Hos(?:ea)?|Joel|Amos|Obad(?:iah)?|Jonah|Mic(?:ah)?|Nah(?:um)?|Hab(?:akkuk)?|"
    r"Zeph(?:aniah)?|Hag(?:gai)?|Zech(?:ariah)?|Mal(?:achi)?|Matt(?:hew)?|Mark|Luke|John|Acts|"
    r"Rom(?:ans)?|Cor(?:inthians)?|Gal(?:atians)?|Eph(?:esians)?|Phil(?:ippians)?|Col(?:ossians)?|"
    r"Thess(?:alonians)?|Tim(?:othy)?|Titus|Philemon|Heb(?:rews)?|Jas|James|Pet(?:er)?|Rev(?:elation)?)\.?\s+"
    r"\d{1,3}(?::\d{1,3}(?:-\d{1,3})?)?\b",
    re.IGNORECASE
)

# 4. Theological Lexicon
THEOLOGY_REGEX = re.compile(
    r"\b(God|Jesus|Christ|Scripture|Trinity|Triune|Creator|Creation|Divine|Theism|"
    r"Theology|Resurrection|Incarnation|Gospel|Grace|Atonement|Omniscience|Logos|"
    r"Yahweh|Eschatology|Teleology|Transcendence|Immanence)\b",
    re.IGNORECASE
)

# 5. Wikilinks, Tags, Headings
WIKILINK_REGEX = re.compile(r"\[\[(.*?)\]\]")
TAG_REGEX = re.compile(r"(?<!\S)#([a-zA-Z0-9_\-]+)")
HEADING_REGEX = re.compile(r"^(#+)\s+(.+)$", re.MULTILINE)

# -----------------------------------------------------------------------------
# DATABASE LAYER
# -----------------------------------------------------------------------------
class VaultDatabase:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS file_queue (
                    path TEXT PRIMARY KEY,
                    folder TEXT,
                    file_size INTEGER,
                    mtime REAL,
                    status TEXT DEFAULT 'pending', -- pending, processed, error
                    error_msg TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS note_analytics (
                    file_path TEXT PRIMARY KEY,
                    title TEXT,
                    folder TEXT,
                    size_chars INTEGER,
                    line_count INTEGER,
                    word_count INTEGER,
                    heading_count INTEGER,
                    headings_json TEXT,
                    wikilink_count INTEGER,
                    wikilinks_json TEXT,
                    tag_count INTEGER,
                    tags_json TEXT,
                    table_count INTEGER,
                    code_block_count INTEGER,
                    equation_count INTEGER,
                    equations_json TEXT,
                    math_rigor_score REAL,
                    theology_count INTEGER,
                    theology_terms_json TEXT,
                    axiom_count INTEGER,
                    axioms_json TEXT,
                    bible_cite_count INTEGER,
                    bible_cites_json TEXT,
                    content_tier TEXT,
                    has_dataview INTEGER DEFAULT 0,
                    has_charts INTEGER DEFAULT 0,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_queue_status ON file_queue(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_math_rigor ON note_analytics(math_rigor_score DESC)")
            conn.commit()

    def enqueue_files(self, file_paths: List[Path]) -> Tuple[int, int]:
        """Add new or updated files to queue. Returns (new_count, skipped_count)."""
        new_count = 0
        skipped_count = 0
        with self._get_conn() as conn:
            cur = conn.cursor()
            for fp in file_paths:
                try:
                    stat = fp.stat()
                    p_str = str(fp.resolve())
                    folder_str = str(fp.parent.resolve())
                    
                    cur.execute("SELECT mtime, status FROM file_queue WHERE path = ?", (p_str,))
                    row = cur.fetchone()
                    if row:
                        if row["mtime"] == stat.st_mtime and row["status"] == "processed":
                            skipped_count += 1
                            continue
                        else:
                            # Modified file: re-queue
                            cur.execute("""
                                UPDATE file_queue 
                                SET mtime = ?, file_size = ?, status = 'pending', processed_at = NULL 
                                WHERE path = ?
                            """, (stat.st_mtime, stat.st_size, p_str))
                            new_count += 1
                    else:
                        cur.execute("""
                            INSERT INTO file_queue (path, folder, file_size, mtime, status)
                            VALUES (?, ?, ?, ?, 'pending')
                        """, (p_str, folder_str, stat.st_size, stat.st_mtime))
                        new_count += 1
                except Exception as e:
                    pass
            conn.commit()
        return new_count, skipped_count

    def get_pending_batch(self, limit: int = 50) -> List[sqlite3.Row]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT path, folder FROM file_queue WHERE status = 'pending' LIMIT ?", (limit,))
            return cur.fetchall()

    def mark_processed(self, path_str: str, data: Dict[str, Any]):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO note_analytics (
                    file_path, title, folder, size_chars, line_count, word_count,
                    heading_count, headings_json, wikilink_count, wikilinks_json,
                    tag_count, tags_json, table_count, code_block_count,
                    equation_count, equations_json, math_rigor_score,
                    theology_count, theology_terms_json, axiom_count, axioms_json,
                    bible_cite_count, bible_cites_json, content_tier,
                    has_dataview, has_charts, analyzed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                data["file_path"], data["title"], data["folder"], data["size_chars"],
                data["line_count"], data["word_count"], data["heading_count"],
                json.dumps(data["headings_list"]), data["wikilink_count"],
                json.dumps(data["wikilinks_list"]), data["tag_count"],
                json.dumps(data["tags_list"]), data["table_count"],
                data["code_block_count"], data["equation_count"],
                json.dumps(data["equations_list"]), data["math_rigor_score"],
                data["theology_count"], json.dumps(data["theology_terms"]),
                data["axiom_count"], json.dumps(data["axioms_list"]),
                data["bible_cite_count"], json.dumps(data["bible_cites_list"]),
                data["content_tier"], data["has_dataview"], data["has_charts"]
            ))
            cur.execute("UPDATE file_queue SET status = 'processed', processed_at = CURRENT_TIMESTAMP WHERE path = ?", (path_str,))
            conn.commit()

    def mark_error(self, path_str: str, error_msg: str):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE file_queue SET status = 'error', error_msg = ? WHERE path = ?", (error_msg, path_str))
            conn.commit()

    def get_progress(self) -> Dict[str, Any]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM file_queue")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM file_queue WHERE status = 'processed'")
            processed = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM file_queue WHERE status = 'pending'")
            pending = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM file_queue WHERE status = 'error'")
            errors = cur.fetchone()[0]

            cur.execute("SELECT SUM(word_count), SUM(equation_count), SUM(axiom_count), SUM(bible_cite_count) FROM note_analytics")
            totals_row = cur.fetchone()
            total_words = totals_row[0] or 0
            total_eqs = totals_row[1] or 0
            total_axioms = totals_row[2] or 0
            total_cites = totals_row[3] or 0

            return {
                "total": total,
                "processed": processed,
                "pending": pending,
                "errors": errors,
                "total_words": total_words,
                "total_equations": total_eqs,
                "total_axioms": total_axioms,
                "total_bible_cites": total_cites
            }

# -----------------------------------------------------------------------------
# CORE ANALYTICS PARSER
# -----------------------------------------------------------------------------
class VaultFileAnalyzer:
    @staticmethod
    def analyze_file(file_path: Path) -> Dict[str, Any]:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        chars = len(content)
        lines = content.count("\n") + 1
        words = len(content.split())

        # 1. Headings
        headings = [m[1].strip() for m in HEADING_REGEX.findall(content)]
        
        # 2. Wikilinks (target page without alias)
        raw_links = WIKILINK_REGEX.findall(content)
        wikilinks = list(set([l.split("|")[0].strip() for l in raw_links if l.strip()]))

        # 3. Tags
        tags = list(set(TAG_REGEX.findall(content)))

        # 4. Tables and Code Blocks
        tables = content.count("\n|")
        code_blocks = len(re.findall(r"```", content)) // 2

        # 5. Equations Extraction
        raw_equations = EQUATION_REGEX.findall(content)
        clean_equations = []
        for eq in raw_equations:
            eq_strip = eq.strip()
            if len(eq_strip) > 3 and eq_strip not in clean_equations:
                clean_equations.append(eq_strip)

        # 6. Axioms / Foundational Formalisms
        raw_axioms = AXIOM_REGEX.findall(content)
        axioms = list(set([a.strip().upper() for a in raw_axioms]))

        # 7. Biblical Citations
        bible_cites = list(set(BIBLE_CITE_REGEX.findall(content)))

        # 8. Theological Lexicon
        theology_terms = list(set([t.capitalize() for t in THEOLOGY_REGEX.findall(content)]))

        # 9. Math Rigor Score (0 to 100)
        # Ratio of equations & axioms to length, plus formal indicators
        eq_factor = min(len(clean_equations) * 8.0, 50.0)
        axiom_factor = min(len(axioms) * 10.0, 30.0)
        table_code_factor = min((tables + code_blocks) * 2.0, 20.0)
        math_rigor = round(eq_factor + axiom_factor + table_code_factor, 1)

        # 10. Content Tier
        if words < 300:
            tier = "Stub / Seed"
        elif words < 1200:
            tier = "Working Note"
        elif words < 3500:
            tier = "Comprehensive Essay"
        else:
            tier = "Master Treatise"

        title = file_path.stem
        # Extract title from frontmatter or first heading if available
        if headings:
            title = headings[0][:80]

        lower_c = content.lower()
        has_dataview = 1 if "dataview" in lower_c else 0
        has_charts = 1 if "chart" in lower_c or "graph" in lower_c or "mermaid" in lower_c else 0

        return {
            "file_path": str(file_path.resolve()),
            "title": title,
            "folder": file_path.parent.name,
            "size_chars": chars,
            "line_count": lines,
            "word_count": words,
            "heading_count": len(headings),
            "headings_list": headings[:15],
            "wikilink_count": len(wikilinks),
            "wikilinks_list": wikilinks[:30],
            "tag_count": len(tags),
            "tags_list": tags[:20],
            "table_count": tables,
            "code_block_count": code_blocks,
            "equation_count": len(clean_equations),
            "equations_list": clean_equations[:25],
            "math_rigor_score": math_rigor,
            "theology_count": len(theology_terms),
            "theology_terms": theology_terms[:20],
            "axiom_count": len(axioms),
            "axioms_list": axioms,
            "bible_cite_count": len(bible_cites),
            "bible_cites_list": bible_cites[:20],
            "content_tier": tier,
            "has_dataview": has_dataview,
            "has_charts": has_charts
        }

# -----------------------------------------------------------------------------
# BATCH RUNNER & REPORT GENERATOR
# -----------------------------------------------------------------------------
class VaultDeepAnalyticsEngine:
    def __init__(self):
        self.db = VaultDatabase(DB_PATH)

    def scan_and_queue(self, directories: List[Path]):
        all_md_files = []
        for d in directories:
            if d.is_file() and d.suffix.lower() == ".md":
                all_md_files.append(d)
            elif d.is_dir():
                print(f"[i] Scanning directory: {d}")
                all_md_files.extend(list(d.rglob("*.md")))
        
        print(f"[i] Found {len(all_md_files):,} Markdown files across target folder(s).")
        new_cnt, skipped_cnt = self.db.enqueue_files(all_md_files)
        print(f"[OK] Queued {new_cnt:,} files for processing ({skipped_cnt:,} already up-to-date).")

    def process_queue(self, batch_size: int = 50, pause_sec: float = 0.05):
        """Process queue with real-time progress and zero machine freezing."""
        stats = self.db.get_progress()
        total = stats["total"]
        if total == 0 or stats["pending"] == 0:
            print("\n[OK] All queued files are already processed!")
            self.export_reports()
            return

        print(f"\n{'='*76}")
        print(f"               STARTING DEEP VAULT ANALYTICS SCAN")
        print(f"{'='*76}")
        print(f"Total Files in Scope : {total:,}")
        print(f"Already Processed    : {stats['processed']:,}")
        print(f"Pending to Process   : {stats['pending']:,}")
        print(f"{'='*76}\n")

        start_time = time.time()
        processed_in_session = 0

        while True:
            batch = self.db.get_pending_batch(limit=batch_size)
            if not batch:
                break

            for row in batch:
                p = Path(row["path"])
                try:
                    if not p.exists():
                        self.db.mark_error(row["path"], "File not found")
                        continue
                    data = VaultFileAnalyzer.analyze_file(p)
                    self.db.mark_processed(row["path"], data)
                except Exception as e:
                    self.db.mark_error(row["path"], str(e))

                processed_in_session += 1

            # Progress update
            curr_stats = self.db.get_progress()
            done = curr_stats["processed"]
            pct = (done / total) * 100.0 if total else 100.0
            elapsed = max(time.time() - start_time, 0.001)
            rate = processed_in_session / elapsed
            rem = curr_stats["pending"]
            eta_sec = rem / rate if rate > 0 else 0
            eta_str = f"{int(eta_sec // 60)}m {int(eta_sec % 60):02d}s"

            sys.stdout.write(
                f"\r  [{done:,} / {total:,}] ({pct:5.1f}%) | "
                f"Eqs: {curr_stats['total_equations']:,} | "
                f"Axioms: {curr_stats['total_axioms']:,} | "
                f"Speed: {rate:4.1f} f/s | ETA: {eta_str}   "
            )
            sys.stdout.flush()

            time.sleep(pause_sec)

        print("\n\n[OK] Batch processing complete!")
        self.export_reports()

    def export_reports(self):
        """Generates the master analytics reports."""
        stats = self.db.get_progress()
        print("\n[i] Compiling comprehensive vault research reports...")

        with self.db._get_conn() as conn:
            cur = conn.cursor()
            
            # Top Math Rigor Notes
            cur.execute("""
                SELECT title, folder, word_count, equation_count, axiom_count, math_rigor_score, file_path
                FROM note_analytics
                ORDER BY math_rigor_score DESC, equation_count DESC
                LIMIT 30
            """)
            top_rigor = cur.fetchall()

            # All Equations Found
            cur.execute("""
                SELECT title, file_path, equations_json
                FROM note_analytics
                WHERE equation_count > 0
                ORDER BY equation_count DESC
            """)
            equation_rows = cur.fetchall()

            # Axioms Distribution
            cur.execute("SELECT axioms_json FROM note_analytics WHERE axiom_count > 0")
            all_axioms = {}
            for r in cur.fetchall():
                for ax in json.loads(r[0]):
                    all_axioms[ax] = all_axioms.get(ax, 0) + 1

            # Biblical Citations Distribution
            cur.execute("SELECT bible_cites_json FROM note_analytics WHERE bible_cite_count > 0")
            all_cites = {}
            for r in cur.fetchall():
                for c in json.loads(r[0]):
                    all_cites[c] = all_cites.get(c, 0) + 1

        # 1. Master Dashboard
        dashboard_path = OUTPUT_DIR / "00_VAULT_RESEARCH_DASHBOARD.md"
        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.write("# 🏛️ Theophysics Vault Deep Research & Analytics Dashboard\n\n")
            f.write(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  \n")
            f.write(f"**Total Notes Analyzed:** {stats['processed']:,} | **Total Word Count:** {stats['total_words']:,}\n\n")
            f.write(f"- **Mathematical Equations Extracted:** `{stats['total_equations']:,}`\n")
            f.write(f"- **Axioms / Core Tokens Referenced:** `{stats['total_axioms']:,}`\n")
            f.write(f"- **Biblical Passages Cited:** `{stats['total_bible_cites']:,}`\n\n")
            f.write("---\n\n")

            f.write("## 🧮 Top 30 Most Mathematically Rigorous Notes\n\n")
            f.write("| # | Note Title | Folder | Words | Equations | Axioms | Rigor Score |\n")
            f.write("|---|---|---|---:|---:|---:|---:|\n")
            for idx, r in enumerate(top_rigor, 1):
                f.write(f"| {idx} | [{r['title']}]({Path(r['file_path']).as_uri()}) | `{r['folder']}` | {r['word_count']:,} | {r['equation_count']} | {r['axiom_count']} | **{r['math_rigor_score']}** |\n")
            f.write("\n---\n\n")

            f.write("## 📜 Core Axioms & Ontology Frequency (Top 25)\n\n")
            f.write("| Axiom / Formal Token | Occurrences across Vault |\n")
            f.write("|---|---:|\n")
            for ax, count in sorted(all_axioms.items(), key=lambda x: x[1], reverse=True)[:25]:
                f.write(f"| `{ax}` | {count:,} notes |\n")
            f.write("\n---\n\n")

            f.write("## 📖 Top Biblical Passages Cited in Theophysics Work\n\n")
            f.write("| Scripture Citation | Mentions |\n")
            f.write("|---|---:|\n")
            for c, count in sorted(all_cites.items(), key=lambda x: x[1], reverse=True)[:25]:
                f.write(f"| **{c}** | {count} |\n")

        # 2. Master Equations Catalogue
        equations_path = OUTPUT_DIR / "00_EQUATIONS_CATALOGUE.md"
        with open(equations_path, "w", encoding="utf-8") as f:
            f.write("# 📐 Theophysics Formal Equations Catalogue\n\n")
            f.write(f"**Total Notes Containing Math Formalisms:** {len(equation_rows):,}\n\n")
            f.write("---\n\n")
            for r in equation_rows[:50]:
                eqs = json.loads(r["equations_json"])
                f.write(f"### [{r['title']}]({Path(r['file_path']).as_uri()})\n\n")
                for eq in eqs[:6]:
                    f.write(f"```latex\n{eq}\n```\n\n")
                f.write("---\n\n")

        # 3. Master CSV Export
        csv_path = OUTPUT_DIR / "00_VAULT_ANALYTICS_MASTER.csv"
        import csv
        with self.db._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT file_path, title, folder, word_count, equation_count, 
                       axiom_count, bible_cite_count, math_rigor_score, content_tier
                FROM note_analytics
                ORDER BY math_rigor_score DESC
            """)
            rows = cur.fetchall()
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Path", "Title", "Folder", "Words", "Equations", "Axioms", "Bible_Cites", "Math_Rigor_Score", "Tier"])
                for row in rows:
                    writer.writerow(list(row))

        # Mirror reports to Theophysics Vault
        if VAULT_REPORTS_DIR.exists() or Path(r"Z:\Theophysics_Vault").exists():
            VAULT_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            try:
                import shutil
                shutil.copy2(dashboard_path, VAULT_REPORTS_DIR / "00_VAULT_RESEARCH_DASHBOARD.md")
                shutil.copy2(equations_path, VAULT_REPORTS_DIR / "00_EQUATIONS_CATALOGUE.md")
                shutil.copy2(csv_path, VAULT_REPORTS_DIR / "00_VAULT_ANALYTICS_MASTER.csv")
                print(f"[OK] Mirrored reports directly to: {VAULT_REPORTS_DIR}")
            except Exception as e:
                print(f"[Notice] Vault mirror: {e}")

        print(f"[OK] Generated: {dashboard_path.name}")
        print(f"[OK] Generated: {equations_path.name}")
        print(f"[OK] Generated: {csv_path.name}")

# -----------------------------------------------------------------------------
# CLI ENTRY POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    engine = VaultDeepAnalyticsEngine()

    if len(sys.argv) > 1 and sys.argv[1] == "--progress":
        p = engine.db.get_progress()
        print(json.dumps(p, indent=2))
        sys.exit(0)
    elif len(sys.argv) > 1 and sys.argv[1] == "--export":
        engine.export_reports()
        sys.exit(0)

    # Folders to scan
    target_dirs = []
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            target_dirs.append(Path(arg))
    else:
        # Default: The master vault
        default_vault = Path(r"Z:\Theophysics_Vault")
        if default_vault.exists():
            target_dirs.append(default_vault)
        else:
            target_dirs.append(WORKSPACE_ROOT)

    engine.scan_and_queue(target_dirs)
    engine.process_queue()
