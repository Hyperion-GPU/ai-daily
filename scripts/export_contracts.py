import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.contracts import check_artifacts, write_artifacts


def main() -> int:
    if "--check" in sys.argv:
        stale = check_artifacts(REPO_ROOT)
        if stale:
            print("Contract artifacts are stale:", file=sys.stderr)
            for path in stale:
                print(f" - {path.relative_to(REPO_ROOT)}", file=sys.stderr)
            return 1
        print("Contract artifacts are up to date.")
        return 0

    written = write_artifacts(REPO_ROOT)
    print("Updated contract artifacts:")
    for path in written:
        print(f" - {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
