"""
Organize downloaded markdown files into categorized folders based on the Excel HUD codes.
Files are copied (not moved) into:
  bible_contradictions_organized/
    META/
    SCRIBE/
    STRIPPING/
    VANTAGE/
    COVENANT/
    SEMANTIC/
    DISTINCT/
    ROUNDING/
    AUDIENCE/
    PHENOM/
    _UNMATCHED/

Files are renamed: {ScriptureRef} - {Question}.md
Then the Excel is updated with hyperlinks to the organized files.
"""
import os
import re
import shutil
from pathlib import Path
from copy import copy
import openpyxl
from openpyxl.styles import Font

EXCEL_IN = r"C:\Users\lowes\Downloads\bible_contradictions_HUD_tagged.xlsx"
EXCEL_OUT = r"C:\Users\lowes\Downloads\bible_contradictions_HUD_tagged_linked.xlsx"
MD_DIR = Path("D:/GitHub/crawl4ai/downloaded_pages")
ORG_DIR = Path("D:/GitHub/crawl4ai/bible_contradictions_organized")


def sanitize(text, max_len=80):
    """Clean text for use as filename."""
    if not text or text == "None":
        return ""
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_len:
        text = text[:max_len].rsplit(' ', 1)[0]
    return text


def build_file_index():
    """Build maps from question text and URL to file paths."""
    question_map = {}
    url_map = {}
    all_files = {}

    for f in MD_DIR.glob("*.md"):
        all_files[f.stem.lower()] = f
        text = f.read_text(encoding="utf-8", errors="replace")

        for line in text.splitlines()[:5]:
            if line.startswith("url:"):
                url = line[4:].strip()
                url_map[url] = f
                break

        for line in text.splitlines():
            cleaned = line.lstrip("#").strip()
            if cleaned and "?" in cleaned and len(cleaned) > 10:
                if not cleaned.startswith("SAB") and not cleaned.startswith("http"):
                    key = cleaned.lower().rstrip("?").strip()
                    question_map[key] = f
                    break

    return question_map, url_map, all_files


