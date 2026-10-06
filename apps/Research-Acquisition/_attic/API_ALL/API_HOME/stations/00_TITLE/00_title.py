"""00_TITLE: standard title + keywords + move for each item, before any CKG (tools/standard_title.py --apply).

With no items (as in routine D) it titles the notes waiting in the inboxes the next stations read, so the
standard name is in place before any run folder is named after the source."""
from pathlib import Path
import subprocess, sys
API_HOME = Path(__file__).resolve().parents[2]
TOOL = API_HOME / "tools" / "standard_title.py"
INBOXES = ["00_TITLE", "48_API_DEEP", "49_ARGUMENT_GRADE"]
if __name__ == "__main__":
    items = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not items:
        items = [str(d) for d in (API_HOME / "INBOX" / n for n in INBOXES) if d.is_dir() and any(d.glob("*.md"))]
        print(f"00_TITLE: {'titling ' + ', '.join(items) if items else 'no .md notes waiting in the inboxes; nothing to title'}")
    raise SystemExit(subprocess.run([sys.executable, str(TOOL), *items, "--apply"]).returncode if items else 0)
