"""Local raw file storage."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

_EXT_MAP = {"json": "json", "csv": "csv", "parquet": "parquet"}
_SEGMENT = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")
MAX_RAW_FILE_BYTES = 256 * 1024 * 1024


def sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _safe_segment(label: str, value: str) -> str:
    if not _SEGMENT.fullmatch(value):
        raise ValueError(f"invalid {label}: {value!r}")
    return value


@dataclass(frozen=True)
class SavedFile:
    file_id: str
    source: str
    data_domain: str
    local_path: str
    content_hash: str
    file_type: str
    as_of: str


class RawStore:
    def __init__(self, data_root: Path) -> None:
        self.data_root = Path(data_root).resolve()

    def save(
        self,
        content: bytes,
        *,
        source: str,
        data_domain: str,
        file_type: str,
        as_of: str,
    ) -> SavedFile:
        if len(content) > MAX_RAW_FILE_BYTES:
            raise ValueError(
                f"raw file exceeds max size ({len(content)} > {MAX_RAW_FILE_BYTES} bytes)"
            )
        if file_type not in _EXT_MAP:
            raise ValueError(f"unsupported file_type: {file_type!r}")
        safe_source = _safe_segment("source", source)
        safe_domain = _safe_segment("data_domain", data_domain)
        safe_as_of = _safe_segment("as_of", as_of)

        content_hash = sha256_hex(content)
        ext = _EXT_MAP[file_type]
        rel_dir = Path("raw") / safe_source / safe_domain / safe_as_of
        dest_dir = self.data_root / rel_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{content_hash}.{ext}"
        dest_path = (dest_dir / filename).resolve()
        if not dest_path.is_relative_to(self.data_root):
            raise ValueError("path escapes data_root")
        dest_path.write_bytes(content)
        file_id = content_hash[:16] + safe_source
        return SavedFile(
            file_id=file_id,
            source=safe_source,
            data_domain=safe_domain,
            local_path=str(dest_path),
            content_hash=content_hash,
            file_type=file_type,
            as_of=safe_as_of,
        )
