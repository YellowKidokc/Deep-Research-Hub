"""
Extract people from Catherine Austin Fitts' Dillon Read book and write
Obsidian-ready markdown files into the Individual vault folder.

Sources:
  - "Reference: People In This Story" section (canonical bios)
  - Full-text scan for every mention of each name + surrounding context

Output: O:/Valts/epstein_email_obsidian_vault-main/Individual/<Name>.md
        If the file already exists (Epstein email person) it appends a
        ## Dillon Read Book section rather than overwriting.

Frontmatter tag added: dillon_read_book  (for graph filtering in Obsidian)
"""

import re
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BOOK_PATH = Path("O:/Valts/epstein_email_obsidian_vault-main/Dillion Book/AustinFitts_DillonRead.md")
OUTPUT_DIR = Path("O:/Valts/epstein_email_obsidian_vault-main/Individual")
DR_TAG = "dillon_read_book"
BOOK_LABEL = "Dillon Read Book"
EM_DASH = '\u2014'  # —


# ─── helpers ──────────────────────────────────────────────────────────────────

def clean(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def sentences_around(text: str, name: str, window: int = 2) -> list[str]:
    """Return up to 8 context snippets mentioning the person's name."""
    # Use first + last name for matching
    parts = name.split()
    first = parts[0] if parts else name
    last = parts[-1] if len(parts) > 1 else ''

    # Split text into sentences
    sents = re.split(r'(?<=[.!?])\s+', text)
    hits = []
    for i, s in enumerate(sents):
        # Match first name or last name (skip very short last names to avoid noise)
        match_first = len(first) > 3 and re.search(r'\b' + re.escape(first) + r'\b', s, re.I)
        match_last  = len(last) > 4  and re.search(r'\b' + re.escape(last)  + r'\b', s, re.I)
        if match_first or match_last:
            start = max(0, i - window)
            end   = min(len(sents), i + window + 1)
            snippet = ' '.join(sents[start:end]).strip()
            if snippet and snippet not in hits:
                hits.append(snippet)
    return hits[:8]


# ─── parse Reference section ──────────────────────────────────────────────────

PAGE_HEADER_RE = re.compile(r'^Reference:\s*People In This Story\s*[\|\\t]*\d*\s*$')

def parse_reference_section(text: str) -> list[dict]:
    """
    Parse the 'Reference: People In This Story' block.

    Each entry in the book occupies one or more lines:
      Name — Then: ... Now: ...
    The em-dash (U+2014) separates name from bio.
    Page headers ('Reference: People In This Story |213') appear between entries.
    """
    # Find the REAL reference section (not the TOC mention)
    marker = 'As of April 2006'
    idx = text.find(marker)
    if idx == -1:
        print("WARNING: Could not find 'As of April 2006' marker.")
        return []

    ref_text = text[idx:]
    lines = ref_text.split('\n')

    people = []
    current_name = ''
    current_bio_parts = []

    def flush():
        if current_name:
            bio = clean(' '.join(current_bio_parts))
            then_role, now_role = extract_then_now(bio)
            people.append({
                'name': current_name,
                'then_role': then_role,
                'now_role': now_role,
                'bio': bio,
            })

    for line in lines:
        line = line.strip()

        # Skip page headers and empty lines
        if not line or PAGE_HEADER_RE.match(line):
            continue
        if line == marker:
            continue

        if EM_DASH in line:
            # New person entry
            flush()
            name_raw, _, bio_start = line.partition(EM_DASH)
            current_name = clean(name_raw)
            # Clean up name: strip titles like "Senator", "Congressman"
            current_name = re.sub(r'^(Senator|Congressman|Rep\.|Dr\.)\s+', '', current_name)
            # Strip trailing qualifiers like ", R-Missouri"
            current_name = re.sub(r',\s+[A-Z]-\w+$', '', current_name)
            current_name = current_name.strip()
            current_bio_parts = [bio_start.strip()] if bio_start.strip() else []
        else:
            # Continuation line for current person
            if current_name:
                current_bio_parts.append(line)

    flush()  # last person
    return people


def extract_then_now(bio: str) -> tuple[str, str]:
    then_m = re.search(r'\bThen\s*(?:&\s*Now)?\s*:\s*(.*?)(?=\bNow\s*:|Of Interest:|$)', bio, re.DOTALL | re.I)
    now_m  = re.search(r'\bNow\s*:\s*(.*?)(?=Of Interest:|$)', bio, re.DOTALL | re.I)
    then_role = clean(then_m.group(1)) if then_m else ''
    now_role  = clean(now_m.group(1))  if now_m  else ''
    return then_role, now_role


# ─── markdown writer ──────────────────────────────────────────────────────────

def build_frontmatter(person: dict, mention_count: int) -> str:
    name = person['name']
    tags = ['person', DR_TAG]
    if person.get('then_role'):
        tags.append('has_role')

    lines = [
        '---',
        f'name: "{name}"',
        f'mention_count_dr: {mention_count}',
        f'sources: [{DR_TAG}]',
        f'tags: [{", ".join(tags)}]',
        '---',
        '',
    ]
    return '\n'.join(lines)


def build_body(person: dict, mentions: list[str]) -> str:
    name     = person['name']
    then     = person.get('then_role', '')
    now      = person.get('now_role', '')
    bio      = person.get('bio', '')

    lines = [f'# {name}', '']
    lines += [f'> **Source:** *{BOOK_LABEL}* — Catherine Austin Fitts', '']

    if then or now:
        lines += ['## Roles', '']
        if then:
            lines += [f'**Then:** {then}', '']
        if now:
            lines += [f'**Now (as of 2006):** {now}', '']

    if bio:
        lines += ['## Bio (from book)', '', bio, '']

    if mentions:
        lines += [f'## Mentions in Text ({len(mentions)})', '']
        for i, snippet in enumerate(mentions, 1):
            if len(snippet) > 700:
                snippet = snippet[:697] + '...'
            lines += [f'**{i}.** _{snippet}_', '']

    return '\n'.join(lines)


def append_dr_section(existing: str, person: dict, mentions: list[str]) -> str:
    """Append Dillon Read info to an existing Epstein email file."""
    if 'Dillon Read Book' in existing:
        return existing  # already done

    then = person.get('then_role', '')
    now  = person.get('now_role', '')
    bio  = person.get('bio', '')

    extra = [
        '',
        '---',
        '',
        '## Dillon Read Book',
        '',
        f'> **Also appears in:** *{BOOK_LABEL}* — Catherine Austin Fitts',
        '',
    ]
    if then:
        extra += [f'**Role (Then):** {then}', '']
    if now:
        extra += [f'**Role (Now, 2006):** {now}', '']
    if bio:
        bio_trimmed = bio[:800] + ('...' if len(bio) > 800 else '')
        extra += ['**Bio:**', '', bio_trimmed, '']
    if mentions:
        extra += [f'### Book Mentions ({len(mentions)})', '']
        for i, s in enumerate(mentions[:5], 1):
            if len(s) > 400:
                s = s[:397] + '...'
            extra += [f'**{i}.** _{s}_', '']

    # Add dillon_read_book tag to frontmatter if missing
    if DR_TAG not in existing:
        existing = re.sub(
            r'(tags:\s*\[)([^\]]*)\]',
            lambda m: m.group(1) + m.group(2).rstrip(', ') + f', {DR_TAG}]',
            existing, count=1
        )

    return existing + '\n'.join(extra)


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    print('=' * 70)
    print('FITTS PEOPLE EXTRACTOR — Dillon Read Book')
    print(f'Book:   {BOOK_PATH}')
    print(f'Output: {OUTPUT_DIR}')
    print('=' * 70)

    if not BOOK_PATH.exists():
        print(f'ERROR: Book not found at {BOOK_PATH}')
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    text = BOOK_PATH.read_text(encoding='utf-8')
    text = text.replace('\r\n', '\n')

    # ── Step 1: parse reference section ───────────────────────────────────────
    print('\n[1/4] Parsing Reference: People In This Story...')
    ref_people = parse_reference_section(text)
    print(f'      Found {len(ref_people)} people in reference section.')
    for p in ref_people:
        print(f'        • {p["name"]}')

    # ── Step 2: find mentions for each person ─────────────────────────────────
    print('\n[2/4] Extracting text mentions...')
    for p in ref_people:
        p['mentions'] = sentences_around(text, p['name'])
        print(f'        {p["name"]}: {len(p["mentions"])} mention(s)')

    # ── Step 3: clean up any bad files from previous run ─────────────────────
    # (delete obvious non-person files we may have created before)
    junk_patterns = [
        'Dillon Read.md', 'Stock Profits.md', 'Urban Development.md',
        'Austin Fitts.md', 'Bush Administration.md', 'Hamilton Securities.md',
        'Catherine Austin.md', 'Wrote This.md', 'Rothschild Man.md',
    ]
    cleaned = 0
    for junk in OUTPUT_DIR.iterdir():
        # Only delete files created without a proper frontmatter name that matches
        if junk.name in junk_patterns:
            content = junk.read_text(encoding='utf-8')
            if DR_TAG in content and 'email_count' not in content:
                junk.unlink()
                cleaned += 1
    if cleaned:
        print(f'\n[3/4] Cleaned {cleaned} junk files from previous run.')
    else:
        print('\n[3/4] No junk files to clean.')

    # ── Step 4: write files ───────────────────────────────────────────────────
    print('\n[4/4] Writing Obsidian markdown files...')
    created = 0
    updated = 0
    skipped = 0

    for person in ref_people:
        name     = person['name']
        mentions = person.get('mentions', [])

        if not name:
            skipped += 1
            continue

        safe_name = re.sub(r'[<>:"/\\|?*]', '', name)
        out_file  = OUTPUT_DIR / f'{safe_name}.md'

        if out_file.exists():
            existing     = out_file.read_text(encoding='utf-8')
            updated_text = append_dr_section(existing, person, mentions)
            out_file.write_text(updated_text, encoding='utf-8')
            print(f'  UPDATED : {out_file.name}')
            updated += 1
        else:
            fm   = build_frontmatter(person, len(mentions))
            body = build_body(person, mentions)
            out_file.write_text(fm + '\n' + body, encoding='utf-8')
            print(f'  CREATED : {out_file.name}')
            created += 1

    print('\n' + '=' * 70)
    print(f'DONE  |  Created: {created}  Updated: {updated}  Skipped: {skipped}')
    print('=' * 70)


if __name__ == '__main__':
    main()
