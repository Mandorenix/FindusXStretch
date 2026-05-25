from __future__ import annotations

import sys
import zipfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: build_release_zip.py <source_dir> <zip_path>", file=sys.stderr)
        return 1

    source_dir = Path(sys.argv[1]).resolve()
    zip_path = Path(sys.argv[2]).resolve()

    if not source_dir.exists() or not source_dir.is_dir():
        print(f"Source directory not found: {source_dir}", file=sys.stderr)
        return 1

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source_dir.rglob("*")):
            if not path.is_file():
                continue
            archive.write(path, path.relative_to(source_dir).as_posix())

    print(zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
