"""
CureVerseAI — AI Engine
Generic disk-backed cache.

Purpose
-------

Several CureVerseAI clients make expensive HTTP calls whose
results are stable for days or weeks:

    - Ensembl gene lookups
    - UniProt accession resolution
    - (future) Reactome pathway lookups

Caching these on disk turns 2-3 minute requests into
sub-second repeats, which is essential for any live demo.

Design
------

- Key = SHA256 of (prefix + separator + identifier)
- Value = JSON-serializable payload
- Storage = one file per key under a root directory
- Each file contains {"timestamp": <unix>, "value": <payload>}
- Reads check TTL against the current time

Failure model
-------------

Cache read or write failures MUST NOT break the caller.
Any I/O error, decode error, or malformed payload is
treated as a cache miss, silently. The caller should
behave exactly as if the cache did not exist.

No new libraries. Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional


class DiskCache:
    """
    Minimal TTL-based disk cache.

    Not thread-safe. Intended for sequential use inside a
    single process. If a caller needs concurrency, guard
    reads and writes at the call site or extend this class.
    """

    def __init__(
        self,
        root_dir: str | Path,
        ttl_seconds: int = 30 * 24 * 3600,
    ):
        self.root = Path(root_dir)
        self.ttl_seconds = int(ttl_seconds)

        try:
            self.root.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Cache directory creation failure is non-fatal.
            # All later operations will silently miss.
            pass

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    @staticmethod
    def make_key(
        prefix: str,
        identifier: str,
    ) -> str:
        """
        Derive a filesystem-safe key from a prefix and
        identifier pair. Uses SHA256 so the input may
        contain any characters.
        """

        raw = f"{prefix}|{identifier}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _path_for(self, key: str) -> Path:
        return self.root / f"{key}.json"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[Any]:
        """
        Return the cached value if it exists and is
        unexpired; otherwise None.
        """

        path = self._path_for(key)

        try:
            if not path.is_file():
                return None

            raw = path.read_text(encoding="utf-8")
            record = json.loads(raw)

            timestamp = float(record.get("timestamp", 0))
            age = time.time() - timestamp

            if age > self.ttl_seconds:
                # Expired. Do not delete; leave for manual
                # inspection and allow a subsequent set()
                # to overwrite.
                return None

            return record.get("value")

        except (OSError, ValueError, TypeError):
            # Any failure is treated as a miss.
            return None

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store a JSON-serializable value under key. Failures
        are silent.
        """

        path = self._path_for(key)

        record = {
            "timestamp": time.time(),
            "value": value,
        }

        try:
            payload = json.dumps(record)
            path.write_text(payload, encoding="utf-8")
        except (OSError, ValueError, TypeError):
            # Write failure is non-fatal.
            pass

    def clear(self) -> int:
        """
        Delete every cached file under the root directory.
        Returns the number of files removed. Failures are
        silent (the count reflects only successful unlinks).
        """

        removed = 0

        try:
            for path in self.root.glob("*.json"):
                try:
                    path.unlink()
                    removed += 1
                except OSError:
                    continue
        except OSError:
            pass

        return removed
