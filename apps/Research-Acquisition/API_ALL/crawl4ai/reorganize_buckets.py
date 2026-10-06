"""
Reorganize into the 6 Operational Buckets + Essays folder + Needs_Work folder.

Structure:
  bible_contradictions_HUD/
    1_SCRIBAL_ERROR/          (SCRIBE + ROUNDING = ~125 files)
    2_POLICE_REPORT/          (VANTAGE + AUDIENCE = ~62 files)
    3_TIMELINE_SHIFT/         (COVENANT = ~42 files)
    4_DEFINITION_GAME/        (SEMANTIC + DISTINCT = ~55 files)
    5_REPORTER_RULE/          (STRIPPING = ~100 files)
    6_MISSING_CONTEXT/        (META + PHENOM = ~231 files)
    7_ESSAYS/                 (empty - placeholder for bucket-level essays)
    8_NEEDS_INDIVIDUAL_WORK/  (unmatched rows that need manual research)
"""
import os
import re
import shutil
from pathlib import Path
import openpyxl
from openpyxl.styles import Font

EXCEL_IN = r"C:\Users\lowes\Downloads\bible_contradictions_HUD_tagged.xlsx"
EXCEL_OUT = r"C:\Users\lowes\Downloads\bible_contradictions_HUD_tagged_linked.xlsx"
MD_DIR = Path("D:/GitHub/crawl4ai/downloaded_pages")
HUD_DIR = Path("D:/GitHub/crawl4ai/bible_contradictions_HUD")

# The 6-bucket mapping
BUCKET_MAP = {
    "SCRIBE":    "1_SCRIBAL_ERROR",
    "ROUNDING":  "1_SCRIBAL_ERROR",
    "VANTAGE":   "2_POLICE_REPORT",
    "AUDIENCE":  "2_POLICE_REPORT",
    "COVENANT":  "3_TIMELINE_SHIFT",
    "SEMANTIC":  "4_DEFINITION_GAME",
    "DISTINCT":  "4_DEFINITION_GAME",
    "STRIPPING": "5_REPORTER_RULE",
    "META":      "6_MISSING_CONTEXT",
    "PHENOM":    "6_MISSING_CONTEXT",
}

BUCKET_LABELS = {
    "1_SCRIBAL_ERROR":   "It's a typo in a digit or a name, not a lie.",
    "2_POLICE_REPORT":   "Different witnesses see different angles. Variation validates authenticity.",
    "3_TIMELINE_SHIFT":  "That was Old Management (Theocracy). We are under New Management (Grace).",
    "4_DEFINITION_GAME": "You are forcing a modern English definition on an ancient Hebrew word.",
    "5_REPORTER_RULE":   "The Bible recorded that sin (Descriptive), it didn't vote for it (Prescriptive).",
    "6_MISSING_CONTEXT": "You took a soundbite out of a paragraph and made it say the opposite.",
}


def sanitize(text, max_len=80):
    if not text or text == "None":
        return ""
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_len:
        text = text[:max_len].rsplit(' ', 1)[0]
    return text


