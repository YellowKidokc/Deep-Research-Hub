# Theophysics Labeler (CocoIndex)

This pipeline labels every file in a folder, writes a `.fistag` JSON sidecar beside each one (the same format as `fistag.py`, which FIS reads), and then reports
duplicates and empty folders.

```powershell
cd D:\GitHub\deep-research-hub\apps\cocoindex\examples\theophysics_labeler
python main.py run "D:\some\folder"            # label + sidecar, then duplicates + empty folders
python main.py run                             # same folders as last time
python main.py run "D:\some\folder" --live     # then keep labeling as files change (Ctrl+C stops)
python main.py report                          # duplicates + empty folders only
python main.py run --remove-empty              # also remove folders that are completely empty
python main.py run --full                      # re-label everything
```

## What happens

1. **Label + sidecar.** CocoIndex walks the folders and treats each file as one component.
   - Documents (`.md .txt .pdf .docx .html`) are labeled against `C:\Theophysics_Tagger`'s registry with the
     Convergence Tagger engine. That gives primary tag and category, tags, Master Equation variables and scripture refs.
   - Every other file gets a kind (image, audio, video, code, data, archive ...) plus filename keywords.
   - Each file gets `<file>.fistag` beside it (FIS codes such as `NO.AXM · RUN · --`, plus label, tags, scripture, sha256) and a row in `state/index.db`.
   - It's incremental. An unchanged file is skipped without being re-read (memo on path + size + mtime + registry).
     A deleted file loses its sidecar and row. Editing the registry re-labels everything.
2. **Duplicates.** `state/reports/duplicates.csv` lists exact copies (same sha256). Each group marks the copy to
   keep (the shortest path) and the copies that are `duplicate`, sorted by reclaimable space.
   `same_text.csv` lists documents with the same words in different bytes, such as copies whose frontmatter differs.
3. **Empty folders.** `state/reports/empty_folders.csv` lists folders with no real files anywhere beneath them, and
   says whether each one is truly empty, holds only empty subfolders, or holds only `desktop.ini` or sidecars.
   Nothing is removed unless you pass `--remove-empty`, and even then only completely empty folders go.

`state/reports/summary.md` has the totals. `problems.csv` lists files it couldn't read, such as empty files or
image-only PDFs.

## Notes

- Nothing is ever moved or deleted except the sidecars this pipeline wrote, and those only go when their file is gone or
  the folder is dropped from the list.
- Skipped: `.git`, `node_modules`, `.obsidian`, `__pycache__`, `.venv`, recycle bin, `desktop.ini`, `Thumbs.db`, and
  existing `.fistag` / `.fmeta` / `.fisnote` sidecars.
- Environment: `THEO_TAGGER_ROOT` (default `C:\Theophysics_Tagger`) and `LABELER_STATE` (default `./state`).
