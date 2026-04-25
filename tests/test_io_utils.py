import json
import os
from pathlib import Path

import pytest

from src import io_utils
from src.io_utils import atomic_write_json, atomic_write_text


def test_atomic_write_text_creates_new_file(tmp_path):
    path = tmp_path / "nested" / "note.txt"

    atomic_write_text(path, "hello")

    assert path.read_text(encoding="utf-8") == "hello"


def test_atomic_write_text_replaces_existing_file(tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("old", encoding="utf-8")

    atomic_write_text(path, "new")

    assert path.read_text(encoding="utf-8") == "new"


def test_atomic_write_json_writes_valid_json(tmp_path):
    path = tmp_path / "payload.json"
    payload = {"message": "hello", "items": [1, 2, 3]}

    atomic_write_json(path, payload)

    assert json.loads(path.read_text(encoding="utf-8")) == payload


@pytest.mark.skipif(os.name == "nt", reason="component length semantics differ on Windows")
def test_atomic_write_text_handles_long_legal_target_name(tmp_path):
    path = tmp_path / ("a" * 240)

    atomic_write_text(path, "long")

    assert path.read_text(encoding="utf-8") == "long"


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits are not stable on Windows")
def test_atomic_write_text_uses_umask_permissions_for_new_file(tmp_path):
    atomic_path = tmp_path / "atomic.txt"
    regular_path = tmp_path / "regular.txt"

    previous_umask = os.umask(0o022)
    try:
        atomic_write_text(atomic_path, "atomic")
        regular_path.write_text("regular", encoding="utf-8")
    finally:
        os.umask(previous_umask)

    assert (atomic_path.stat().st_mode & 0o777) == (regular_path.stat().st_mode & 0o777)
    assert (atomic_path.stat().st_mode & 0o777) == 0o644


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits are not stable on Windows")
def test_atomic_write_text_preserves_existing_file_mode(tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("old", encoding="utf-8")
    os.chmod(path, 0o640)

    atomic_write_text(path, "new")

    assert path.read_text(encoding="utf-8") == "new"
    assert (path.stat().st_mode & 0o777) == 0o640


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits are not stable on Windows")
def test_atomic_write_text_keeps_restricted_replacement_temp_mode(tmp_path, monkeypatch):
    path = tmp_path / "secret.txt"
    path.write_text("old", encoding="utf-8")
    os.chmod(path, 0o600)
    created_modes: list[int] = []
    real_create_temporary_file = io_utils._create_temporary_file

    def recording_create_temporary_file(target, mode):
        fd, temp_path = real_create_temporary_file(target, mode)
        created_modes.append(temp_path.stat().st_mode & 0o777)
        return fd, temp_path

    monkeypatch.setattr(io_utils, "_create_temporary_file", recording_create_temporary_file)

    previous_umask = os.umask(0o022)
    try:
        atomic_write_text(path, "new")
    finally:
        os.umask(previous_umask)

    assert created_modes == [0o600]
    assert path.read_text(encoding="utf-8") == "new"
    assert (path.stat().st_mode & 0o777) == 0o600


def test_atomic_write_text_uses_fsync_and_atomic_replace(tmp_path, monkeypatch):
    path = tmp_path / "note.txt"
    fsync_calls: list[int] = []
    replace_calls: list[tuple[Path, Path]] = []
    real_fsync = os.fsync
    real_replace = os.replace

    def recording_fsync(fd):
        fsync_calls.append(fd)
        real_fsync(fd)

    def recording_replace(src, dst):
        replace_calls.append((Path(src), Path(dst)))
        real_replace(src, dst)

    monkeypatch.setattr(io_utils.os, "fsync", recording_fsync)
    monkeypatch.setattr(io_utils.os, "replace", recording_replace)

    atomic_write_text(path, "durable")

    assert fsync_calls
    assert replace_calls
    temp_path, target_path = replace_calls[0]
    assert temp_path.parent == path.parent
    assert target_path == path
    assert path.read_text(encoding="utf-8") == "durable"


def test_atomic_write_text_cleans_temp_file_when_replace_fails(tmp_path, monkeypatch):
    path = tmp_path / "note.txt"
    path.write_text("old", encoding="utf-8")
    replace_calls: list[tuple[Path, Path]] = []

    def failing_replace(src, dst):
        replace_calls.append((Path(src), Path(dst)))
        raise OSError("replace failed")

    monkeypatch.setattr(io_utils.os, "replace", failing_replace)

    with pytest.raises(OSError, match="replace failed"):
        atomic_write_text(path, "new")

    assert replace_calls
    assert replace_calls[0][0].parent == path.parent
    assert path.read_text(encoding="utf-8") == "old"
    assert sorted(item.name for item in tmp_path.iterdir()) == ["note.txt"]
