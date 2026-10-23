#!/usr/bin/env python3
"""
batch_analyze_folder.py — Point at a folder of transcripts, get analyzed markdown.

Usage:
    python batch_analyze_folder.py "subtitles/Gary Habermas" --out analyzed
    python batch_analyze_folder.py subtitles --out analyzed
    python batch_analyze_folder.py transcripts_inbox --out analyzed_transcripts
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ANALYZER = SCRIPT_DIR / "yt_deep_analyze.py"


def main():
    p = argparse.ArgumentParser(description="Batch deep-analyze a folder of transcripts.")
    p.add_argument("folder", help="folder containing .md transcript files")
    p.add_argument("--out", dest="out_dir", default="analyzed_transcripts", help="output folder")
    args = p.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        print(f"Folder not found: {folder}")
        sys.exit(1)

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = SCRIPT_DIR / out_dir

    print(f"Batch analyzing: {folder}")
    print(f"Output folder:   {out_dir}\n")

    subprocess.run([
        sys.executable, str(ANALYZER),
        "--in", str(folder),
        "--out", str(out_dir),
    ], check=True)


if __name__ == "__main__":
    main()
