from pathlib import Path
import json, subprocess, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from engine.paths import external
from engine.station_runner import parser

# Same two steps as the working "Python Clean Library\CLEAN_LIBRARY.bat", minus its zip prompt:
# sort loose files into channel folders, then clean new/changed transcripts into Obsidian notes.
# Uses the downloader's venv (it has the local punctuation model); cleaning stays pure Python.
def main() -> int:
    args,_=parser("02_YT_CLEAN").parse_known_args()
    root=external("legacy_youtube"); lib=root/"Python Clean Library"
    subs=external("subtitles"); notes=root/"obsidian_transcripts"
    venv=root/"venv"/"Scripts"/"python.exe"
    py=str(venv) if venv.is_file() else sys.executable
    has_punct=subprocess.run([py,"-c","import punctuators"],capture_output=True).returncode==0
    sort=[py,str(lib/"sort_by_channel.py"),"--dir",str(subs),"--apply"]
    clean=[py,str(lib/"clean_library.py"),"--src",str(subs),"--out",str(notes)]
    if has_punct: clean.append("--punctuate")
    if args.limit: clean+=["--limit",str(args.limit)]
    for item in args.items: clean+=["--channel",Path(item).name]
    if args.redo: clean.append("--force")
    print("PLAN",json.dumps({"station":"02_YT_CLEAN","commands":[sort,clean],"dry_run":args.dry_run},ensure_ascii=False))
    if args.dry_run: return 0
    for cmd in (sort,clean):
        rc=subprocess.run(cmd,cwd=lib).returncode
        if rc: return rc
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
