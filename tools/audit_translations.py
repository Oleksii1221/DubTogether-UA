"""Fail on missing or unchanged UI translations before a Windows build."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "translations" / "uk.json"
PLACEHOLDERS = re.compile(r"%(?:\d+\$)?[-+#0-9.]*[sdf]")
KNOWN_UNTRANSLATED_PROPER_NAMES = {"TWITCH", "DISCORD"}
REQUIRED_UI = {
    "NORMAL", "CHIPMUNK", "MONSTER", "AUTOTUNE", "LINE %d/%d",
    "▶ ORIGINAL", "▶ MEIN TAKE", "■ STOPP", "ABGEBEN", "WEITER ▶",
}


def audit() -> dict[str, str]:
    data = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    errors = []
    missing = REQUIRED_UI - data.keys()
    if missing:
        errors.append("Missing interface keys: " + ", ".join(sorted(missing)))
    for source, translated in data.items():
        if not translated.strip():
            errors.append(f"Empty translation: {source!r}")
        if source == translated and source not in KNOWN_UNTRANSLATED_PROPER_NAMES and re.search(r"[A-Za-z]", source):
            errors.append(f"Source text remained unchanged: {source!r}")
        if sorted(PLACEHOLDERS.findall(source)) != sorted(PLACEHOLDERS.findall(translated)):
            errors.append(f"Placeholder mismatch: {source!r} -> {translated!r}")
    if errors:
        raise ValueError("\n".join(errors))
    return data


if __name__ == "__main__":
    print(f"Перевірено {len(audit())} українських рядків; незмінених англійських рядків немає.")
