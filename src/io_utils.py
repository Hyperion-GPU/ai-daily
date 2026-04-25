from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """Write text by fsyncing a same-directory temp file before atomic replace."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        target_mode = target.stat().st_mode & 0o777
    except FileNotFoundError:
        target_mode = None

    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding=encoding,
            dir=target.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(text)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        if target_mode is not None:
            os.chmod(temp_path, target_mode)
        os.replace(temp_path, target)
        temp_path = None
    finally:
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
