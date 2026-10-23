"""Maintainer tool: make distributable delta files from an owned game install.

The resulting repository contains deltas and a new Ukrainian catalogue, not
the original game's compiled scripts or its PCK.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bsdiff4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dubua.pck import read_entry, verify_game  # noqa: E402


PATCH_TARGETS = {
    "autoload/Lang.gdc": "Lang.gdc",
    "autoload/Settings.gdc": "Settings.gdc",
    "autoload/UiTheme.gdc": "UiTheme.gdc",
    "scenes/screens/SettingsScreen.gdc": "SettingsScreen.gdc",
    "scenes/screens/RecordScreen.gdc": "RecordScreen.gdc",
}
ADDED = {
    "autoload/sprachen/uk.gdc": "uk.gdc",
    "autoload/sprachen/uk.gd.remap": "uk.gd.remap",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", required=True, type=Path)
    parser.add_argument("--compiled", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "src" / "dubua" / "assets")
    args = parser.parse_args()
    verify_game(args.game)
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {"patches": {}, "added": {}}
    for game_name, filename in PATCH_TARGETS.items():
        old = read_entry(args.game, game_name)
        new = (args.compiled / filename).read_bytes()
        patch = bsdiff4.diff(old, new)
        if bsdiff4.patch(old, patch) != new:
            raise RuntimeError(f"Patch roundtrip failed: {filename}")
        patch_file = filename + ".bsdiff"
        (args.output / patch_file).write_bytes(patch)
        manifest["patches"][game_name] = {
            "file": patch_file,
            "original_sha256": hashlib.sha256(old).hexdigest(),
            "result_sha256": hashlib.sha256(new).hexdigest(),
        }
        print(f"{game_name}: {len(old)} -> {len(new)}, delta {len(patch)} bytes")
    for game_name, filename in ADDED.items():
        data = (args.compiled / filename).read_bytes()
        (args.output / filename).write_bytes(data)
        manifest["added"][game_name] = {
            "file": filename,
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
