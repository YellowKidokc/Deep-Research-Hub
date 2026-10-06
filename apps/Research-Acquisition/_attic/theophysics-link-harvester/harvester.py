"""
TEMPLATE: Theophysics Link Harvester
=====================================
GENERALIZED link discovery template. Edit ONLY the CONFIG section below.
Searches multiple engines, collects links, grades them with fringe-priority
hierarchy, and writes to PostgreSQL + markdown output.

HOW TO USE:
1. Edit SEARCH_TERMS with your topics
2. Pick your ENGINE (google_scholar, semantic_scholar, arxiv, duckduckgo, etc.)
3. Optionally add DIRECT_URLS if you already have specific pages to harvest
4. Run it

Grading system (fringe-priority = higher score for less mainstream):
  A+ (90-100) = Fringe/heterodox, interdisciplinary, <50 citations, buried
  A  (80-89)  = Non-mainstream journal, cross-domain, unconventional
  B  (70-79)  = Edge of mainstream, some interdisciplinary elements
  C  (60-69)  = Standard academic, well-cited, single domain
  D  (50-59)  = Textbook/establishment, >1000 citations, no cross-domain

POF 2828 | April 2026
"""

import subprocess
import sys
subprocess.check_call([sys.executable, '-m', 'pip', 'install',
    'requests', 'beautifulsoup4', 'psycopg2-binary', '-q'])

import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
import traceback
from urllib.parse import urlparse, quote_plus, urljoin, parse_qs
from datetime import datetime

try:
    from crawlab import save_item
except:
    def save_item(item):
        pass

import psycopg2

# ============================================================
# ██████  CONFIG — EDIT THIS SECTION  ██████
# ============================================================

CONFIG = {
    # --------------------------------------------------------
    # SEARCH TERMS — Put your topics here, one per line
    # --------------------------------------------------------
    'search_terms': [
        "cross-domain isomorphism physics theology",
        "information as substrate consciousness",
        "morphogenetic fields bioelectric patterns",
        "Wigner unreasonable effectiveness mathematics",
        "it from bit Wheeler information physics",
        "Landauer information is physical",
        "is-ought problem naturalistic fallacy bridge",
        "moral realism structural grounding",
        "truth as substrate reality",
        "convergent discovery independent mathematics",
        "cooperation game theory iterated prisoners dilemma",
        "cross-cultural moral universals anthropology",
        "psychopathy moral cognition Blair",
        "entropy information degradation coherence",
        "Godel incompleteness truth transcends formal systems",
        "fine tuning constants anthropic principle",
        "consciousness hard problem integrated information",
        "Axelrod cooperation evolution tit for tat",
    ],

    # --------------------------------------------------------
    # ENGINE — Pick your search source
    # Options: 'semantic_scholar', 'duckduckgo', 'arxiv', 'openalex'
    # --------------------------------------------------------
    'engine': 'semantic_scholar',

    # --------------------------------------------------------
    # MAX RESULTS per search term
    # --------------------------------------------------------
    'max_results_per_term': 50,

    # --------------------------------------------------------
    # DIRECT URLS — Already have pages full of links? Paste them here.
    # The harvester will also crawl these and extract all links found.
    # Leave empty [] if you only want search results.
    # --------------------------------------------------------
    'direct_urls': [
        # "https://fqxi.org/community/forum/category/",
        # "https://www.santafe.edu/research/results/working-papers",
        # "https://philpapers.org/browse/philosophy-of-physics",
    ],

    # --------------------------------------------------------
    # FRINGE PRIORITY KEYWORDS — Boost score for links containing these
    # --------------------------------------------------------
    'fringe_boost_keywords': [
        'interdisciplinary', 'cross-domain', 'heterodox', 'anomalous',
        'isomorphism', 'emergence', 'consciousness', 'information',
        'morphic', 'bioelectric', 'wholeness', 'implicate order',
        'process philosophy', 'cybernetics', 'systems theory',
        'self-organization', 'coherence', 'structural identity',
        'unification', 'substrate', 'observer', 'panpsychism',
    ],

    # --------------------------------------------------------
    # MAINSTREAM PENALTY KEYWORDS — Lower score for these
    # --------------------------------------------------------
    'mainstream_penalty_keywords': [
        'textbook', 'introduction to', 'undergraduate', 'standard model',
        'well-established', 'review article', 'handbook',
    ],

    # --------------------------------------------------------
    # FRINGE BOOST DOMAINS — Sites that get automatic score boost
    # --------------------------------------------------------
    'fringe_boost_domains': [
        'fqxi.org', 'vixra.org', 'edge.org', 'santafe.edu',
        'mdpi.com/journal/entropy', 'mdpi.com/journal/symmetry',
        'scientificexploration.org', 'process.org',
        'cosmosandhistory.org', 'neuroquantology.com',
        'physicsessays.org', 'zfrn.org',
    ],

    # --------------------------------------------------------
    # MAINSTREAM PENALTY DOMAINS — Sites that get score lowered
    # --------------------------------------------------------
    'mainstream_penalty_domains': [
        'nature.com', 'science.org', 'aps.org',
    ],

    # --------------------------------------------------------
    # THEOPHYSICS CONCEPT TAGS — Auto-tag links matching these
    # --------------------------------------------------------
    'concept_keywords': {
        'master_equation': ['master equation', 'chi', 'unified equation',
            'governing equation', 'fundamental equation'],
        'cross_domain_isomorphism': ['isomorphism', 'structural identity',
            'cross-domain', 'homomorphism', 'correspondence',
            'parallel structure', 'mapping between'],
        'information_as_substrate': ['information is physical', 'it from bit',
            'information substrate', 'digital physics',
            'computational universe', 'Landauer', 'Wheeler'],
        'consciousness_as_variable': ['consciousness', 'observer',
            'measurement problem', 'observer effect', 'hard problem',
            'qualia', 'panpsychism', 'integrated information'],
        'entropy_as_adversary': ['entropy', 'disorder', 'second law',
            'thermodynamic', 'dissipative', 'irreversibility'],
        'conservation_of_coherence': ['coherence', 'entanglement',
            'quantum coherence', 'decoherence', 'phase coherence'],
        'ten_laws': ['conservation law', 'symmetry', 'invariance',
            'universality', 'natural law', 'fundamental law'],
    },

    # --------------------------------------------------------
    # OUTPUT OPTIONS
    # --------------------------------------------------------
    'output_markdown': True,
    'markdown_filename': 'harvested_links.md',
    'write_to_postgres': True,

    # --------------------------------------------------------
    # RATE LIMITING (seconds between requests)
    # --------------------------------------------------------
    'delay_between_requests': 2,
}

