from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXE = REPO_ROOT / "dist" / "AI Daily.exe"
DESKTOP_DATA_DIRNAME = "AI Daily"
REMOVED_ERROR_TOKENS = (
    "RemovedDesktopUiModeError",
    "no longer supported",
    "QML is the only supported desktop UI.",
)


def _ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _terminate_process(proc: subprocess.Popen[str] | subprocess.Popen[bytes]) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def _build_env(local_appdata_root: Path, *, widgets_mode: bool) -> dict[str, str]:
    env = os.environ.copy()
    env["LOCALAPPDATA"] = str(local_appdata_root)
    if widgets_mode:
        env["AI_DAILY_DESKTOP_UI"] = "widgets"
    else:
        env.pop("AI_DAILY_DESKTOP_UI", None)
    return env


def _verify_default_qml(exe_path: Path, local_appdata_root: Path, timeout: float) -> None:
    desktop_root = local_appdata_root / DESKTOP_DATA_DIRNAME
    config_path = desktop_root / "config.yaml"
    env = _build_env(local_appdata_root, widgets_mode=False)
    proc = subprocess.Popen(
        [str(exe_path)],
        cwd=str(exe_path.parent),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            exit_code = proc.poll()
            if exit_code is not None:
                raise RuntimeError(
                    "Packaged default QML launch exited early "
                    f"(exitCode={exit_code}, configExists={config_path.is_file()})."
                )
            if config_path.is_file():
                time.sleep(1.0)
                if proc.poll() is None:
                    print(
                        "default-qml ok "
                        f"pid={proc.pid} localappdata={local_appdata_root} config={config_path}"
                    )
                    return
            time.sleep(0.5)
        raise RuntimeError(
            "Packaged default QML launch timed out "
            f"(configExists={config_path.is_file()}, localappdata={local_appdata_root})."
        )
    finally:
        _terminate_process(proc)


def _verify_widgets_removed(exe_path: Path, local_appdata_root: Path, timeout: float) -> None:
    env = _build_env(local_appdata_root, widgets_mode=True)
    stderr_chunks: list[str] = []
    stderr_path = local_appdata_root / "widgets-removed-stderr.txt"
    proc = subprocess.Popen(
        [str(exe_path)],
        cwd=str(exe_path.parent),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    def _reader() -> None:
        if proc.stderr is None:
            return
        for line in proc.stderr:
            stderr_chunks.append(line)

    reader = threading.Thread(target=_reader, daemon=True)
    reader.start()
    matched = False
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            stderr_text = "".join(stderr_chunks)
            if all(token in stderr_text for token in REMOVED_ERROR_TOKENS):
                matched = True
                break
            if proc.poll() is not None:
                time.sleep(0.5)
                stderr_text = "".join(stderr_chunks)
                if all(token in stderr_text for token in REMOVED_ERROR_TOKENS):
                    matched = True
                break
            time.sleep(0.5)
    finally:
        _terminate_process(proc)
        reader.join(timeout=5)
        if proc.stderr is not None:
            proc.stderr.close()

    stderr_text = "".join(stderr_chunks)
    stderr_path.write_text(stderr_text, encoding="utf-8")
    exit_code = proc.returncode if proc.poll() is not None else None
    if not matched:
        raise RuntimeError(
            "Packaged widgets-removed contract was not observed "
            f"(exitCode={exit_code}, stderrPath={stderr_path}, stderr={stderr_text!r})."
        )
    print(
        "widgets-removed ok "
        f"pid={proc.pid} exitCode={exit_code} localappdata={local_appdata_root} stderr={stderr_path}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check the packaged desktop runtime under an isolated LOCALAPPDATA root."
    )
    parser.add_argument(
        "--mode",
        choices=("default-qml", "widgets-removed"),
        required=True,
        help="Which packaged desktop contract to verify.",
    )
    parser.add_argument(
        "--exe",
        default=str(DEFAULT_EXE),
        help="Path to the packaged desktop executable.",
    )
    parser.add_argument(
        "--localappdata-root",
        required=True,
        help="Isolated LOCALAPPDATA root used for this verification run.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=45.0,
        help="Maximum number of seconds to wait for the verification to complete.",
    )
    args = parser.parse_args()

    exe_path = Path(args.exe).resolve()
    if not exe_path.is_file():
        raise SystemExit(f"Packaged desktop executable not found: {exe_path}")

    local_appdata_root = Path(args.localappdata_root).resolve()
    _ensure_clean_dir(local_appdata_root)

    if args.mode == "default-qml":
        _verify_default_qml(exe_path, local_appdata_root, args.timeout)
    else:
        _verify_widgets_removed(exe_path, local_appdata_root, args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
