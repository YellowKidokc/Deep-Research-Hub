"""
Theophysics & Biblical Mathematics Evidence Engine & Continuous Crawler
-----------------------------------------------------------------------
A persistent, multi-source research crawler and evidence extraction engine.
Discovers and extracts instances where Christian theology (God, Jesus, the Bible,
Trinity, Creation) intersects with mathematical formalisms, equations, and proofs.

Supports week-long continuous crawling with SQLite state checkpointing,
8-signal transparent scoring, clean Markdown preservation, and direct integration
with the Theophysics Vault (Z:\Theophysics_Vault).
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, quote_plus

import aiohttp
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("theophysics_evidence_crawler.log", encoding="utf-8", mode="a")
    ]
)
logger = logging.getLogger("EvidenceEngine")

# Directories
WORKSPACE_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = WORKSPACE_ROOT / "output" / "theophysics_evidence"
SOURCES_DIR = OUTPUT_DIR / "sources"
DB_PATH = OUTPUT_DIR / "evidence_crawler_state.db"
VAULT_EVIDENCE_DIR = Path(r"Z:\Theophysics_Vault\02_Evidence_Matrix\47_Formal_Logic_and_Epistemic_Intake\Evidence_Receipts")
LEXICON_INTAKE_CSV = Path(r"Z:\Theophysics_Vault\07_System_and_Operations\AG_Lexicon_Intake\AG_SORTING_TERMS_INTAKE.csv")

for d in [OUTPUT_DIR, SOURCES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# FAITH & MATHEMATICS PATTERNS
# -----------------------------------------------------------------------------
FAITH_PATTERNS = [
    r"\bGod\b", r"\bJesus\b", r"\bChrist\b", r"\bBible\b", r"\bBiblical\b",
    r"\bScripture\b", r"\bScriptures\b", r"\bYahweh\b", r"\bTrinity\b",
    r"\bTriune\b", r"\bCreator\b", r"\bCreation\b", r"\bDivine\b",
    r"\bTheism\b", r"\bTheistic\b", r"\bTheology\b", r"\bTheological\b",
    r"\bResurrection\b", r"\bIncarnation\b", r"\bGospel\b", r"\bGenesis\b",
    r"\bOmniscience\b", r"\bOmnipotence\b", r"\bLogos\b", r"\bHoly Spirit\b",
    r"\bChristian faith\b", r"\bMessianic\b", r"\bEschatology\b", r"\bAtonement\b"
]
FAITH_REGEX = re.compile("|".join(FAITH_PATTERNS), re.IGNORECASE)

MATH_EQUATION_PATTERNS = [
    # LaTeX display / inline math
    r"\$\$[\s\S]+?\$\$",
    r"\$[^\$]{3,80}\$",
    r"\\\[[\s\S]+?\\\]",
    r"\\\(.+?\\/math\)",
    r"\\begin\{(?:equation|align|gather|multline)\}[\s\S]+?\\end\{(?:equation|align|gather|multline)\}",
    # Explicit formulas with operators & formal symbols
    r"(?:P\([A-Za-z0-9_|\\ ]+\)\s*=\s*[^,\.\n]+)",                    # P(H|E) = ...
    r"(?:e\^\{\s*i\s*\\?pi\s*\}\s*\+\s*1\s*=\s*0)",                   # Euler identity
    r"(?:[A-Za-z0-9_]+\s*=\s*[A-Za-z0-9_+\-*/^\\ ]{4,40})",          # General equations
    r"(?:\\sum_\{[^}]+\}|\\int_\{[^}]+\}|\\prod_\{[^}]+\})",           # Integrals/Sums
    r"(?:\\forall|\\exists|\\implies|\\iff|\\aleph|\\infty|\\mathbb)", # Set & Modal logic symbols
    # Named formalisms
    r"\bBayes(?:ian)?\s+(?:theorem|formula|probability|inference|analysis|prior)\b",
    r"\bEuler(?:'s)?\s+identity\b",
    r"\bG[oö]del(?:'s)?\s+(?:ontological\s+proof|incompleteness\s+theorem|axioms)\b",
    r"\bCantor(?:'s)?\s+(?:transfinite|diagonal|paradox|actual\s+infinity)\b",
    r"\bKolmogorov\s+complexity\b",
    r"\bBoltzmann\s+entropy\s+(?:formula|equation)\b",
    r"\bSchr[oö]dinger\s+equation\b",
    r"\bmathematical\s+(?:equation|proof|formalism|axiom|model|probability)\b",
    r"\bmodal\s+logic\s+(?:proof|axiom|system)\b",
    r"\bontological\s+argument\s+(?:formalized|equation|symbolic)\b"
]
MATH_REGEX = re.compile("|".join(MATH_EQUATION_PATTERNS), re.IGNORECASE)

# High-priority academic seed queries
DEFAULT_DISCOVERY_QUERIES = [
    "God mathematical equations",
    "Jesus resurrection Bayesian probability Swinburne",
    "God necessary ground axiom primitive explanatory",
    "Gödel ontological proof modal logic formalized",
    "Euler identity God mathematics Christian",
    "Cantor transfinite numbers absolute infinite God",
    "Bible mathematical patterns probability calculation",
    "fine-tuning cosmological constant God equation",
    "John Earman Hume abject failure Bayesian probability",
    "Principia Mathematica Moralia theophysics",
    "Trinity vector space relational ontology mathematics",
    "mathematical proof existence of God peer reviewed",
    "information theory DNA code God creator signature",
    "quantum cosmology first observer watcher God",
    "modal ontological argument S5 Plantinga God axiom"
]

# -----------------------------------------------------------------------------
# DATABASE LAYER (Resumable State)
# -----------------------------------------------------------------------------
class EvidenceDatabase:
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
                CREATE TABLE IF NOT EXISTS url_queue (
                    url TEXT PRIMARY KEY,
                    source_type TEXT,
                    query TEXT,
                    priority INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'pending', -- pending, visiting, crawled, failed
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_attempt TIMESTAMP,
                    error_msg TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS crawled_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE,
                    title TEXT,
                    domain TEXT,
                    author TEXT,
                    published_date TEXT,
                    source_type TEXT,
                    has_evidence INTEGER DEFAULT 0,
                    content_hash TEXT,
                    word_count INTEGER,
                    overall_score REAL DEFAULT 0.0,
                    markdown_filename TEXT,
                    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS evidence_receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER,
                    url TEXT,
                    quote_text TEXT,
                    equation_snippet TEXT,
                    faith_terms TEXT,
                    math_terms TEXT,
                    score REAL,
                    score_breakdown TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(source_id) REFERENCES crawled_sources(id)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_queue_status ON url_queue(status, priority)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_receipt_score ON evidence_receipts(score DESC)")
            conn.commit()

    def add_url(self, url: str, source_type: str, query: str = "", priority: int = 5) -> bool:
        if not url or not url.startswith("http"):
            return False
        # Normalize
        url = url.split("#")[0].strip()
        try:
            with self._get_conn() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT OR IGNORE INTO url_queue (url, source_type, query, priority)
                    VALUES (?, ?, ?, ?)
                """, (url, source_type, query, priority))
                conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            logger.debug(f"Error adding URL {url}: {e}")
            return False

    def get_next_batch(self, limit: int = 10) -> List[sqlite3.Row]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT url, source_type, query FROM url_queue
                WHERE status = 'pending'
                ORDER BY priority DESC, added_at ASC
                LIMIT ?
            """, (limit,))
            rows = cur.fetchall()
            if rows:
                urls = [r["url"] for r in rows]
                placeholders = ",".join("?" for _ in urls)
                cur.execute(f"""
                    UPDATE url_queue
                    SET status = 'visiting', last_attempt = CURRENT_TIMESTAMP
                    WHERE url IN ({placeholders})
                """, urls)
                conn.commit()
            return rows

    def mark_url(self, url: str, status: str, error_msg: Optional[str] = None):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE url_queue
                SET status = ?, error_msg = ?, last_attempt = CURRENT_TIMESTAMP
                WHERE url = ?
            """, (status, error_msg, url))
            conn.commit()

    def save_source(self, data: Dict[str, Any]) -> int:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO crawled_sources 
                (url, title, domain, author, published_date, source_type, has_evidence, 
                 content_hash, word_count, overall_score, markdown_filename)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["url"], data.get("title", ""), data.get("domain", ""),
                data.get("author", ""), data.get("published_date", ""),
                data.get("source_type", "web"), data.get("has_evidence", 0),
                data.get("content_hash", ""), data.get("word_count", 0),
                data.get("overall_score", 0.0), data.get("markdown_filename", "")
            ))
            source_id = cur.lastrowid
            conn.commit()
            return source_id

    def save_receipt(self, receipt: Dict[str, Any]):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO evidence_receipts 
                (source_id, url, quote_text, equation_snippet, faith_terms, math_terms, score, score_breakdown)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                receipt.get("source_id"), receipt["url"], receipt["quote_text"],
                receipt.get("equation_snippet", ""), receipt.get("faith_terms", ""),
                receipt.get("math_terms", ""), receipt.get("score", 0.0),
                json.dumps(receipt.get("breakdown", {}))
            ))
            conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM url_queue")
            total_discovered = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM url_queue WHERE status = 'crawled'")
            total_crawled = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM url_queue WHERE status = 'failed'")
            total_failed = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM url_queue WHERE status = 'pending'")
            total_pending = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM crawled_sources WHERE has_evidence = 1")
            sources_with_evidence = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM evidence_receipts")
            total_receipts = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT domain) FROM crawled_sources")
            distinct_domains = cur.fetchone()[0]

            return {
                "total_discovered": total_discovered,
                "total_crawled": total_crawled,
                "total_failed": total_failed,
                "total_pending": total_pending,
                "sources_with_evidence": sources_with_evidence,
                "total_receipts": total_receipts,
                "distinct_domains": distinct_domains
            }

    def get_top_receipts(self, limit: int = 100) -> List[sqlite3.Row]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT r.*, s.title, s.domain, s.published_date, s.author, s.markdown_filename
                FROM evidence_receipts r
                LEFT JOIN crawled_sources s ON r.source_id = s.id
                ORDER BY r.score DESC
                LIMIT ?
            """, (limit,))
            return cur.fetchall()

# -----------------------------------------------------------------------------
# MULTI-SOURCE DISCOVERY MODULE
# -----------------------------------------------------------------------------
class DiscoveryEngine:
    """Discovers 1,000s of candidates from OpenAlex, arXiv, Crossref, and DuckDuckGo."""
    def __init__(self, db: EvidenceDatabase):
        self.db = db
        self.headers = {
            "User-Agent": "ResearchEvidenceEngine/2.0 (Theophysics Research Initiative; mailto:contact@theophysics.org)"
        }

    async def discover_openalex(self, query: str, max_results: int = 100):
        """Query OpenAlex API for open academic papers & books."""
        url = f"https://api.openalex.org/works?search={quote_plus(query)}&per-page={min(max_results, 100)}"
        logger.info(f"[Discovery:OpenAlex] Searching '{query}'...")
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=20) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get("results", [])
                        count = 0
                        for item in results:
                            # Primary landing URL or open access URL
                            doi = item.get("doi")
                            oa = item.get("open_access", {})
                            oa_url = oa.get("oa_url")
                            best_url = oa_url or doi or (item.get("primary_location") or {}).get("landing_page_url")
                            if best_url:
                                added = self.db.add_url(best_url, source_type="academic_openalex", query=query, priority=8)
                                if added:
                                    count += 1
                        logger.info(f"[Discovery:OpenAlex] Discovered {count} academic links for '{query}'.")
        except Exception as e:
            logger.warning(f"[Discovery:OpenAlex] Error querying '{query}': {e}")

    async def discover_arxiv(self, query: str, max_results: int = 50):
        """Query arXiv API for math, logic, and quantum cosmology preprints."""
        url = f"http://export.arxiv.org/api/query?search_query=all:{quote_plus(query)}&max_results={max_results}"
        logger.info(f"[Discovery:arXiv] Searching '{query}'...")
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=20) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        soup = BeautifulSoup(text, "xml")
                        entries = soup.find_all("entry")
                        count = 0
                        for entry in entries:
                            link = entry.find("id")
                            if link and link.text:
                                paper_url = link.text.strip()
                                added = self.db.add_url(paper_url, source_type="academic_arxiv", query=query, priority=9)
                                if added:
                                    count += 1
                        logger.info(f"[Discovery:arXiv] Discovered {count} preprints for '{query}'.")
        except Exception as e:
            logger.warning(f"[Discovery:arXiv] Error querying arXiv: {e}")

    async def discover_crossref(self, query: str, max_results: int = 50):
        """Query Crossref API for peer-reviewed journal papers."""
        url = f"https://api.crossref.org/works?query={quote_plus(query)}&rows={max_results}"
        logger.info(f"[Discovery:Crossref] Searching '{query}'...")
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=20) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        items = data.get("message", {}).get("items", [])
                        count = 0
                        for item in items:
                            doi = item.get("DOI")
                            resource = item.get("resource", {}).get("primary", {}).get("URL")
                            target_url = resource or (f"https://doi.org/{doi}" if doi else None)
                            if target_url:
                                added = self.db.add_url(target_url, source_type="academic_crossref", query=query, priority=7)
                                if added:
                                    count += 1
                        logger.info(f"[Discovery:Crossref] Discovered {count} DOI links for '{query}'.")
        except Exception as e:
            logger.warning(f"[Discovery:Crossref] Error querying Crossref: {e}")

    async def discover_duckduckgo(self, query: str, max_results: int = 30):
        """Query DuckDuckGo HTML for web & specialist pages."""
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://html.duckduckgo.com/"
        }
        logger.info(f"[Discovery:DuckDuckGo] Searching '{query}'...")
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, "html.parser")
                        links = soup.find_all("a", class_="result__url")
                        count = 0
                        for a in links:
                            raw_href = a.get("href", "").strip()
                            if "uddg=" in raw_href:
                                import urllib.parse
                                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                                actual_url = parsed.get("uddg", [""])[0]
                                if actual_url.startswith("http"):
                                    added = self.db.add_url(actual_url, source_type="web_search", query=query, priority=6)
                                    if added:
                                        count += 1
                        logger.info(f"[Discovery:DuckDuckGo] Discovered {count} web links for '{query}'.")
        except Exception as e:
            logger.warning(f"[Discovery:DuckDuckGo] Error: {e}")

    async def run_initial_discovery(self, queries: Optional[List[str]] = None):
        """Run discovery across all default queries."""
        q_list = queries or DEFAULT_DISCOVERY_QUERIES
        logger.info(f"[Discovery] Initializing discovery across {len(q_list)} research queries...")
        for q in q_list:
            await self.discover_openalex(q, max_results=40)
            await asyncio.sleep(1.0)
            await self.discover_arxiv(q, max_results=25)
            await asyncio.sleep(1.0)
            await self.discover_crossref(q, max_results=25)
            await asyncio.sleep(1.0)
            await self.discover_duckduckgo(q, max_results=20)
            await asyncio.sleep(2.0)

# -----------------------------------------------------------------------------
# 8-SIGNAL EVIDENCE SCORER
# -----------------------------------------------------------------------------
class EvidenceScorer:
    """Computes the 8-signal transparent quality score."""

    @staticmethod
    def score(text: str, url: str, faith_matches: List[str], math_matches: List[str], 
              author: str, date: str, domain: str) -> Tuple[float, Dict[str, float]]:
        # 1. Relevance to exact question (30% weight)
        # Co-occurrence density within sliding windows
        co_density = min(len(faith_matches) * len(math_matches), 100) / 100.0
        relevance_score = 30.0 * co_density

        # 2. Primary-source status (20% weight)
        # Papers, original treatises, direct academic papers vs secondary aggregate blogs
        primary_score = 10.0
        if any(d in domain for d in [".edu", ".ac.uk", "arxiv.org", "doi.org", "springer", "cambridge.org", "oxford"]):
            primary_score = 20.0
        elif any(d in domain for d in ["plato.stanford.edu", "iep.utm.edu", "jstor.org"]):
            primary_score = 18.0
        elif len(author) > 2:
            primary_score = 14.0

        # 3. Authority and provenance (15% weight)
        authority_score = 7.5
        if any(d in domain for d in [".edu", "stanford.edu", "mit.edu", "ox.ac.uk", "cam.ac.uk", "arxiv.org"]):
            authority_score = 15.0
        elif any(d in domain for d in ["reasonablefaith.org", "philpapers.org", "nature.com"]):
            authority_score = 12.5

        # 4. Independent corroboration (10% weight)
        # Footnotes, bibliography, citation patterns
        citations_found = len(re.findall(r"\[\d+\]|\(\w+,\s*\d{4}\)", text))
        corroboration_score = min(10.0, (citations_found / 10.0) * 10.0)

        # 5. Evidence and citation density (10% weight)
        math_count = len(math_matches)
        math_density_score = min(10.0, (math_count / 5.0) * 10.0)

        # 6. Historical or archival value (5% weight)
        archival_score = 2.5
        if any(name in text.lower() for name in ["leibniz", "euler", "newton", "cantor", "pascal", "gödel", "godel"]):
            archival_score = 5.0

        # 7. Recency or chronological grounding (5% weight)
        recency_score = 3.0
        if date:
            try:
                year = int(re.search(r"\b(19\d\d|20\d\d)\b", date).group(1))
                if year >= 2015:
                    recency_score = 5.0
                elif year >= 2000:
                    recency_score = 4.0
                else:
                    recency_score = 3.5
            except Exception:
                pass

        # 8. Accessibility & formula extractability (5% weight)
        has_latex = 1 if re.search(r"\$\$|\$|\\begin\{equation\}", text) else 0
        extractability_score = 5.0 if has_latex else 2.5

        total = (relevance_score + primary_score + authority_score + 
                 corroboration_score + math_density_score + archival_score + 
                 recency_score + extractability_score)
        
        breakdown = {
            "relevance_30": round(relevance_score, 1),
            "primary_source_20": round(primary_score, 1),
            "authority_15": round(authority_score, 1),
            "corroboration_10": round(corroboration_score, 1),
            "evidence_density_10": round(math_density_score, 1),
            "archival_5": round(archival_score, 1),
            "recency_5": round(recency_score, 1),
            "extractability_5": round(extractability_score, 1)
        }
        return round(total, 2), breakdown

# -----------------------------------------------------------------------------
# EVIDENCE EXTRACTION & PARSING
# -----------------------------------------------------------------------------
class ContentExtractor:
    @staticmethod
    def extract_evidence_receipts(text: str, url: str) -> List[Dict[str, Any]]:
        """Scans paragraphs for co-occurrences of Faith terms AND Math formalisms."""
        paragraphs = re.split(r"\n\s*\n", text)
        receipts = []

        for p in paragraphs:
            clean_p = p.strip()
            if len(clean_p) < 60:
                continue

            faith_finds = list(set(FAITH_REGEX.findall(clean_p)))
            math_finds = list(set(MATH_REGEX.findall(clean_p)))

            if faith_finds and math_finds:
                # Find mathematical snippet
                equation_snippet = ""
                for m in math_finds:
                    if len(m) > len(equation_snippet):
                        equation_snippet = m.strip()

                receipts.append({
                    "quote_text": clean_p,
                    "equation_snippet": equation_snippet[:200],
                    "faith_terms": ", ".join(faith_finds[:5]),
                    "math_terms": ", ".join(math_finds[:5]),
                    "faith_count": len(faith_finds),
                    "math_count": len(math_finds)
                })

        return receipts

# -----------------------------------------------------------------------------
# CONTINUOUS WORKER (The Polite Crawling Loop)
# -----------------------------------------------------------------------------
class ContinuousEvidenceCrawler:
    def __init__(self):
        self.db = EvidenceDatabase(DB_PATH)
        self.discovery = DiscoveryEngine(self.db)
        self.scorer = EvidenceScorer()
        self.extractor = ContentExtractor()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

    async def crawl_page(self, session: aiohttp.ClientSession, url: str, source_type: str) -> Optional[Dict[str, Any]]:
        domain = urlparse(url).netloc
        try:
            async with session.get(url, timeout=25, allow_redirects=True) as resp:
                if resp.status != 200:
                    self.db.mark_url(url, "failed", f"HTTP {resp.status}")
                    return None

                content_type = resp.headers.get("Content-Type", "")
                
                # Check for PDF
                if "application/pdf" in content_type or url.lower().endswith(".pdf"):
                    # Note: Handle PDF binary extraction if needed
                    self.db.mark_url(url, "skipped", "PDF direct binary (queued for docling/tika)")
                    return None

                html = await resp.text(errors="replace")
                soup = BeautifulSoup(html, "html.parser")

                # Strip script, style, nav
                for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    tag.decompose()

                title = soup.title.string.strip() if soup.title and soup.title.string else domain
                text = soup.get_text(separator="\n", strip=True)
                words = len(text.split())

                if words < 100:
                    self.db.mark_url(url, "crawled", "Low word count")
                    return None

                content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

                # Extract receipts
                receipts = self.extractor.extract_evidence_receipts(text, url)
                has_evidence = 1 if len(receipts) > 0 else 0

                # Score source
                all_faith = list(set(FAITH_REGEX.findall(text)))
                all_math = list(set(MATH_REGEX.findall(text)))
                score, breakdown = self.scorer.score(
                    text=text, url=url, faith_matches=all_faith, math_matches=all_math,
                    author="", date="", domain=domain
                )

                # Save markdown representation
                safe_slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", domain + "_" + title[:40])[:60]
                md_filename = f"{safe_slug}.md"
                md_path = SOURCES_DIR / md_filename

                frontmatter = f"""---