# ============================================================
# PostgreSQL Configuration
# ============================================================
DB_CONFIG = {
    'host': os.environ.get('POSTGRES_HOST', '192.168.1.177'),
    'port': int(os.environ.get('POSTGRES_PORT', '2665')),
    'database': os.environ.get('POSTGRES_DB', 'crawlab_data'),
    'user': os.environ.get('POSTGRES_USER', 'root'),
    'password': os.environ.get('POSTGRES_PASSWORD', 'Moss9pep28'),
}

# ============================================================
# HTTP Session Setup
# ============================================================
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def get_db():
    return psycopg2.connect(**DB_CONFIG)

def ensure_tables():
    """Create harvested_links table if not exists."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS harvested_links (
            id SERIAL PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT,
            source_category TEXT,
            source_name TEXT,
            found_on_page TEXT,
            concepts_matched TEXT,
            link_text TEXT,
            discovery_date TIMESTAMP DEFAULT NOW(),
            scraped BOOLEAN DEFAULT FALSE,
            priority INTEGER DEFAULT 5,
            fringe_score INTEGER DEFAULT 50,
            grade TEXT DEFAULT 'C',
            search_term TEXT,
            engine TEXT,
            notes TEXT,
            pillar_tag TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_harvested_url ON harvested_links(url);
        CREATE INDEX IF NOT EXISTS idx_harvested_scraped ON harvested_links(scraped);
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("  Ensured harvested_links table exists")

def link_exists(url):
    """Check if a URL is already in the database."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM harvested_links WHERE url = %s", (url,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count > 0

def insert_link(data):
    """Insert a harvested link into PostgreSQL."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO harvested_links
            (url, title, source_category, source_name, found_on_page,
             concepts_matched, link_text, search_term, engine,
             priority, fringe_score, grade, notes, pillar_tag)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('url'), data.get('title'), data.get('source_category'),
            data.get('source_name'), data.get('found_on_page'),
            data.get('concepts_matched'), data.get('link_text'),
            data.get('search_term'), data.get('engine'),
            data.get('priority', 5), data.get('fringe_score', 50),
            data.get('grade', 'C'), data.get('notes', ''),
            data.get('pillar_tag', ''),
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"  DB insert error: {e}")
    finally:
        cur.close()
        conn.close()

# ============================================================
# SCORING ENGINE — Fringe Priority Grading
# ============================================================
def calculate_fringe_score(url, title, snippet='', source_engine=''):
    """
    Score a link from 0-100 where HIGHER = more fringe/valuable.
    This is the INVERSE of how most people rank papers.
    """
    score = 50
    text_lower = (title + ' ' + snippet + ' ' + url).lower()
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Fringe domain boost (+15)
    for fd in CONFIG.get('fringe_boost_domains', []):
        if fd in domain:
            score += 15
            break

    # Mainstream domain penalty (-10)
    for md in CONFIG.get('mainstream_penalty_domains', []):
        if md in domain:
            score -= 10
            break

    # Fringe keyword boost (+3 each, max +30)
    fringe_hits = 0
    for kw in CONFIG.get('fringe_boost_keywords', []):
        if kw.lower() in text_lower:
            fringe_hits += 1
    score += min(fringe_hits * 3, 30)

    # Mainstream keyword penalty (-5 each, max -20)
    mainstream_hits = 0
    for kw in CONFIG.get('mainstream_penalty_keywords', []):
        if kw.lower() in text_lower:
            mainstream_hits += 1
    score -= min(mainstream_hits * 5, 20)

    # Cross-domain bonus: if title contains words from 2+ different concept areas
    concept_areas_hit = 0
    for concept_key, keywords in CONFIG.get('concept_keywords', {}).items():
        if any(kw.lower() in text_lower for kw in keywords):
            concept_areas_hit += 1
    if concept_areas_hit >= 2:
        score += 15
    elif concept_areas_hit == 1:
        score += 5

    # Preprint / working paper boost
    if any(x in text_lower for x in ['preprint', 'working paper', 'arxiv', 'vixra', 'fqxi essay']):
        score += 5

    # Old/buried paper boost
    year_match = re.search(r'(19[5-8]\d|199\d|200[0-5])', text_lower)
    if year_match:
        year = int(year_match.group(1))
        if year < 1980:
            score += 10
        elif year < 2000:
            score += 5

    # Clamp to 0-100
    score = max(0, min(100, score))
    return score

def score_to_grade(score):
    if score >= 90: return 'A+'
    elif score >= 80: return 'A'
    elif score >= 70: return 'B'
    elif score >= 60: return 'C'
    else: return 'D'

def match_concepts(text):
    """Find which theophysics concepts are mentioned in the text."""
    text_lower = text.lower()
    matched = {}
    for concept_key, keywords in CONFIG.get('concept_keywords', {}).items():
        hits = [kw for kw in keywords if kw.lower() in text_lower]
        if hits:
            matched[concept_key] = hits
    return matched

# ============================================================
# SEARCH ENGINE IMPLEMENTATIONS
# ============================================================

def search_semantic_scholar(term, max_results=50):
    """Search Semantic Scholar API (free, no key needed)."""
    results = []
    offset = 0
    per_page = min(max_results, 100)

    while len(results) < max_results:
        try:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                'query': term,
                'offset': offset,
                'limit': per_page,
                'fields': 'title,url,abstract,year,citationCount,journal,authors'
            }
            resp = session.get(url, params=params, timeout=30)
            if resp.status_code == 429:
                print("  Rate limited, waiting 60s...")
                time.sleep(60)
                continue
            resp.raise_for_status()
            data = resp.json()

            papers = data.get('data', [])
            if not papers:
                break

            for paper in papers:
                results.append({
                    'url': paper.get('url', ''),
                    'title': paper.get('title', ''),
                    'snippet': (paper.get('abstract', '') or '')[:500],
                    'year': paper.get('year'),
                    'citations': paper.get('citationCount', 0),
                    'journal': (paper.get('journal') or {}).get('name', ''),
                    'authors': ', '.join([a.get('name', '') for a in (paper.get('authors') or [])[:5]]),
                    'source_engine': 'semantic_scholar',
                })

            offset += per_page
            if offset >= data.get('total', 0):
                break
            time.sleep(CONFIG.get('delay_between_requests', 2))

        except Exception as e:
            print(f"  Semantic Scholar error: {e}")
            break

    return results[:max_results]

def search_duckduckgo(term, max_results=50):
    """Search DuckDuckGo HTML (no API key needed)."""
    results = []
    try:
        url = "https://html.duckduckgo.com/html/"
        resp = session.post(url, data={'q': term}, timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')

        for result in soup.select('.result__body'):
            link = result.select_one('.result__a')
            snippet_el = result.select_one('.result__snippet')
            if link:
                href = link.get('href', '')
                # DDG wraps URLs
                if 'uddg=' in href:
                    parsed_qs = parse_qs(urlparse(href).query)
                    href = parsed_qs.get('uddg', [href])[0]

                results.append({
                    'url': href,
                    'title': link.get_text(strip=True),
                    'snippet': snippet_el.get_text(strip=True) if snippet_el else '',
                    'source_engine': 'duckduckgo',
                })

            if len(results) >= max_results:
                break
    except Exception as e:
        print(f"  DuckDuckGo error: {e}")
    return results

def search_arxiv(term, max_results=50):
    """Search arXiv API."""
    results = []
    try:
        url = "http://export.arxiv.org/api/query"
        params = {
            'search_query': f'all:{term}',
            'start': 0,
            'max_results': max_results,
            'sortBy': 'relevance',
        }
        resp = session.get(url, params=params, timeout=30)
        soup = BeautifulSoup(resp.text, 'xml')

        for entry in soup.find_all('entry'):
            title = entry.find('title')
            summary = entry.find('summary')
            link = entry.find('id')
            authors = entry.find_all('author')

            results.append({
                'url': link.get_text(strip=True) if link else '',
                'title': title.get_text(strip=True) if title else '',
                'snippet': (summary.get_text(strip=True) if summary else '')[:500],
                'authors': ', '.join([a.find('name').get_text(strip=True) for a in authors[:5]]) if authors else '',
                'source_engine': 'arxiv',
            })
    except Exception as e:
        print(f"  arXiv error: {e}")
    return results

def search_openalex(term, max_results=50):
    """Search OpenAlex API (free, open scholarly data)."""
    results = []
    try:
        url = "https://api.openalex.org/works"
        params = {
            'search': term,
            'per_page': min(max_results, 200),
            'mailto': 'research@example.com',
        }
        resp = session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        for work in data.get('results', []):
            results.append({
                'url': work.get('doi', work.get('id', '')),
                'title': work.get('title', ''),
                'snippet': '',
                'year': work.get('publication_year'),
                'citations': work.get('cited_by_count', 0),
                'source_engine': 'openalex',
            })
    except Exception as e:
        print(f"  OpenAlex error: {e}")
    return results[:max_results]

def harvest_direct_urls(urls):
    """Visit pages and extract all links found on them."""
    results = []
    for page_url in urls:
        try:
            print(f"  Harvesting links from: {page_url}")
            resp = session.get(page_url, timeout=30)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for a in soup.find_all('a', href=True):
                href = a.get('href', '')
                if not href or href.startswith('#') or href.startswith('javascript:'):
                    continue
                full_url = urljoin(page_url, href)
                link_text = a.get_text(strip=True)

                if len(link_text) < 5:
                    continue
                parsed = urlparse(full_url)
                if not parsed.scheme.startswith('http'):
                    continue

                results.append({
                    'url': full_url,
                    'title': link_text,
                    'snippet': '',
                    'found_on_page': page_url,
                    'source_engine': 'direct_harvest',
                })

            time.sleep(CONFIG.get('delay_between_requests', 2))
        except Exception as e:
            print(f"  Error harvesting {page_url}: {e}")
    return results

# Engine dispatcher
ENGINES = {
    'semantic_scholar': search_semantic_scholar,
    'duckduckgo': search_duckduckgo,
    'arxiv': search_arxiv,
    'openalex': search_openalex,
}

# ============================================================
# MARKDOWN OUTPUT
# ============================================================
def write_markdown(all_links, filename):
    """Write harvested links to a markdown file, sorted by fringe score."""
    sorted_links = sorted(all_links, key=lambda x: x.get('fringe_score', 0), reverse=True)

    md = []
    md.append("# Harvested Links Report")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md.append(f"**Engine:** {CONFIG['engine']}")
    md.append(f"**Total Links:** {len(sorted_links)}")
    md.append(f"**Search Terms:** {', '.join(CONFIG['search_terms'])}")
    md.append("")
    md.append("---")
    md.append("")

    # Summary by grade
    grades = {}
    for link in sorted_links:
        g = link.get('grade', 'C')
        grades[g] = grades.get(g, 0) + 1
    md.append("## Grade Distribution")
    for g in ['A+', 'A', 'B', 'C', 'D']:
        if g in grades:
            md.append(f"- **{g}**: {grades[g]} links")
    md.append("")

    # Summary by concept
    md.append("## Concept Coverage")
    concept_counts = {}
    for link in sorted_links:
        for c in link.get('concepts_list', []):
            concept_counts[c] = concept_counts.get(c, 0) + 1
    for c, count in sorted(concept_counts.items(), key=lambda x: -x[1]):
        md.append(f"- **{c}**: {count} links")
    md.append("")
    md.append("---")
    md.append("")

    # All links grouped by grade
    current_grade = None
    for link in sorted_links:
        g = link.get('grade', 'C')
        if g != current_grade:
            current_grade = g
            md.append(f"## Grade {g} Links")
            md.append("")

        md.append(f"### [{link.get('title', 'Untitled')}]({link.get('url', '')})")
        md.append(f"**Score:** {link.get('fringe_score', 50)} | **Grade:** {g}")
        if link.get('concepts_matched'):
            md.append(f"**Concepts:** {link['concepts_matched']}")
        if link.get('snippet'):
            md.append(f"> {link['snippet'][:300]}")
        if link.get('search_term'):
            md.append(f"*Found via:* {link['search_term']} ({link.get('engine', '')})")
        md.append("")

    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"  Markdown written to {filename}")

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("  THEOPHYSICS LINK HARVESTER")
    print(f"  Engine: {CONFIG['engine']}")
    print(f"  Search terms: {len(CONFIG['search_terms'])}")
    print("=" * 60)

    # Try PostgreSQL, fall back to markdown-only if DB is down
    db_available = False
    if CONFIG.get('write_to_postgres', True):
        try:
            ensure_tables()
            db_available = True
        except Exception as e:
            print(f"\n  [WARN] PostgreSQL not available: {e}")
            print("  Continuing with markdown-only output...\n")

    engine_func = ENGINES.get(CONFIG['engine'])
    if not engine_func:
        print(f"ERROR: Unknown engine '{CONFIG['engine']}'")
        print(f"Available engines: {list(ENGINES.keys())}")
        return

    all_links = []
    new_count = 0
    skip_count = 0

    # Search each term
    for i, term in enumerate(CONFIG['search_terms']):
        print(f"\n[{i+1}/{len(CONFIG['search_terms'])}] Searching: {term}")
        results = engine_func(term, CONFIG.get('max_results_per_term', 50))
        print(f"  Found {len(results)} results")

        for r in results:
            url = r.get('url', '')
            if not url:
                continue

            # Skip if already harvested (DB check)
            if db_available:
                try:
                    if link_exists(url):
                        skip_count += 1
                        continue
                except:
                    pass

            # Score it
            score = calculate_fringe_score(
                url, r.get('title', ''), r.get('snippet', ''), r.get('source_engine', '')
            )
            grade = score_to_grade(score)

            # Match concepts
            full_text = f"{r.get('title', '')} {r.get('snippet', '')}"
            concepts = match_concepts(full_text)
            concepts_str = ', '.join([
                f"{k}: {'; '.join(v)}" for k, v in concepts.items()
            ]) if concepts else ''
            concepts_list = list(concepts.keys())

            # Determine source category
            parsed = urlparse(url)
            domain = parsed.netloc
            source_cat = 'search_result'
            source_name = domain

            link_data = {
                'url': url,
                'title': r.get('title', ''),
                'source_category': source_cat,
                'source_name': source_name,
                'found_on_page': r.get('found_on_page', ''),
                'concepts_matched': concepts_str,
                'concepts_list': concepts_list,
                'link_text': r.get('title', ''),
                'search_term': term,
                'engine': CONFIG['engine'],
                'priority': 1 if score >= 80 else (3 if score >= 60 else 5),
                'fringe_score': score,
                'grade': grade,
                'snippet': r.get('snippet', ''),
                'notes': f"Year: {r.get('year', 'N/A')}, Citations: {r.get('citations', 'N/A')}, Authors: {r.get('authors', 'N/A')}",
            }

            # Save to PostgreSQL if available
            if db_available:
                try:
                    insert_link(link_data)
                except Exception as e:
                    print(f"  DB write failed: {e}")

            # Save to Crawlab
            save_item(link_data)

            all_links.append(link_data)
            new_count += 1

        time.sleep(CONFIG.get('delay_between_requests', 2))

    # Harvest direct URLs if provided
    if CONFIG.get('direct_urls'):
        print(f"\nHarvesting {len(CONFIG['direct_urls'])} direct URLs...")
        direct_results = harvest_direct_urls(CONFIG['direct_urls'])
        print(f"  Found {len(direct_results)} links from direct pages")

        for r in direct_results:
            url = r.get('url', '')
            if not url:
                continue
            if db_available:
                try:
                    if link_exists(url):
                        skip_count += 1
                        continue
                except:
                    pass

            score = calculate_fringe_score(url, r.get('title', ''), '', 'direct_harvest')
            grade = score_to_grade(score)
            full_text = r.get('title', '')
            concepts = match_concepts(full_text)
            concepts_str = ', '.join([f"{k}: {'; '.join(v)}" for k, v in concepts.items()]) if concepts else ''

            link_data = {
                'url': url,
                'title': r.get('title', ''),
                'source_category': 'direct_harvest',
                'source_name': urlparse(url).netloc,
                'found_on_page': r.get('found_on_page', ''),
                'concepts_matched': concepts_str,
                'concepts_list': list(concepts.keys()),
                'link_text': r.get('title', ''),
                'search_term': 'direct_url',
                'engine': 'direct_harvest',
                'priority': 1 if score >= 80 else (3 if score >= 60 else 5),
                'fringe_score': score,
                'grade': grade,
                'snippet': '',
                'notes': '',
            }

            if db_available:
                try:
                    insert_link(link_data)
                except:
                    pass
            save_item(link_data)
            all_links.append(link_data)
            new_count += 1

    # Write markdown
    if CONFIG.get('output_markdown', True) and all_links:
        write_markdown(all_links, CONFIG.get('markdown_filename', 'harvested_links.md'))

    # Final report
    print()
    print("=" * 60)
    print("  HARVESTING COMPLETE")
    print("=" * 60)
    print(f"  New links found: {new_count}")
    print(f"  Duplicates skipped: {skip_count}")
    print(f"  Total in this run: {len(all_links)}")

    if all_links:
        grades = {}
        for link in all_links:
            g = link.get('grade', 'C')
            grades[g] = grades.get(g, 0) + 1
        print("\n  Grade distribution:")
        for g in ['A+', 'A', 'B', 'C', 'D']:
            if g in grades:
                print(f"    {g}: {grades[g]}")

    # DB stats
    if db_available:
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM harvested_links")
            total = cur.fetchone()[0]
            cur.execute("SELECT grade, COUNT(*) FROM harvested_links GROUP BY grade ORDER BY grade")
            grade_counts = cur.fetchall()
            cur.execute("SELECT COUNT(*) FROM harvested_links WHERE scraped = FALSE")
            unscraped = cur.fetchone()[0]
            print(f"\n  Database totals:")
            print(f"    Total links: {total}")
            print(f"    Unscraped: {unscraped}")
            for row in grade_counts:
                print(f"    Grade {row[0]}: {row[1]}")
            cur.close()
            conn.close()
        except Exception as e:
            print(f"  Error reading DB stats: {e}")

if __name__ == '__main__':
    main()
