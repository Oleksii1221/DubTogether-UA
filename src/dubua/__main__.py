"""Entry point. Opening the EXE only shows the welcome screen."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .installer import install


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline-test", nargs=2, metavar=("GAME_EXE", "OUTPUT_PACK"))
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--screenshot-guide", type=Path)
    args = parser.parse_args()
    if args.offline_test:
        game, output = map(Path, args.offline_test)
        result = install(game, output, close_running_game=False)
        print(result)
        return 0
    from .ui import run_app
    return run_app(args.screenshot or args.screenshot_guide, bool(args.screenshot_guide))


if __name__ == "__main__":
    sys.exit(main())
