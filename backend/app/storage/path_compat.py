"""Windows long-path helpers for raw evidence I/O."""

from __future__ import annotations

import os
import secrets
from pathlib import Path, PureWindowsPath

_WIN_MAX_PATH = 260


def _path_text(path: Path | str) -> str:
    return os.path.abspath(str(path))


def needs_extended_path(path: Path | str) -> bool:
    if os.name != "nt":
        return False
    return len(_path_text(path)) >= _WIN_MAX_PATH


def to_extended_path(path: Path | str) -> Path:
    """Return a Path usable for filesystem ops when Windows MAX_PATH would block I/O."""
    p = Path(path)
    if os.name != "nt":
        return p
    text = _path_text(p)
    if text.startswith("\\\\?\\"):
        return Path(text)
    if len(text) < _WIN_MAX_PATH:
        return Path(text)
    if text.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + text[2:])
    return Path("\\\\?\\" + text)


def mkdir_parents(path: Path, *, exist_ok: bool = False) -> None:
    text = _path_text(path)
    if os.name != "nt" or len(text) < _WIN_MAX_PATH:
        path.mkdir(parents=True, exist_ok=exist_ok)
        return
    os.makedirs(str(to_extended_path(path)), exist_ok=exist_ok)


def write_bytes(path: Path, data: bytes) -> None:
    to_extended_path(path).write_bytes(data)


def write_bytes_atomic(path: Path, data: bytes) -> None:
    """Write bytes atomically via same-dir temp file and os.replace.

    Caller must validate path containment (e.g. data_root sandbox) before calling.
    ponytail: same-dir temp + os.replace is crash-safe on POSIX/NT; ceiling—no
    parent-dir fsync (directory durability on power loss), full payload in RAM.
    """
    dest = Path(path)
    temp_path = dest.parent / f".{dest.name}.tmp.{os.getpid()}.{secrets.token_hex(4)}"
    extended_temp = to_extended_path(temp_path)
    extended_dest = to_extended_path(dest)
    try:
        with open(extended_temp, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(extended_temp), str(extended_dest))
    except BaseException:
        try:
            extended_temp.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def read_bytes(path: Path) -> bytes:
    return to_extended_path(path).read_bytes()


def is_file(path: Path) -> bool:
    return to_extended_path(path).is_file()


def is_relative_to_data_root(path: Path, data_root: Path) -> bool:
    """Path containment check that tolerates Windows extended-path prefixes."""
    resolved = Path(_path_text(path))
    root = Path(_path_text(data_root))
    try:
        resolved.relative_to(root)
        return True
    except ValueError:
        pass
    resolved_text = PureWindowsPath(str(resolved)).as_posix().lower()
    root_text = PureWindowsPath(str(root)).as_posix().lower()
    return resolved_text == root_text or resolved_text.startswith(root_text + "/")
