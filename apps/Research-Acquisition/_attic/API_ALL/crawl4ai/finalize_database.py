"""
FINAL PASS: Backfill CBC Rebuttal Text + add all linking columns to the
UNIFIED_HUD_TACTICAL_DATABASE. One master file with a bow on it.

Strategy for CBC matching:
1. Parse each CBC article -> extract title, SAB URLs referenced, rebuttal text
2. Match to Excel rows via SAB URL (most reliable)
3. Fallback: match via question text overlap
"""
import os
import re
import sys
import shutil
from pathlib import Path
from collections import Counter

os.environ["PYTHONUTF8"] = "1"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

EXCEL_IN = Path("D:/GitHub/crawl4ai/UNIFIED_HUD_TACTICAL_DATABASE_1.xlsx")
EXCEL_OUT = Path("C:/Users/lowes/Downloads/UNIFIED_HUD_MASTER_FINAL.xlsx")
MD_DIR = Path("D:/GitHub/crawl4ai/downloaded_pages")
HUD_DIR = Path("D:/GitHub/crawl4ai/bible_contradictions_HUD")

BUCKET_MAP = {
    "[SCRIBE]":    "1_SCRIBAL_ERROR",
    "[ROUNDING]":  "1_SCRIBAL_ERROR",
    "[VANTAGE]":   "2_POLICE_REPORT",
    "[AUDIENCE]":  "2_POLICE_REPORT",
    "[COVENANT]":  "3_TIMELINE_SHIFT",
    "[SEMANTIC]":  "4_DEFINITION_GAME",
    "[DISTINCT]":  "4_DEFINITION_GAME",
    "[STRIPPING]": "5_REPORTER_RULE",
    "[META]":      "6_MISSING_CONTEXT",
    "[PHENOM]":    "6_MISSING_CONTEXT",
}

BUCKET_LABELS = {
    "1_SCRIBAL_ERROR":   "SCRIBAL ERROR",
    "2_POLICE_REPORT":   "POLICE REPORT",
    "3_TIMELINE_SHIFT":  "TIMELINE SHIFT",
    "4_DEFINITION_GAME": "DEFINITION GAME",
    "5_REPORTER_RULE":   "REPORTER RULE",
    "6_MISSING_CONTEXT": "MISSING CONTEXT",
}


