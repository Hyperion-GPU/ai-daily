from __future__ import annotations

import json
import os
import secrets
from pathlib import Path


def _create_temporary_file(target: Path, mode: int) -> tuple[int, Path]:
    for _ in range(100):
        candidate = target.parent / f".{target.name}.{secrets.token_hex(8)}"
        try:
            fd = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        except FileExistsError:
            continue
        return fd, candidate
    raise FileExistsError(f"Could not create a unique temporary file for {target}")


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """Write text by fsyncing a same-directory temp file before atomic replace."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    fd: int | None = None
    try:
        target_mode = target.stat().st_mode & 0o777
    except FileNotFoundError:
        target_mode = None

    try:
        create_mode = target_mode if target_mode is not None else 0o666
        fd, temp_path = _create_temporary_file(target, create_mode)
        if target_mode is not None:
            os.chmod(temp_path, target_mode)
        with os.fdopen(fd, "w", encoding=encoding) as temp_file:
            fd = None
            temp_file.write(text)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        if target_mode is not None:
            os.chmod(temp_path, target_mode)
        os.replace(temp_path, target)
        temp_path = None
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def atomic_write_json(
    path: Path,
    payload: object,
    *,
    ensure_ascii: bool = False,
    indent: int | None = 2,
) -> None:
    """Serialize JSON and write it through atomic_write_text."""
    atomic_write_text(path, json.dumps(payload, ensure_ascii=ensure_ascii, indent=indent))
