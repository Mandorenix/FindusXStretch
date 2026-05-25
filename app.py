from __future__ import annotations

import sys


def main() -> int:
    try:
        from paulstretch_light.gui import run
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        print("Install dependencies with: pip install -r requirements.txt", file=sys.stderr)
        return 1
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
