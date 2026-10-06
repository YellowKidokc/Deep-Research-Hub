# Hister folder queue

Hister's web page is primarily for searching. Local folders are submitted with
the command-line client. These launchers process folders sequentially so several
large locations are not imported at once.

## Use

1. Edit either `GROUP_1_DESKTOP_PAGES.txt` or `GROUP_2_THEOPHYSICS.txt`.
2. Put one complete folder path on each line.
3. Double-click the matching `.bat` launcher once.
4. Leave it running. Each directory is scanned recursively, one after another.

Existing indexed documents are skipped. Rerunning a group is therefore a safe
way to pick up new files without deliberately reprocessing everything. Logs and
CSV receipts are written beneath `logs\`.

`HISTER_STATUS.bat` reports the current indexed-document count and all durable
website crawl jobs. Website crawls and folder imports are separate operations:
website crawl jobs are resumable queues, while local-folder reruns rely on
`--skip-existing`.

`RUN_ALL_GROUPS.bat` runs Group 1 and then Group 2 sequentially. It never runs
the two imports concurrently.

No launcher deletes, moves, renames, or edits source files.
