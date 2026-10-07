"""Read receipt: what a research run actually read, kept and dropped.

One ReadReceipt per GPTResearcher. The document loader records every file it
finds (loaded, or skipped and why); the context compressor records, per
sub-query, how many chunks it produced, how many passed the similarity
filter, and how many survived the top-N cut, broken down by source. Nothing
here changes what the researcher does; it only writes down what happened.

    receipt.to_dict()        # plain JSON-able dict
    receipt.write(path)      # JSON file next to the report
"""
from __future__ import annotations

import json
import os
import threading
import time
from collections import defaultdict
from typing import Any


class ReadReceipt:
    def __init__(self, query: str = "", doc_path: str | None = None, report_source: str | None = None):
        self._lock = threading.Lock()
        self.query = query
        self.doc_path = doc_path
        self.report_source = report_source
        self.started = time.time()
        self.settings: dict[str, Any] = {}
        self.files: dict[str, dict[str, Any]] = {}
        self.sub_queries: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []

    # ---------------------------------------------------------------- files
    def file_found(self, path: str, size: int | None = None) -> None:
        with self._lock:
            self.files[path] = {"path": path, "bytes": size, "status": "found"}

    def file_loaded(self, path: str, pages: int, chars: int) -> None:
        with self._lock:
            f = self.files.setdefault(path, {"path": path})
            f.update(status="loaded", pages=pages, chars=chars)

    def file_skipped(self, path: str, reason: str) -> None:
        with self._lock:
            f = self.files.setdefault(path, {"path": path})
            f.update(status="skipped", reason=reason)

    # ---------------------------------------------------------- compression
    def compression(self, sub_query: str, *, path: str, documents: int, truncated: int,
                    threshold: float | None, max_results: int,
                    per_source: dict[str, dict[str, int]]) -> None:
        """One context-compression pass for one sub-query.

        path: "fast" (small input, no similarity filter) or "filtered".
        per_source: {source: {"chunks": n, "kept": n, "returned": n}}.
        """
        totals = defaultdict(int)
        for counts in per_source.values():
            for k, v in counts.items():
                totals[k] += v
        with self._lock:
            self.sub_queries.append({
                "sub_query": sub_query,
                "path": path,
                "documents_in": documents,
                "documents_truncated": truncated,
                "similarity_threshold": threshold,
                "max_results": max_results,
                "chunks_produced": totals["chunks"],
                "chunks_kept": totals["kept"],
                "chunks_dropped_by_similarity": totals["chunks"] - totals["kept"],
                "chunks_returned": totals["returned"],
                "chunks_cut_by_max_results": totals["kept"] - totals["returned"],
                # EmbeddingsFilter keeps chunks in document order and the context
                # takes the first max_results of them: the cut is by position.
                "max_results_cut": "first N kept chunks in document order" if path == "filtered" else "first N documents",
                "by_source": per_source,
            })

    def sub_query_error(self, sub_query: str, error: str) -> None:
        """A sub-query that failed: it contributed nothing, and the run went on."""
        with self._lock:
            self.errors.append({"sub_query": sub_query, "error": error[:500]})

    # --------------------------------------------------------------- output
    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            files = sorted(self.files.values(), key=lambda f: f["path"])
            subs = list(self.sub_queries)
            errors = list(self.errors)
        skipped: dict[str, int] = defaultdict(int)
        for f in files:
            if f.get("status") == "skipped":
                skipped[f.get("reason", "unknown").split(":")[0]] += 1
        contributed = {s for q in subs for s, c in q["by_source"].items() if c.get("returned")}
        local = {f["path"] for f in files if f.get("status") == "loaded"}
        return {
            "receipt_version": 1,
            "query": self.query,
            "report_source": self.report_source,
            "doc_path": self.doc_path,
            "started": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.started)),
            "settings": self.settings,
            "summary": {
                "files_found": len(files),
                "files_loaded": sum(1 for f in files if f.get("status") == "loaded"),
                "files_skipped": sum(1 for f in files if f.get("status") == "skipped"),
                "skipped_by_reason": dict(skipped),
                "sub_queries": len(subs),
                "sub_query_errors": len(errors),
                "chunks_produced": sum(q["chunks_produced"] for q in subs),
                "chunks_kept": sum(q["chunks_kept"] for q in subs),
                "chunks_returned": sum(q["chunks_returned"] for q in subs),
                "local_files_that_reached_context": len(local & contributed),
                "local_files_never_used": sorted(local - contributed),
            },
            "files": files,
            "sub_queries": subs,
            "errors": errors,
        }

    def write(self, path: str) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        return path