url: "{url}"
title: "{title}"
domain: "{domain}"
source_type: "{source_type}"
has_evidence: {bool(has_evidence)}
score: {score}
crawled_at: "{datetime.now(timezone.utc).isoformat()}"
faith_matches: {len(all_faith)}
math_matches: {len(all_math)}
---

# {title}

**Source:** [{url}]({url})  
**Evidence Score:** {score}/100  
**Domain:** `{domain}`  

## Extracted Evidence Receipts ({len(receipts)} found):

"""
                for i, r in enumerate(receipts, 1):
                    frontmatter += f"""### Receipt #{i}
> {r['quote_text']}

- **Faith Terms:** `{r['faith_terms']}`
- **Math Formalisms:** `{r['math_terms']}`
- **Formula Snippet:** `{r['equation_snippet']}`

---
"""
                frontmatter += f"\n## Full Extracted Text\n\n{text[:15000]}\n"
                
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(frontmatter)

                source_record = {
                    "url": url,
                    "title": title,
                    "domain": domain,
                    "author": "",
                    "published_date": "",
                    "source_type": source_type,
                    "has_evidence": has_evidence,
                    "content_hash": content_hash,
                    "word_count": words,
                    "overall_score": score,
                    "markdown_filename": md_filename
                }
                source_id = self.db.save_source(source_record)

                # Save individual receipts
                for r in receipts:
                    r["source_id"] = source_id
                    r["url"] = url
                    r_score, r_breakdown = self.scorer.score(
                        text=r["quote_text"], url=url, 
                        faith_matches=[r["faith_terms"]], math_matches=[r["math_terms"]],
                        author="", date="", domain=domain
                    )
                    r["score"] = r_score
                    r["breakdown"] = r_breakdown
                    self.db.save_receipt(r)

                self.db.mark_url(url, "crawled")

                if has_evidence:
                    logger.info(f"💎 [EVIDENCE FOUND] {title[:45]} | Score: {score} | {len(receipts)} receipts")
                    # Synchronize to Vault
                    self.sync_to_vault(md_path, md_filename)
                else:
                    logger.info(f"✓ Crawled: {title[:40]} (No math+faith intersection)")

                return source_record

        except asyncio.TimeoutError:
            self.db.mark_url(url, "failed", "Timeout (25s)")
        except Exception as e:
            self.db.mark_url(url, "failed", str(e)[:100])
        return None

    def sync_to_vault(self, local_file: Path, filename: str):
        """Mirrors evidence into Z:\\Theophysics_Vault per rule."""
        if VAULT_EVIDENCE_DIR.exists():
            try:
                dest = VAULT_EVIDENCE_DIR / filename
                import shutil
                shutil.copy2(local_file, dest)
            except Exception as e:
                logger.debug(f"Vault copy notice: {e}")

    async def run_continuous_crawl(self, max_pages: Optional[int] = None, delay_between_requests: float = 1.5):
        """The main continuous loop. Can run indefinitely or for a designated quota."""
        logger.info("=================================================================")
        logger.info("    STARTING THEOPHYSICS & BIBLICAL MATHEMATICS EVIDENCE ENGINE   ")
        logger.info("=================================================================")
        
        # Check if queue has items; if not, seed it
        stats = self.db.get_stats()
        if stats["total_pending"] == 0:
            logger.info("Queue is empty. Running initial discovery seeds...")
            await self.discovery.run_initial_discovery()

        pages_crawled = 0
        conn = aiohttp.TCPConnector(limit_per_host=2)
        async with aiohttp.ClientSession(connector=conn, headers=self.headers) as session:
            while True:
                if max_pages and pages_crawled >= max_pages:
                    logger.info(f"Target page count ({max_pages}) reached. Pausing crawl.")
                    break

                batch = self.db.get_next_batch(limit=5)
                if not batch:
                    logger.info("Queue exhausted. Expanding candidate discovery...")
                    await self.discovery.run_initial_discovery()
                    batch = self.db.get_next_batch(limit=5)
                    if not batch:
                        logger.info("No more URLs discovered. Waiting 30 seconds before re-checking...")
                        await asyncio.sleep(30)
                        continue

                tasks = [self.crawl_page(session, row["url"], row["source_type"]) for row in batch]
                await asyncio.gather(*tasks)
                pages_crawled += len(batch)

                # Periodic report update every 10 pages
                if pages_crawled % 10 == 0:
                    self.export_reports()

                await asyncio.sleep(delay_between_requests)

    def export_reports(self):
        """Compiles transparent Top 100 Evidence Report and master CSV index."""
        top_receipts = self.db.get_top_receipts(limit=100)
        stats = self.db.get_stats()

        # 1. Master Evidence Report
        report_path = OUTPUT_DIR / "00_TOP_100_RANKED_EVIDENCE.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# 🏆 Top 100 Biblical Mathematics & Theophysics Evidence Receipts\n\n")
            f.write(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  \n")
            f.write(f"**Pages Crawled:** {stats['total_crawled']} | **Evidence Items Found:** {stats['total_receipts']} | **Domains:** {stats['distinct_domains']}\n\n")
            f.write("Scored using the 8-Signal Matrix: Relevance (30%), Primary-source (20%), Authority (15%), Corroboration (10%), Density (10%), Archival (5%), Recency (5%), Extractability (5%).\n\n")
            f.write("---\n\n")

            for idx, r in enumerate(top_receipts, 1):
                f.write(f"## {idx}. [{r['title'] or r['domain']}]({r['url']})\n\n")
                f.write(f"- **Evidence Score:** `{r['score']}/100`\n")
                f.write(f"- **Domain:** `{r['domain']}`\n")
                f.write(f"- **Formula Snippet:** `{r['equation_snippet']}`\n")
                f.write(f"- **Faith Lexicon:** `{r['faith_terms']}`\n")
                f.write(f"- **Math Lexicon:** `{r['math_terms']}`\n\n")
                f.write(f"> **Exact Quotation:**  \n> {r['quote_text']}\n\n")
                if r['markdown_filename']:
                    f.write(f"*Full preserved document: [sources/{r['markdown_filename']}](file:///{SOURCES_DIR / r['markdown_filename']})*\n\n")
                f.write("---\n\n")

        # 2. Master CSV Index
        import csv
        csv_path = OUTPUT_DIR / "00_EVIDENCE_INDEX.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Score", "Title", "Domain", "URL", "Equation_Snippet", "Faith_Terms", "Math_Terms", "Quote_Excerpt"])
            for r in top_receipts:
                writer.writerow([
                    r["id"], r["score"], r["title"], r["domain"], r["url"],
                    r["equation_snippet"], r["faith_terms"], r["math_terms"],
                    r["quote_text"][:250].replace("\n", " ")
                ])

        # Mirror to Vault
        if VAULT_EVIDENCE_DIR.exists():
            try:
                import shutil
                shutil.copy2(report_path, VAULT_EVIDENCE_DIR / "00_TOP_100_RANKED_EVIDENCE.md")
                shutil.copy2(csv_path, VAULT_EVIDENCE_DIR / "00_EVIDENCE_INDEX.csv")
            except Exception:
                pass

        logger.info(f"📊 [REPORT UPDATED] Top 100 evidence compiled to {report_path.name}")


# -----------------------------------------------------------------------------
# CLI ENTRY POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    crawler = ContinuousEvidenceCrawler()
    
    # Check arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        s = crawler.db.get_stats()
        print(json.dumps(s, indent=2))
        crawler.export_reports()
    elif len(sys.argv) > 1 and sys.argv[1] == "--query":
        custom_q = sys.argv[2]
        print(f"Running targeted discovery for: {custom_q}")
        asyncio.run(crawler.discovery.run_initial_discovery([custom_q]))
        asyncio.run(crawler.run_continuous_crawl(max_pages=20))
    elif len(sys.argv) > 1 and sys.argv[1] == "--export":
        crawler.export_reports()
        print("Reports exported successfully.")
    else:
        # Continuous run
        try:
            asyncio.run(crawler.run_continuous_crawl())
        except KeyboardInterrupt:
            logger.info("Crawl paused by user. State saved in database. Resume anytime!")
            crawler.export_reports()
