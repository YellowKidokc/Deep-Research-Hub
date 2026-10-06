"""
Portable single-folder relay watcher.

Drop this file (plus FolderWatcher.py and relay.yaml) into any folder.
It watches that folder and copies/moves new files to configured destinations,
optionally running a command on each.

Usage:
  python relay_watch.py              # watch forever
  python relay_watch.py --backfill   # relay existing files once, then watch
  python relay_watch.py --dry-run    # log what would be done
  python relay_watch.py --once       # one pass, then exit
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import pathlib
import shutil
import subprocess
import sys

from FolderWatcher import FolderWatcher

HERE = pathlib.Path(__file__).resolve().parent
CONFIG = HERE / "relay.yaml"
DEFAULT_LOG = HERE / "relay_watch.log"
DEFAULT_STATE = HERE / ".relay_state.json"


def log(path: pathlib.Path, msg: str) -> None:
    line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(line.encode("utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace"), flush=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_config(path: pathlib.Path) -> dict:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required: pip install pyyaml") from exc
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_state(path: pathlib.Path) -> dict:
    if not path.exists():
        return {"relayed": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(path: pathlib.Path, state: dict) -> None:
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    tmp.replace(path)


def should_ignore(path: pathlib.Path, ignore: list[str]) -> bool:
    name = path.name
    if name.startswith("."):
        return True
    for pat in ignore:
        if fnmatch.fnmatch(name, pat):
            return True
    return False


def expand(cmd: str, src: pathlib.Path) -> str:
    mapping = {
        "{path}": str(src),
        "{name}": src.name,
        "{stem}": src.stem,
        "{ext}": src.suffix,
        "{parent}": str(src.parent),
    }
    for key, val in mapping.items():
        cmd = cmd.replace(key, val)
    return cmd


def relay_file(
    path: pathlib.Path,
    rule: dict,
    state: dict,
    dry_run: bool,
    log_file: pathlib.Path,
) -> None:
    action = rule.get("action", "copy")
    destinations = rule.get("destinations", [])
    if isinstance(destinations, str):
        destinations = [destinations]

    log(log_file, f"relay '{rule.get('name', 'unnamed')}': {path.name}")

    current = path

    if dry_run:
        for dest_str in destinations:
            dest = pathlib.Path(dest_str).expanduser()
            target = dest / current.name
            log(log_file, f"  would {action} -> {target}")
        return

    for dest_str in destinations:
        dest = pathlib.Path(dest_str).expanduser()
        target = dest / current.name
        dest.mkdir(parents=True, exist_ok=True)
        if action == "move":
            shutil.move(str(current), str(target))
            current = target
        elif action == "copy":
            shutil.copy2(str(current), str(target))
        else:
            log(log_file, f"  unknown action: {action}")
            return

    state["relayed"][str(path)] = {
        "time": dt.datetime.now().isoformat(),
        "rule": rule.get("name"),
    }

    command = rule.get("command")
    if command:
        cmd = expand(command, current)
        log(log_file, f"  command: {cmd}")
        if not dry_run:
            rc = subprocess.run(cmd, shell=True, check=False).returncode
            if rc != 0:
                log(log_file, f"  warning: command exited {rc}")


def _patterns(rule: dict) -> list[str]:
    raw = rule.get("match", "*")
    if isinstance(raw, str):
        return [raw]
    return list(raw)


def find_rule(rules: list[dict], path: pathlib.Path) -> dict | None:
    for rule in rules:
        if any(fnmatch.fnmatch(path.name, pat) for pat in _patterns(rule)):
            return rule
    return None


def process_file(
    path: pathlib.Path,
    config: dict,
    state: dict,
    dry_run: bool,
    log_file: pathlib.Path,
) -> None:
    ignore = config.get("ignore", ["*.tmp", "*.swp", "~$*"])
    if should_ignore(path, ignore):
        return
    if not path.is_file():
        return
    if str(path) in state.get("relayed", {}):
        return

    rule = find_rule(config.get("routes", []), path)
    if rule:
        relay_file(path, rule, state, dry_run, log_file)
    else:
        log(log_file, f"no route for {path.name}")


def on_change(
    changed: list[tuple[str, pathlib.Path]],
    config: dict,
    state: dict,
    dry_run: bool,
    log_file: pathlib.Path,
) -> None:
    files = {path for event, path in changed if event in ("created", "modified")}
    for path in sorted(files):
        process_file(path, config, state, dry_run, log_file)


def backfill(
    config: dict,
    state: dict,
    dry_run: bool,
    log_file: pathlib.Path,
) -> None:
    rules = config.get("routes", [])
    patterns = set()
    for rule in rules:
        for pat in _patterns(rule):
            patterns.add(pat)

    files: list[pathlib.Path] = []
    for pat in patterns:
        files.extend(HERE.glob(pat))

    log(log_file, f"backfill: {len(files)} candidate file(s)")
    for path in sorted(set(files)):
        process_file(path, config, state, dry_run, log_file)


def main() -> int:
    ap = argparse.ArgumentParser(description=f"Relay watcher for {HERE.name}.")
    ap.add_argument("--config", type=pathlib.Path, default=CONFIG)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backfill", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--debounce", type=float, default=2.0)
    args = ap.parse_args()

    if not args.config.exists():
        print(f"config not found: {args.config}", file=sys.stderr)
        return 1

    config = load_config(args.config)
    log_file = pathlib.Path(config.get("log", DEFAULT_LOG)).expanduser()
    state_file = pathlib.Path(config.get("state", DEFAULT_STATE)).expanduser()
    state = load_state(state_file)

    log(log_file, f"relay watcher started: {HERE}")

    if args.backfill:
        backfill(config, state, args.dry_run, log_file)
        save_state(state_file, state)
        if args.once:
            return 0

    def callback(changed):
        try:
            on_change(changed, config, state, args.dry_run, log_file)
            save_state(state_file, state)
        except Exception as e:
            log(log_file, f"error in callback: {e}")

    watcher = FolderWatcher(
        path=str(HERE),
        callback=callback,
        recursive=True,
        debounce=args.debounce,
        return_mode="files",
    )

    if args.once:
        log(log_file, "--once: nothing to watch; exiting")
        return 0

    try:
        watcher.run_forever()
    except KeyboardInterrupt:
        log(log_file, "stopped by user")
    return 0


if __name__ == "__main__":
    sys.exit(main())
