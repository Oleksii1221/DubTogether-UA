"""Installer orchestration. This module never closes a game on import."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Callable

from .game import close_game_gracefully, find_game_exe
from .pck import PackError, build_pack, verify_game

ASSETS = Path(__file__).resolve().parent / "assets"
PACK_NAME = "DubTogether-UA.pck"


def output_path() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise PackError("Windows не надав шлях LOCALAPPDATA.")
    return Path(local) / "DubTogether-UA" / PACK_NAME


def launch_option(pack: Path) -> str:
    return f'--main-pack "{pack}"'


def load_assets() -> tuple[
    dict[str, bytes], dict[str, bytes], dict[str, str], dict[str, str],
]:
    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    patches = {name: (ASSETS / item["file"]).read_bytes()
               for name, item in manifest["patches"].items()}
    added = {name: (ASSETS / item["file"]).read_bytes()
             for name, item in manifest["added"].items()}
    originals = {name: item["original_sha256"]
                 for name, item in manifest["patches"].items()}
    results = {name: item["result_sha256"]
               for name, item in manifest["patches"].items()}
    for name, data in added.items():
        if hashlib.sha256(data).hexdigest() != manifest["added"][name]["sha256"]:
            raise PackError("Файли інсталятора пошкоджено. Завантажте його ще раз.")
    return patches, added, originals, results


def install(
    game_exe: Path | None = None,
    destination: Path | None = None,
    *,
    close_running_game: bool = True,
    progress: Callable[[int, str], None] | None = None,
) -> Path:
    """Install only when explicitly called after the UI confirmation."""
    game = game_exe or find_game_exe()
    if game is None:
        raise PackError("Dub Together не знайдено у бібліотеках Steam.")
    if progress:
        progress(8, "Перевіряємо версію гри")
    patches, added, originals, results = load_assets()
    verify_game(game, originals)
    if close_running_game:
        if progress:
            progress(20, "Закриваємо Dub Together")
        close_game_gracefully(game)
    if progress:
        progress(30, "Готуємо українські файли")
    return build_pack(
        game, destination or output_path(), patches, added, progress,
        expected_originals=originals, expected_results=results,
    )
