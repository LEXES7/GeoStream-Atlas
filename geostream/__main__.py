"""CLI entrypoint: python -m geostream"""

from __future__ import annotations

import os
import sys

from .pipeline import run


def main() -> int:
    try:
        manifest = run()
    except Exception as err:
        print(f"collection failed: {err}", file=sys.stderr)
        return 1

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as fh:
            fh.write(f"date={manifest.date}\n")
            fh.write(f"cities_ok={manifest.cities_ok}\n")
            fh.write(f"nino_ok={manifest.nino_ok}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
