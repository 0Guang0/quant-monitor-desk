"""Windows long-path helpers for raw evidence I/O."""

from __future__ import annotations

import os
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
