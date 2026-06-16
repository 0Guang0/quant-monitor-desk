"""Single-writer DuckDB connection manager with file lock."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import duckdb
import yaml
from backend.app.config import CONFIGS_ROOT, DATA_ROOT, get_resource_profile

if TYPE_CHECKING:
    from collections.abc import Iterator


_MAX_LOCK_RETRIES = 5


class WriteLockError(RuntimeError):
    """Raised when another process holds the write lock."""


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def _load_profile_limits(profile: str, limits: dict | None) -> dict:
    if limits is not None:
        return limits.get(profile, limits.get("eco", {}))
    config_path = CONFIGS_ROOT / "resource_limits.yaml"
    with config_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["profiles"][profile]


def _escape_sql_string(value: str) -> str:
    return value.replace("'", "''")


class ConnectionManager:
    def __init__(
        self,
        db_path: Path,
        profile: str | None = None,
        limits: dict | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        self.profile = profile or get_resource_profile()
        self._limits = limits
        self._lock_path = self.db_path.with_suffix(self.db_path.suffix + ".write.lock")
        self._lock_fd: int | None = None

    def _read_lock_payload(self) -> dict | None:
        if not self._lock_path.exists():
            return None
        try:
            payload = json.loads(self._lock_path.read_text(encoding="utf-8"))
        except PermissionError as exc:
            raise WriteLockError("write lock held by another process") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise WriteLockError(
                f"corrupt write lock file at {self._lock_path}; manual cleanup required"
            ) from exc
        if not isinstance(payload, dict):
            raise WriteLockError(
                f"corrupt write lock file at {self._lock_path}; manual cleanup required"
            )
        return payload

    def _try_remove_stale_lock(self) -> bool:
        payload = self._read_lock_payload()
        if payload is None:
            return True
        pid = int(payload.get("pid", 0))
        if _pid_alive(pid):
            raise WriteLockError(f"write lock held by pid {pid}")
        self._lock_path.unlink(missing_ok=True)
        return True

    def _acquire_lock(self) -> None:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        for _ in range(_MAX_LOCK_RETRIES):
            try:
                fd = os.open(str(self._lock_path), flags, 0o644)
                break
            except FileExistsError:
                self._try_remove_stale_lock()
        else:
            raise WriteLockError(
                f"could not acquire write lock after {_MAX_LOCK_RETRIES} attempts"
            )

        payload = {
            "pid": os.getpid(),
            "started_at": datetime.now(UTC).isoformat(),
            "target": str(self.db_path),
        }
        payload_bytes = json.dumps(payload).encode("utf-8")
        os.write(fd, payload_bytes)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(fd, msvcrt.LK_NBLCK, len(payload_bytes))
        else:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self._lock_fd = fd

    def _release_lock(self) -> None:
        if self._lock_fd is not None:
            if os.name == "nt":
                import msvcrt

                lock_size = os.fstat(self._lock_fd).st_size or 1
                msvcrt.locking(self._lock_fd, msvcrt.LK_UNLCK, lock_size)
            else:
                import fcntl

                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
            os.close(self._lock_fd)
            self._lock_fd = None
        self._lock_path.unlink(missing_ok=True)

    def _apply_pragmas(self, con: duckdb.DuckDBPyConnection) -> None:
        profile_limits = _load_profile_limits(self.profile, self._limits)
        memory_mb = int(profile_limits.get("duckdb_memory_max_mb", 1536))
        threads = int(profile_limits.get("max_threads", 2))
        temp_dir = DATA_ROOT / "cache" / "duckdb_tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = _escape_sql_string(temp_dir.as_posix())
        con.execute(f"SET memory_limit = '{memory_mb}MB'")
        con.execute(f"SET threads = {threads}")
        con.execute(f"SET temp_directory = '{temp_path}'")

    @contextmanager
    def writer(self) -> Iterator[duckdb.DuckDBPyConnection]:
        """Exclusive writable connection with file lock."""
        self._acquire_lock()
        con: duckdb.DuckDBPyConnection | None = None
        try:
            con = duckdb.connect(str(self.db_path))
            self._apply_pragmas(con)
            yield con
        finally:
            if con is not None:
                con.close()
            self._release_lock()

    @contextmanager
    def reader(self) -> Iterator[duckdb.DuckDBPyConnection]:
        """Read-only connection; multiple readers allowed."""
        con = duckdb.connect(str(self.db_path), read_only=True)
        try:
            self._apply_pragmas(con)
            yield con
        finally:
            con.close()