def normalize(text):
    """Normalize text for comparison: lowercase, strip punctuation, collapse spaces."""
    t = text.lower()
    t = re.sub(r"[''`]", "'", t)
    t = re.sub(r'[^a-z0-9\' ]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def word_overlap_score(a, b):
    """Score based on shared significant words."""
    stop = {'the','a','an','of','in','to','and','is','it','was','did','how','who',
            'what','when','where','were','are','his','her','that','this','for','by',
            'many','much','from','does','do','have','has','had','be','been','or','not'}
    wa = set(a.split()) - stop
    wb = set(b.split()) - stop
    if not wa or not wb:
        return 0
    shared = wa & wb
    return len(shared) / min(len(wa), len(wb))


def find_file_for_row(question, question_map, all_files):
    if not question:
        return None

    q = question.strip().lower().rstrip("?").strip()

    # Exact match
    if q in question_map:
        return question_map[q]

    # Substring match
    for key, fpath in question_map.items():
        if q in key or key in q:
            return fpath

    # Normalized word overlap match
    nq = normalize(question)
    best_score = 0
    best_file = None
    for key, fpath in question_map.items():
        score = word_overlap_score(nq, normalize(key))
        if score > best_score:
            best_score = score
            best_file = fpath
    if best_score >= 0.5 and best_file:
        return best_file

    # Keyword match on filename
    words = re.findall(r'[a-z]{4,}', q)
    if words:
        best_score = 0
        best_file = None
        for stem, fpath in all_files.items():
            if "contra" not in stem:
                continue
            score = sum(1 for w in words if w in stem)
            if score > best_score and score >= 2:
                best_score = score
                best_file = fpath
        if best_file:
            return best_file

    return None


def find_url_for_file(filepath, url_map):
    for url, fpath in url_map.items():
        if fpath == filepath:
            return url
    return None


def main():
    print("Building file index...")
    question_map, url_map, all_files = build_file_index()
    print(f"  {len(question_map)} questions, {len(url_map)} URLs, {len(all_files)} files")

    # Clean and recreate organized directory
    if ORG_DIR.exists():
        shutil.rmtree(ORG_DIR)
    ORG_DIR.mkdir(parents=True)

    print(f"\nLoading Excel: {EXCEL_IN}")
    wb = openpyxl.load_workbook(EXCEL_IN)
    ws = wb["Master Tagged Database"]

    # Find columns
    headers = {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1)}
    q_col = headers.get("Question", 3)
    book_col = headers.get("Bible Book", 4)
    ref_col = headers.get("Scripture Ref", 5)
    hud_col = headers.get("HUD Code", 7)
    num_col = headers.get("#", 1)

    # Add/replace link columns
    link_col = ws.max_column + 1
    url_col = ws.max_column + 2
    ws.cell(1, link_col, "Local File")
    ws.cell(1, link_col).font = Font(bold=True)
    ws.cell(1, url_col, "Source URL")
    ws.cell(1, url_col).font = Font(bold=True)

    # Track what gets organized
    used_names = {}  # track duplicate filenames
    matched = 0
    unmatched_rows = []

    print("\nOrganizing files...")
    for r in range(2, ws.max_row + 1):
        question = ws.cell(r, q_col).value
        scripture = ws.cell(r, ref_col).value
        hud = ws.cell(r, hud_col).value
        row_num = ws.cell(r, num_col).value

        if not question:
            continue

        # Find matching file
        source_file = find_file_for_row(question, question_map, all_files)

        if not source_file:
            unmatched_rows.append((r, question[:60], hud))
            continue

        matched += 1

        # Determine category folder
        category = sanitize(hud) if hud and hud != "None" else "_UNCATEGORIZED"
        cat_dir = ORG_DIR / category
        cat_dir.mkdir(exist_ok=True)

        # Build nice filename: "001 - Genesis 16_15 - How many sons did Abraham have.md"
        num_str = f"{int(row_num):03d}" if row_num else f"r{r:03d}"
        ref_str = sanitize(scripture, 40).replace(":", "_") if scripture and scripture != "None" else "No_Ref"
        q_str = sanitize(question, 60)
        new_name = f"{num_str} - {ref_str} - {q_str}.md"

        # Handle duplicates
        if new_name in used_names:
            new_name = f"{num_str}b - {ref_str} - {q_str}.md"
        used_names[new_name] = True

        dest = cat_dir / new_name

        # Copy file
        shutil.copy2(source_file, dest)

        # Add hyperlink to organized file
        file_url = dest.as_uri()
        cell = ws.cell(r, link_col)
        cell.value = new_name
        cell.hyperlink = file_url
        cell.font = Font(color="0000FF", underline="single")

        # Add source URL
        source_url = find_url_for_file(source_file, url_map)
        if source_url:
            ucell = ws.cell(r, url_col)
            ucell.value = source_url
            ucell.hyperlink = source_url
            ucell.font = Font(color="0000FF", underline="single")

    # Now do the same for category sheets
    for sheet_name in wb.sheetnames:
        if sheet_name == "Master Tagged Database" or sheet_name == "Category Summary":
            continue

        sws = wb[sheet_name]
        if sws.max_row < 2:
            continue

        s_q_col = None
        for c in range(1, sws.max_column + 1):
            val = sws.cell(1, c).value
            if val and "question" in str(val).lower():
                s_q_col = c
                break
        if not s_q_col:
            continue

        s_link_col = sws.max_column + 1
        s_url_col = sws.max_column + 2
        sws.cell(1, s_link_col, "Local File")
        sws.cell(1, s_link_col).font = Font(bold=True)
        sws.cell(1, s_url_col, "Source URL")
        sws.cell(1, s_url_col).font = Font(bold=True)

        for r in range(2, sws.max_row + 1):
            question = sws.cell(r, s_q_col).value
            if not question:
                continue

            source_file = find_file_for_row(question, question_map, all_files)
            if not source_file:
                continue

            # Find the organized file that matches
            for cat_dir in ORG_DIR.iterdir():
                if not cat_dir.is_dir():
                    continue
                for org_file in cat_dir.glob("*.md"):
                    # Check if this org file was copied from our source
                    if org_file.stat().st_size == source_file.stat().st_size:
                        cell = sws.cell(r, s_link_col)
                        cell.value = org_file.name
                        cell.hyperlink = org_file.as_uri()
                        cell.font = Font(color="0000FF", underline="single")

                        source_url = find_url_for_file(source_file, url_map)
                        if source_url:
                            ucell = sws.cell(r, s_url_col)
                            ucell.value = source_url
                            ucell.hyperlink = source_url
                            ucell.font = Font(color="0000FF", underline="single")
                        break

    # Summary
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Master sheet: {matched}/{ws.max_row - 1} rows linked")
    print(f"Unmatched: {len(unmatched_rows)}")

    # Show folder structure
    print(f"\nOrganized folder: {ORG_DIR}")
    for cat_dir in sorted(ORG_DIR.iterdir()):
        if cat_dir.is_dir():
            count = len(list(cat_dir.glob("*.md")))
            print(f"  {cat_dir.name}/  ({count} files)")

    if unmatched_rows:
        print(f"\nUnmatched rows (no downloaded file found):")
        for r, q, hud in unmatched_rows[:20]:
            print(f"  Row {r} [{hud}]: {q}")
        if len(unmatched_rows) > 20:
            print(f"  ... and {len(unmatched_rows)-20} more")

    print(f"\nSaving Excel: {EXCEL_OUT}")
    wb.save(EXCEL_OUT)
    print("Done!")


if __name__ == "__main__":
    main()
