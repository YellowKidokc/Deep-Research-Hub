import os
from pathlib import Path

base = Path("D:/GitHub/crawl4ai/bible_contradictions_HUD")
print("=== HUD Bucket Folders ===")
grand = 0
for d in sorted(base.iterdir()):
    if d.is_dir():
        primary = len([f for f in d.glob("*.md") if f.name != "README.md"])
        sources_dir = d / "sources"
        sources = len(list(sources_dir.glob("*.md"))) if sources_dir.exists() else 0
        grand += primary + sources
        if sources > 0:
            print(f"  {d.name}: {primary} primary + {sources} source refs")
        else:
            print(f"  {d.name}: {primary} files")
print(f"  --- Grand total: {grand} files ---")

downloads = Path("D:/GitHub/crawl4ai/downloaded_pages")
print(f"\n=== Raw Downloads ===")
total = len(list(downloads.glob("*.md")))
print(f"  Total: {total} files")
sab = len([f for f in downloads.glob("*.md") if f.name.startswith("skepticsannotatedbible")])
cbc = len([f for f in downloads.glob("*.md") if f.name.startswith("contradictingbiblecontradictions")])
di = len([f for f in downloads.glob("*.md") if f.name.startswith("defendinginerrancy")])
carm = len([f for f in downloads.glob("*.md") if f.name.startswith("carm_org")])
other = total - sab - cbc - di - carm
print(f"  SAB: {sab}")
print(f"  CBC: {cbc}")
print(f"  Defending Inerrancy: {di}")
print(f"  CARM: {carm}")
if other > 0:
    print(f"  Other: {other}")
