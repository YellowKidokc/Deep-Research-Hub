# CRAWL4AI Research Prompt — Generic Template
# Usage: Fill in {{TOPIC}} and {{VAULT_PATH}} then give to Claude/Haiku

## INSTRUCTIONS

You are a research assistant. Your job is to crawl web pages about a specific topic, download them as clean markdown, and organize them in an Obsidian vault.

### TOPIC: {{TOPIC}}
### VAULT DESTINATION: {{VAULT_PATH}}
### CRAWL4AI LOCATION: D:\GitHub\crawl4ai

---

## STEP 1: Search and Build URL List

Search the web for high-quality sources on: **{{TOPIC}}**

Prioritize:
- Peer-reviewed papers and academic sources
- Stanford Encyclopedia of Philosophy
- Primary source documents
- High-quality explainers (not clickbait)
- Both FOR and AGAINST perspectives

Build a list of 10-20 URLs. Save them to:
`D:\GitHub\crawl4ai\urls_{{TOPIC_SLUG}}.txt`
(one URL per line)

## STEP 2: Crawl Each URL

For each URL, use crawl4ai to download as markdown:

```python
import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import re

async def crawl_and_save(urls, output_dir):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        for url in urls:
            try:
                result = await crawler.arun(url=url)
                if result.success:
                    # Build filename from URL
                    parsed = urlparse(url)
                    domain = parsed.netloc.replace('www.', '')
                    path_part = parsed.path.strip('/').replace('/', '_')
                    filename = re.sub(r'[<>:"/\\|?*]', '_', f"{domain}_{path_part}")[:200] + ".md"
                    
                    # Get title
                    title = "Untitled"
                    if hasattr(result, 'metadata') and result.metadata:
                        title = result.metadata.get('title', 'Untitled')
                    elif hasattr(result, 'title'):
                        title = result.title or 'Untitled'
                    
                    # Get content
                    content = ""
                    if hasattr(result, 'markdown'):
                        content = result.markdown
                    elif hasattr(result, 'extracted_content'):
                        content = result.extracted_content
                    
                    # Build frontmatter + content
                    md = f"---\n"
                    md += f"source_url: \"{url}\"\n"
                    md += f"title: \"{title}\"\n"
                    md += f"downloaded: \"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\"\n"
                    md += f"topic: \"{{TOPIC}}\"\n"
                    md += f"status: raw\n"
                    md += f"---\n\n"
                    md += f"# {title}\n\n"
                    md += f"**Source:** {url}\n\n---\n\n"
                    md += content
                    
                    (output_path / filename).write_text(md, encoding='utf-8')
                    print(f"✅ {filename}")
                else:
                    print(f"❌ Failed: {url}")
            except Exception as e:
                print(f"❌ Error on {url}: {e}")

# Load URLs and run
urls = Path("D:/GitHub/crawl4ai/urls_{{TOPIC_SLUG}}.txt").read_text().strip().split('\n')
urls = [u.strip() for u in urls if u.strip() and not u.startswith('#')]
asyncio.run(crawl_and_save(urls, "{{VAULT_PATH}}"))
```

Run from: `D:\GitHub\crawl4ai`
Command: `python crawl_{{TOPIC_SLUG}}.py`

## STEP 3: Create Index Note

After crawling, create an index note at `{{VAULT_PATH}}/_Index.md`:

```markdown
---
topic: "{{TOPIC}}"
created: YYYY-MM-DD
sources: X
status: raw
---

# {{TOPIC}} — Research Index

## Sources Downloaded
| # | Title | Source | Status |
|---|-------|--------|--------|
| 1 | [Title](filename.md) | domain.com | raw |
| 2 | ... | ... | raw |

## Summary
[Brief summary of what was found across all sources]

## Key Arguments FOR
- ...

## Key Arguments AGAINST
- ...

## Next Steps
- [ ] Review each source for quality
- [ ] Extract key claims
- [ ] Cross-reference with existing vault
- [ ] Write synthesis note
```

## STEP 4: Quality Pass (Optional)

For each downloaded file, add a quality assessment to the frontmatter:
- `quality: high/medium/low`
- `relevance: direct/supporting/tangential`
- `perspective: for/against/neutral`

---

## EXAMPLE USAGE

**Topic:** "Information Theory and Truth — Shannon's Theorems Applied to Philosophy"
**Vault Path:** `O:\_Theophysics_v4\David\____ THE TRUTH\RESEARCH\Information_Theory`

**Topic:** "Infinite Monkey Theorem — Mathematical Proofs and Evolution Debate"  
**Vault Path:** `O:\_ Theophysics_Case_for_Christ\06-Science-and-Faith\KEY-SOURCES`

**Topic:** "Dead Sea Scrolls Isaiah Manuscript Comparison"
**Vault Path:** `O:\_ Theophysics_Case_for_Christ\15-Textual-Criticism\KEY-SOURCES`

---

*Template by David Lowe + Claude Opus — March 2026*
*For use with Crawl4AI (D:\GitHub\crawl4ai)*
