"""Generate our Ukrainian GDScript catalogue from editable JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_translations import audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    catalogue = audit()
    lines = ["extends Node", "", "const T = {", ""]
    for source, translated in catalogue.items():
        lines.append(f"\t{json.dumps(source, ensure_ascii=False)}: {json.dumps(translated, ensure_ascii=False)},")
    lines += ["}", ""]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(catalogue)} translations to {args.output}")


if __name__ == "__main__":
    main()