def normalize(text):
    t = text.lower()
    t = re.sub(r"[''`]", "'", t)
    t = re.sub(r'[^a-z0-9\' ]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def word_overlap_score(a, b):
    stop = {'the','a','an','of','in','to','and','is','it','was','did','how','who',
            'what','when','where','were','are','his','her','that','this','for','by',
            'many','much','from','does','do','have','has','had','be','been','or','not',
            'why','can','will','shall','should','could','would','may','might'}
    wa = set(a.split()) - stop
    wb = set(b.split()) - stop
    if not wa or not wb:
        return 0
    shared = wa & wb
    return len(shared) / min(len(wa), len(wb))


def parse_cbc_article(filepath):
    """Parse a CBC markdown article. Returns (title, sab_urls, rebuttal_text) or None."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except:
        return None

    lines = text.splitlines()

    # Find the H1 heading (the article title) - it's the first "# " line
    title = None
    title_idx = None
    for i, line in enumerate(lines):
        if line.startswith("# ") and len(line) > 5:
            # Skip if it's clearly navigation (contains markdown links)
            if "[" not in line and "]" not in line:
                title = line[2:].strip()
                title_idx = i
                break

    if not title or not title_idx:
        return None

    # Extract SAB URLs from the article
    sab_urls = set()
    sab_pattern = re.compile(r'https?://(?:www\.)?skepticsannotatedbible\.com/[^\s\)\"]+')
    for line in lines[title_idx:]:
        for match in sab_pattern.finditer(line):
            url = match.group(0).rstrip('.')
            sab_urls.add(url)

    # Also extract SAB contradiction numbers
    sab_nums = set()
    sab_num_pattern = re.compile(r'SAB\s+Contradiction\s+(\d+)', re.IGNORECASE)
    for line in lines[title_idx:]:
        for match in sab_num_pattern.finditer(line):
            sab_nums.add(int(match.group(1)))

    # Extract rebuttal text: from after the title to "No Bible Contradiction" or footer
    content_lines = []
    in_content = False
    for line in lines[title_idx + 1:]:
        stripped = line.strip()

        # Skip publication date
        if stripped.startswith("Published ") and not in_content:
            continue

        # Stop markers
        if stripped == "**No Bible Contradiction**":
            break
        if stripped.startswith("* [1 Chronicles]") or stripped.startswith("  * [1 Chronicles]"):
            break
        if any(marker in stripped.lower() for marker in ['share this', 'leave a reply', 'posted in']):
            break

        # Skip navigation links at the start
        if not in_content:
            if stripped.startswith("[**SAB"):
                # This is the SAB reference line, skip but keep going
                continue
            if not stripped:
                continue
            if stripped.startswith("**") and not stripped.endswith("**"):
                # Bold text that's not just a label - content starting
                in_content = True
                content_lines.append(stripped)
            elif stripped.startswith("_") or len(stripped) > 40:
                in_content = True
                content_lines.append(stripped)
            elif stripped.startswith("**") and stripped.endswith("**") and len(stripped) < 100:
                # Scripture labels like "**He was 18 years old...**" - skip preamble
                continue
        else:
            content_lines.append(stripped)

    rebuttal = "\n".join(content_lines).strip()

    # Trim to reasonable length for Excel cell (max 2000 chars)
    if len(rebuttal) > 2000:
        cut = rebuttal[:2000]
        last_period = cut.rfind(". ")
        if last_period > 1000:
            rebuttal = cut[:last_period + 1]
        else:
            rebuttal = cut.rsplit(" ", 1)[0] + "..."

    if len(rebuttal) < 30:
        return None

    return title, sab_urls, sab_nums, rebuttal


def build_cbc_index():
    """Build indexes: sab_url -> rebuttal, sab_num -> rebuttal, title -> rebuttal."""
    cbc_files = sorted(MD_DIR.glob("contradictingbiblecontradictions_com_p_*.md"))
    print(f"  Found {len(cbc_files)} CBC article files")

    sab_url_index = {}   # sab_url -> (title, rebuttal)
    sab_num_index = {}   # sab_num -> (title, rebuttal)
    title_index = {}     # normalized_title -> (title, rebuttal)

    parsed = 0
    for f in cbc_files:
        result = parse_cbc_article(f)
        if not result:
            continue

        title, sab_urls, sab_nums, rebuttal = result
        parsed += 1

        for url in sab_urls:
            sab_url_index[url] = (title, rebuttal)
            # Also store normalized version (http vs https, with/without www)
            for variant in [url.replace("http://", "https://"),
                           url.replace("https://", "http://"),
                           url.replace("://www.", "://"),
                           url.replace("://skeptics", "://www.skeptics")]:
                sab_url_index[variant] = (title, rebuttal)

        for num in sab_nums:
            sab_num_index[num] = (title, rebuttal)

        ntitle = normalize(title.rstrip("?"))
        title_index[ntitle] = (title, rebuttal)

    print(f"  Parsed {parsed} articles with content")
    print(f"  SAB URL index: {len(sab_url_index)} entries")
    print(f"  SAB number index: {len(sab_num_index)} entries")
    print(f"  Title index: {len(title_index)} entries")

    return sab_url_index, sab_num_index, title_index


def find_cbc_rebuttal(question, sab_url, sab_url_index, sab_num_index, title_index):
    """Find CBC rebuttal for an Excel row. Returns (title, rebuttal) or (None, None)."""

    # Method 1: Match by SAB URL (most reliable)
    if sab_url:
        url = str(sab_url).strip()
        if url in sab_url_index:
            return sab_url_index[url]
        # Try without trailing slash or .html variants
        for variant in [url.rstrip("/"), url + "/", url.replace(".html", ""), url + ".html"]:
            if variant in sab_url_index:
                return sab_url_index[variant]

    # Method 2: Match by question text
    if question:
        nq = normalize(question.strip().rstrip("?"))

        # Exact title match
        if nq in title_index:
            return title_index[nq]

        # Substring match
        for key, val in title_index.items():
            if nq in key or key in nq:
                return val

        # Word overlap
        best_score = 0
        best_val = None
        for key, val in title_index.items():
            score = word_overlap_score(nq, key)
            if score > best_score:
                best_score = score
                best_val = val
        if best_score >= 0.6 and best_val:
            return best_val

    return None, None


def build_organized_file_index():
    """Build index of organized HUD files by row number."""
    index = {}
    for bucket_dir in sorted(HUD_DIR.iterdir()):
        if not bucket_dir.is_dir() or bucket_dir.name.startswith("7_") or bucket_dir.name.startswith("8_"):
            continue
        for f in bucket_dir.glob("*.md"):
            if f.name.startswith("_ESSAY"):
                continue
            # Parse row number from filename: "001 - ..." or "001b - ..."
            m = re.match(r'^(\d+)b?\s*-', f.name)
            if m:
                num = int(m.group(1))
                index[num] = f
    return index


def find_source_url(filepath):
    """Extract the source URL from the frontmatter of a markdown file."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines()[:5]:
            if line.startswith("url:"):
                return line[4:].strip()
    except:
        pass
    return None


def main():
    print("=" * 60)
    print("FINALIZING UNIFIED HUD TACTICAL DATABASE")
    print("The one with the bow on it.")
    print("=" * 60)

    # Step 1: Build CBC index
    print("\n[1/4] Building CBC index...")
    sab_url_index, sab_num_index, title_index = build_cbc_index()

    # Step 2: Build organized file index
    print("\n[2/4] Building organized file index...")
    file_index = build_organized_file_index()
    print(f"  Found {len(file_index)} organized files (by row number)")

    # Step 3: Process Excel
    print(f"\n[3/4] Processing Excel: {EXCEL_IN.name}")
    wb = openpyxl.load_workbook(str(EXCEL_IN))
    ws = wb["Full HUD Arsenal"]

    # Map columns
    headers = {}
    for c in range(1, ws.max_column + 1):
        val = ws.cell(1, c).value
        if val:
            headers[val] = c

    num_col = headers.get("#", 1)
    q_col = headers.get("Question", 2)
    scripture_col = headers.get("Scripture", 3)
    hud_col = headers.get("HUD Code", 5)
    cbc_text_col = headers.get("CBC Rebuttal Text", 12)
    cbc_status_col = headers.get("CBC Status", 13)
    sab_url_col = headers.get("SAB URL", 14)

    # Add new columns after existing ones
    local_col = ws.max_column + 1
    source_url_col = ws.max_column + 2
    bucket_col = ws.max_column + 3

    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, size=11, color="FFFFFF")

    for col, name in [(local_col, "Local File"), (source_url_col, "Source URL"), (bucket_col, "Bucket")]:
        ws.cell(1, col, name).font = header_font
        ws.cell(1, col).fill = header_fill

    # Also style the existing CBC header
    ws.cell(1, cbc_text_col).font = header_font
    ws.cell(1, cbc_text_col).fill = header_fill

    # Process each row
    cbc_filled = 0
    cbc_by_method = Counter()
    files_linked = 0
    urls_linked = 0
    bucket_dist = Counter()

    for r in range(2, ws.max_row + 1):
        row_num = ws.cell(r, num_col).value
        question = ws.cell(r, q_col).value
        scripture = ws.cell(r, scripture_col).value
        hud_code = ws.cell(r, hud_col).value
        existing_cbc = ws.cell(r, cbc_text_col).value
        sab_url = ws.cell(r, sab_url_col).value

        if not question:
            continue

        # --- Bucket ---
        bucket = BUCKET_MAP.get(hud_code, "6_MISSING_CONTEXT") if hud_code else "6_MISSING_CONTEXT"
        bucket_label = BUCKET_LABELS.get(bucket, "MISSING CONTEXT")
        ws.cell(r, bucket_col, bucket_label)
        bucket_dist[bucket_label] += 1

        # --- CBC Rebuttal Text backfill ---
        if not existing_cbc:
            title, rebuttal = find_cbc_rebuttal(question, sab_url,
                                                 sab_url_index, sab_num_index, title_index)
            if rebuttal:
                ws.cell(r, cbc_text_col, rebuttal)
                ws.cell(r, cbc_text_col).alignment = Alignment(wrap_text=True, vertical="top")
                cbc_filled += 1

                # Track which method matched
                if sab_url and str(sab_url).strip() in sab_url_index:
                    cbc_by_method["SAB URL"] += 1
                else:
                    cbc_by_method["Title match"] += 1

        # --- Local File link ---
        row_int = int(row_num) if row_num else None
        org_file = file_index.get(row_int) if row_int else None
        if org_file:
            cell = ws.cell(r, local_col)
            cell.value = org_file.name
            cell.hyperlink = org_file.as_uri()
            cell.font = Font(color="0563C1", underline="single")
            files_linked += 1

            # --- Source URL ---
            source_url = find_source_url(org_file)
            if not source_url and sab_url:
                source_url = str(sab_url)
            if source_url:
                ucell = ws.cell(r, source_url_col)
                ucell.value = source_url
                ucell.hyperlink = source_url
                ucell.font = Font(color="0563C1", underline="single")
                urls_linked += 1

    # Column widths
    ws.column_dimensions[get_column_letter(cbc_text_col)].width = 65
    ws.column_dimensions[get_column_letter(local_col)].width = 50
    ws.column_dimensions[get_column_letter(source_url_col)].width = 55
    ws.column_dimensions[get_column_letter(bucket_col)].width = 18
    ws.column_dimensions[get_column_letter(q_col)].width = 50

    # Step 4: Save
    print(f"\n[4/4] Saving: {EXCEL_OUT}")
    wb.save(str(EXCEL_OUT))

    # Summary
    print(f"\n{'='*60}")
    print("DONE. HERE'S YOUR BOW:")
    print(f"{'='*60}")
    print(f"  CBC Rebuttal Text backfilled: {cbc_filled} / 642 rows")
    if cbc_by_method:
        for method, count in cbc_by_method.items():
            print(f"    via {method}: {count}")
    print(f"  Local files linked:           {files_linked} / 642 rows")
    print(f"  Source URLs linked:            {urls_linked} / 642 rows")
    print(f"\n  Bucket distribution:")
    for bucket, count in sorted(bucket_dist.items()):
        print(f"    {bucket}: {count}")
    print(f"\n  Output: {EXCEL_OUT}")
    print(f"\n  The master file now has {ws.max_column} columns:")
    for c in range(1, ws.max_column + 1):
        v = ws.cell(1, c).value
        print(f"    Col {c}: {v}")


if __name__ == "__main__":
    main()
