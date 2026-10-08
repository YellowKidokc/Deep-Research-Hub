"""Write one job file per DEBATE MAP question.

    python make_jobs.py DEBATE_MAP.md --jobs ../../../../data/jobs --subjects S-CHURCH S-PERSONAL
    python make_jobs.py DEBATE_MAP.md --jobs ... --ids Q-EVIL-REAL-GOOD Q-ORIGIN-FEAR
    python make_jobs.py DEBATE_MAP.md --jobs ... --subjects S-BIBLE --list     # show, write nothing
    python make_jobs.py DEBATE_MAP.md --jobs ... --subjects S-EVIL --job-type fork_map

Reads "## S-XXX · Title" headings and "- `Q-ID` question" lines. Each job is
<Q-ID>.yaml with the question as its query and {question_id, subject} in meta;
everything else comes from _defaults.yaml. Existing job files are not overwritten.
"""
import argparse
import re
import sys
from pathlib import Path

SUBJECT = re.compile(r"^##\s+(S-[A-Z0-9-]+)\s*·\s*(.+)$")
QUESTION = re.compile(r"^-\s+`(Q-[A-Z0-9-]+)`(?:\s*\([^)]*\))?\s+(.+)$")


def parse(text):
    subject, title, out = None, None, []
    for line in text.splitlines():
        line = line.strip()
        m = SUBJECT.match(line)
        if m:
            subject, title = m.group(1), m.group(2).strip()
            continue
        if line.startswith("## ") or line.startswith("# "):
            subject = None
        q = QUESTION.match(line)
        if q and subject:
            out.append({"id": q.group(1), "question": q.group(2).strip(), "subject": subject, "title": title})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("debate_map")
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--subjects", nargs="*", default=[])
    ap.add_argument("--ids", nargs="*", default=[])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--job-type", help="written into each job (e.g. fork_map); default: from _defaults.yaml")
    args = ap.parse_args()

    qs = parse(Path(args.debate_map).read_text(encoding="utf-8"))
    if args.subjects or args.ids:
        qs = [q for q in qs if q["subject"] in args.subjects or q["id"] in args.ids]
    if not qs:
        sys.exit("no questions matched")
    jobs = Path(args.jobs)
    jobs.mkdir(parents=True, exist_ok=True)
    written = skipped = 0
    for q in qs:
        path = jobs / f"{q['id']}.yaml"
        if args.list:
            print(f"{q['id']:<32} {q['question']}")
            continue
        if path.exists():
            skipped += 1
            continue
        query = q["question"].replace('"', '\\"')
        path.write_text(
            f'query: "{query}"\n'
            + (f"job_type: {args.job_type}\n" if args.job_type else "")
            + f"meta:\n  question_id: {q['id']}\n  subject: {q['subject']}\n  subject_title: \"{q['title']}\"\n",
            encoding="utf-8")
        written += 1
    if not args.list:
        print(f"{written} job file(s) written to {jobs}, {skipped} already there")


if __name__ == "__main__":
    main()
