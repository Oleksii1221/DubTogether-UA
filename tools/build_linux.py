"""Build the Linux x86_64, no-console, one-file installer with PyInstaller."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src" / "dubua" / "assets"
NAME = "DubTogether-UA-Installer-Linux-x86_64"
REQUIRED = [
    "manifest.json", "uk.gdc", "Nunito.ttf", "Rubik.ttf", "LilitaOne.ttf",
    "OFL-Rubik.txt", "OFL-LilitaOne.txt", "app.png",
    "screenshots/steam-library-clean.png", "screenshots/steam-launch-options.png",
]


def main() -> None:
    if not sys.platform.startswith("linux"):
        raise SystemExit("The Linux installer must be built on Linux.")
    missing = [name for name in REQUIRED if not (ASSETS / name).is_file()]
    if missing:
        raise SystemExit("Missing installer assets: " + ", ".join(missing))
    subprocess.run([sys.executable, str(ROOT / "tools" / "audit_translations.py")], check=True)
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", NAME,
        "--paths", str(ROOT / "src"),
        "--add-data", f"{ASSETS}{os.pathsep}dubua/assets",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build" / "pyinstaller-linux"),
        "--specpath", str(ROOT / "build"),
        str(ROOT / "run_installer.py"),
    ], check=True, cwd=ROOT)
    output = ROOT / "dist" / NAME
    output.chmod(output.stat().st_mode | 0o111)
    print(output)


if __name__ == "__main__":
    main()
