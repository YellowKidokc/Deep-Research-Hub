import sys
from pathlib import Path
from FolderWatcher import FolderWatcher


def my_function(changed: list[tuple[str, Path]]) -> None:
    """Replace this with your own logic."""
    print("Printing from callback function:")
    for event_type, path in changed:
        print(f"{event_type}: {path}")


folder = sys.argv[1] if len(sys.argv) > 1 else "."

FolderWatcher(path=folder, callback=my_function, return_mode="files").run_forever()