def normalize(text):
    t = text.lower()
    t = re.sub(r"[''`]", "'", t)
    t = re.sub(r'[^a-z0-9\' ]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def word_overlap_score(a, b):
    stop = {'the','a','an','of','in','to','and','is','it','was','did','how','who',
            'what','when','where','were','are','his','her','that','this','for','by',
            'many','much','from','does','do','have','has','had','be','been','or','not'}
    wa = set(a.split()) - stop
    wb = set(b.split()) - stop
    if not wa or not wb:
        return 0
    shared = wa & wb
    return len(shared) / min(len(wa), len(wb))


def build_file_index():
    question_map = {}
    url_map = {}
    all_files = {}

    for f in MD_DIR.glob("*.md"):
        all_files[f.stem.lower()] = f
        text = f.read_text(encoding="utf-8", errors="replace")

        for line in text.splitlines()[:5]:
            if line.startswith("url:"):
                url_map[line[4:].strip()] = f
                break

        for line in text.splitlines():
            cleaned = line.lstrip("#").strip()
            if cleaned and "?" in cleaned and len(cleaned) > 10:
                if not cleaned.startswith("SAB") and not cleaned.startswith("http"):
                    question_map[cleaned.lower().rstrip("?").strip()] = f
                    break

    return question_map, url_map, all_files


def find_file_for_row(question, question_map, all_files):
    if not question:
        return None
    q = question.strip().lower().rstrip("?").strip()

    if q in question_map:
        return question_map[q]

    for key, fpath in question_map.items():
        if q in key or key in q:
            return fpath

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

    # Clean and recreate
    if HUD_DIR.exists():
        shutil.rmtree(HUD_DIR)
    HUD_DIR.mkdir(parents=True)

    # Create bucket folders
    for bucket in BUCKET_MAP.values():
        (HUD_DIR / bucket).mkdir(exist_ok=True)
    (HUD_DIR / "7_ESSAYS").mkdir()
    (HUD_DIR / "8_NEEDS_INDIVIDUAL_WORK").mkdir()

    # Create README in essays folder
    essay_readme = "# Essay Topics\n\nOne essay per bucket defeats the entire category.\n\n"
    for bucket, label in BUCKET_LABELS.items():
        essay_readme += f"## {bucket.split('_', 1)[1].replace('_', ' ')}\n{label}\n\n"
    (HUD_DIR / "7_ESSAYS" / "README.md").write_text(essay_readme, encoding="utf-8")

    print(f"\nLoading Excel: {EXCEL_IN}")
    wb = openpyxl.load_workbook(EXCEL_IN)
    ws = wb["Master Tagged Database"]

    headers = {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1)}
    q_col = headers.get("Question", 3)
    ref_col = headers.get("Scripture Ref", 5)
    hud_col = headers.get("HUD Code", 7)
    num_col = headers.get("#", 1)

    # Add columns
    link_col = ws.max_column + 1
    url_col = ws.max_column + 2
    bucket_col = ws.max_column + 3
    ws.cell(1, link_col, "Local File")
    ws.cell(1, link_col).font = Font(bold=True)
    ws.cell(1, url_col, "Source URL")
    ws.cell(1, url_col).font = Font(bold=True)
    ws.cell(1, bucket_col, "Bucket")
    ws.cell(1, bucket_col).font = Font(bold=True)

    used_names = {}
    matched = 0
    unmatched_rows = []

    print("\nOrganizing into 6 buckets...")
    for r in range(2, ws.max_row + 1):
        question = ws.cell(r, q_col).value
        scripture = ws.cell(r, ref_col).value
        hud = ws.cell(r, hud_col).value
        row_num = ws.cell(r, num_col).value

        if not question:
            continue

        # Determine bucket
        bucket = BUCKET_MAP.get(hud, "6_MISSING_CONTEXT") if hud else "6_MISSING_CONTEXT"
        ws.cell(r, bucket_col, bucket.split("_", 1)[1].replace("_", " "))

        # Find matching file
        source_file = find_file_for_row(question, question_map, all_files)

        # Build filename
        num_str = f"{int(row_num):03d}" if row_num else f"r{r:03d}"
        ref_str = sanitize(scripture, 40).replace(":", "_") if scripture and scripture != "None" else "No_Ref"
        q_str = sanitize(question, 60)
        new_name = f"{num_str} - {ref_str} - {q_str}.md"

        if new_name in used_names:
            new_name = f"{num_str}b - {ref_str} - {q_str}.md"
        used_names[new_name] = True

        if source_file:
            matched += 1
            dest = HUD_DIR / bucket / new_name
            shutil.copy2(source_file, dest)

            file_url = dest.as_uri()
            cell = ws.cell(r, link_col)
            cell.value = new_name
            cell.hyperlink = file_url
            cell.font = Font(color="0000FF", underline="single")

            source_url = find_url_for_file(source_file, url_map)
            if source_url:
                ucell = ws.cell(r, url_col)
                ucell.value = source_url
                ucell.hyperlink = source_url
                ucell.font = Font(color="0000FF", underline="single")
        else:
            unmatched_rows.append((r, question, hud, row_num))
            # Create placeholder in NEEDS_INDIVIDUAL_WORK
            placeholder = f"---\nquestion: {question}\nscripture: {scripture}\nhud: {hud}\nstatus: NEEDS RESEARCH\n---\n\n# {question}\n\nThis contradiction needs individual research and a custom defense.\n\n**Scripture:** {scripture}\n**HUD Code:** {hud} -> {bucket}\n"
            dest = HUD_DIR / "8_NEEDS_INDIVIDUAL_WORK" / new_name
            dest.write_text(placeholder, encoding="utf-8")

            file_url = dest.as_uri()
            cell = ws.cell(r, link_col)
            cell.value = f"[TODO] {new_name}"
            cell.hyperlink = file_url
            cell.font = Font(color="FF0000", underline="single")

    # Process category sheets too
    for sheet_name in wb.sheetnames:
        if sheet_name in ("Master Tagged Database", "Category Summary"):
            continue
        sws = wb[sheet_name]
        if sws.max_row < 2:
            continue

        s_q_col = None
        for c in range(1, sws.max_column + 1):
            if sws.cell(1, c).value and "question" in str(sws.cell(1, c).value).lower():
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

            # Find organized file by matching size
            for bucket_dir in HUD_DIR.iterdir():
                if not bucket_dir.is_dir() or bucket_dir.name.startswith("7_") or bucket_dir.name.startswith("8_"):
                    continue
                for org_file in bucket_dir.glob("*.md"):
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
    print("FINAL STRUCTURE")
    print(f"{'='*60}")
    print(f"Master sheet: {matched} linked, {len(unmatched_rows)} need work")
    print(f"\nFolder: {HUD_DIR}")
    for d in sorted(HUD_DIR.iterdir()):
        if d.is_dir():
            count = len(list(d.glob("*.md")))
            label = BUCKET_LABELS.get(d.name, "")
            print(f"  {d.name}/  ({count} files)")
            if label:
                print(f"    -> {label}")

    print(f"\nSaving: {EXCEL_OUT}")
    wb.save(EXCEL_OUT)
    print("Done!")


if __name__ == "__main__":
    main()
