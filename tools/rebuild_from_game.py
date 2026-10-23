"""Regenerate localization delta assets from an owned game and GDRETools.

Use this only as a maintainer tool. It reads but never modifies DubTogether.exe.
Only the small patch files and our Ukrainian catalogue are kept after the
temporary workspace is deleted.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dubua.pck import read_entry, verify_game  # noqa: E402


MODIFICATIONS = {
    "Lang": ("autoload/Lang.gdc", [
        ('\t"ru": preload("res://autoload/sprachen/ru.gd"), ',
         '\t"ru": preload("res://autoload/sprachen/ru.gd"), \n\t"uk": preload("res://autoload/sprachen/uk.gd"), '),
    ]),
    "Settings": ("autoload/Settings.gdc", [
        ('"russian": "ru", "english": "en", ', '"russian": "ru", "ukrainian": "uk", "english": "en", '),
        ('"ru": "ru", "en": "en", ', '"ru": "ru", "uk": "uk", "en": "en", '),
    ]),
    "SettingsScreen": ("scenes/screens/SettingsScreen.gdc", [
        ('const _LANGS: = ["de", "en", "es", "fr", "pt_BR", "it", "ru"]',
         'const _LANGS: = ["de", "en", "es", "fr", "pt_BR", "it", "ru", "uk"]'),
        ('const _LANG_NAMES: = ["Deutsch", "English", "Español", "Français", "Português (BR)", "Italiano", "Русский"]',
         'const _LANG_NAMES: = ["Deutsch", "English", "Español", "Français", "Português (BR)", "Italiano", "Русский", "Українська"]'),
    ]),
    "RecordScreen": ("scenes/screens/RecordScreen.gdc", [
        ('progress_label = UiTheme.make_title("LINE 1/9", 30, UiTheme.INK)',
         'progress_label = UiTheme.make_title(tr("LINE %d/%d") % [1, 9], 30, UiTheme.INK)'),
        ('progress_label.text = "LINE %d/%d" % [p + 1, n]',
         'progress_label.text = tr("LINE %d/%d") % [p + 1, n]'),
        ('orig_btn = UiTheme.make_button("▶ ORIGINAL", "yellow", 20)',
         'orig_btn = UiTheme.make_button(tr("▶ ORIGINAL"), "yellow", 20)'),
        ('orig_btn.text = "■ STOPP" if mode == "orig" else "▶ ORIGINAL"',
         'orig_btn.text = tr("■ STOPP") if mode == "orig" else tr("▶ ORIGINAL")'),
        ('listen_btn = UiTheme.make_button("▶ MEIN TAKE", "white", 20)',
         'listen_btn = UiTheme.make_button(tr("▶ MEIN TAKE"), "white", 20)'),
        ('listen_btn.text = "■ STOPP" if mode == "take" else "▶ MEIN TAKE"',
         'listen_btn.text = tr("■ STOPP") if mode == "take" else tr("▶ MEIN TAKE")'),
        ('beenden_btn = UiTheme.make_button("RUNDE BEENDEN", "ghost", 19)',
         'beenden_btn = UiTheme.make_button(tr("RUNDE BEENDEN"), "ghost", 19)'),
        ('next_btn.text = "ABGEBEN" if last else "WEITER ▶"',
         'next_btn.text = tr("ABGEBEN") if last else tr("WEITER ▶")'),
    ]),
    "UiTheme": ("autoload/UiTheme.gdc", [
        ("\tb.text = text\n", "\tb.text = tr(text)\n"),
        ("\tl.text = text\n", "\tl.text = tr(text)\n"),
    ]),
}


def gdre_run(executable: Path, args: list[str]) -> None:
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    result = subprocess.run([str(executable), "--headless", *args],
                            text=True, encoding="utf-8", errors="replace",
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            creationflags=flags, timeout=120, check=False)
    if result.returncode or "complete" not in result.stdout.lower():
        raise RuntimeError(f"GDRETools failed ({result.returncode}):\n{result.stdout[-3000:]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--gdre", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "src" / "dubua" / "assets")
    args = parser.parse_args()
    verify_game(args.game)
    if not args.gdre.is_file():
        raise SystemExit("GDRETools executable not found")
    with tempfile.TemporaryDirectory(prefix="dubua-rebuild-") as temporary:
        workspace = Path(temporary)
        originals = workspace / "original"
        source = workspace / "source"
        compiled = workspace / "compiled"
        for folder in (originals, source, compiled):
            folder.mkdir()
        for name, (game_name, replacements) in MODIFICATIONS.items():
            original = originals / f"{name}.gdc"
            original.write_bytes(read_entry(args.game, game_name))
            gdre_run(args.gdre, [f"--decompile={original}", "--bytecode=4.3.0", f"--output-dir={source}"])
            source_file = source / f"{name}.gd"
            text = source_file.read_text(encoding="utf-8")
            for before, after in replacements:
                occurrences = text.count(before)
                if occurrences != 1:
                    raise RuntimeError(f"{name}: expected one occurrence, got {occurrences}: {before!r}")
                text = text.replace(before, after)
            source_file.write_text(text, encoding="utf-8")
            gdre_run(args.gdre, [f"--compile={source_file}", "--bytecode=4.3.0", f"--output-dir={compiled}"])
        subprocess.run([sys.executable, str(ROOT / "tools" / "catalogue_to_gd.py"),
                        str(source / "uk.gd")], check=True)
        gdre_run(args.gdre, [f"--compile={source / 'uk.gd'}", "--bytecode=4.3.0", f"--output-dir={compiled}"])
        (compiled / "uk.gd.remap").write_text('[remap]\n\npath="res://autoload/sprachen/uk.gdc"\n', encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "tools" / "build_patches.py"),
                        "--game", str(args.game), "--compiled", str(compiled),
                        "--output", str(args.output)], check=True)


if __name__ == "__main__":
    main()
