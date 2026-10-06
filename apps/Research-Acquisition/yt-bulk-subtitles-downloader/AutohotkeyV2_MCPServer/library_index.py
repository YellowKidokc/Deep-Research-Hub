"""Symbol-aware indexer for the user's global AHK v2 library.

Scans every .ahk file under the configured library path for:
  - class declarations: `class Name [extends Base]`
  - top-level functions: `Name(args) {` or `Name(args) =>`
  - class methods (indented): `Name(args) {` or `Name(args) =>`

Persists the index to AppData and invalidates on source-tree mtime change.
"""
import os
import re
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

_CLASS_RE = re.compile(r'^\s*class\s+(\w+)(?:\s+extends\s+([\w.]+))?\s*\{?')
_FUNC_RE = re.compile(r'^(\s*)((?:static\s+)?\w+)\s*\(([^)]*)\)\s*([{=])')
_COMMENT_LINE_RE = re.compile(r'^\s*;')

_CONTROL_FLOW = {
    "if", "while", "for", "loop", "until", "switch", "case",
    "return", "throw", "try", "catch", "finally", "else",
}


class LibraryIndex:
    def __init__(self, lib_path: Path, index_file: Path):
        self.lib_path = Path(lib_path)
        self.index_file = Path(index_file)
        self._symbols: List[Dict[str, Any]] = []

    def ensure_built(self) -> None:
        """Build or load the index; invalidate on source mtime change."""
        if self.index_file.exists():
            try:
                src_mtime = self._max_source_mtime()
                idx_mtime = self.index_file.stat().st_mtime
                if src_mtime <= idx_mtime:
                    self._load()
                    if self._symbols:
                        return
            except Exception:
                pass
        self._build()
        self._save()

    def _max_source_mtime(self) -> float:
        if not self.lib_path.exists():
            return 0.0
        max_mtime = 0.0
        for root, _dirs, files in os.walk(self.lib_path):
            for f in files:
                if f.lower().endswith('.ahk'):
                    try:
                        mt = os.path.getmtime(os.path.join(root, f))
                        if mt > max_mtime:
                            max_mtime = mt
                    except OSError:
                        pass
        return max_mtime

    def _build(self) -> None:
        symbols: List[Dict[str, Any]] = []
        if self.lib_path.exists():
            for root, _dirs, files in os.walk(self.lib_path):
                for fname in files:
                    if not fname.lower().endswith('.ahk'):
                        continue
                    full = os.path.join(root, fname)
                    try:
                        with open(full, 'r', encoding='utf-8', errors='replace') as f:
                            lines = f.readlines()
                    except Exception:
                        continue
                    try:
                        rel = os.path.relpath(full, self.lib_path)
                    except ValueError:
                        rel = full
                    self._scan_file(rel, lines, symbols)
        self._symbols = symbols

    def _scan_file(self, rel_path: str, lines: List[str], out: List[Dict[str, Any]]) -> None:
        in_block_comment = False
        for i, line in enumerate(lines):
            line_no = i + 1
            stripped = line.strip()

            if in_block_comment:
                if '*/' in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith('/*'):
                if '*/' not in stripped:
                    in_block_comment = True
                continue

            if _COMMENT_LINE_RE.match(line):
                continue

            cm = _CLASS_RE.match(line)
            if cm:
                name = cm.group(1)
                base = cm.group(2) or ""
                signature = f"class {name}" + (f" extends {base}" if base else "")
                out.append({
                    "name": name,
                    "kind": "class",
                    "file": rel_path,
                    "line": line_no,
                    "signature": signature,
                    "extends": base,
                })
                continue

            fm = _FUNC_RE.match(line)
            if fm:
                indent = fm.group(1)
                name_raw = fm.group(2).strip()
                args = fm.group(3).strip()
                name = re.sub(r'^static\s+', '', name_raw)
                if name.lower() in _CONTROL_FLOW:
                    continue
                kind = "method" if indent else "function"
                signature = f"{name_raw}({args})"
                out.append({
                    "name": name,
                    "kind": kind,
                    "file": rel_path,
                    "line": line_no,
                    "signature": signature,
                })

    def _load(self) -> None:
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._symbols = data.get("symbols", []) if isinstance(data, dict) else []
        except Exception:
            self._symbols = []

    def _save(self) -> None:
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            prefix=".libindex-", suffix=".tmp",
            dir=str(self.index_file.parent),
        )
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(
                    {"version": 1, "lib_path": str(self.lib_path), "symbols": self._symbols},
                    f,
                )
            os.replace(tmp_path, self.index_file)
        except Exception:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            raise

    def search(self, query: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        if not query:
            return []
        needle = query.lower()
        matches = [s for s in self._symbols if needle in s["name"].lower()]
        return matches[offset:offset + limit]

    @property
    def total(self) -> int:
        return len(self._symbols)


_index: Optional[LibraryIndex] = None


def get_index(lib_path: Path, index_file: Path) -> LibraryIndex:
    """Singleton accessor; rebuilds when lib_path changes."""
    global _index
    if _index is None or str(_index.lib_path) != str(Path(lib_path)):
        _index = LibraryIndex(lib_path, index_file)
        _index.ensure_built()
    return _index


def reset() -> None:
    """Drop the cached index; next get_index() rebuilds."""
    global _index
    _index = None
