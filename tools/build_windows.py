"""Build the Windows no-console, one-file installer with PyInstaller."""

from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src" / "dubua" / "assets"
REQUIRED = ["manifest.json", "uk.gdc", "Nunito.ttf", "app.png", "app.ico",
            "screenshots/steam-library-clean.png"]


def main() -> None:
    missing = [name for name in REQUIRED if not (ASSETS / name).is_file()]
    if missing:
        raise SystemExit("Missing installer assets: " + ", ".join(missing))
    subprocess.run([sys.executable, str(ROOT / "tools" / "audit_translations.py")], check=True)
    # CI and developer PATH entries may contain unrelated CRT and ICU DLLs.
    # PyInstaller scans PATH for dependencies, so give it only Python and
    # Windows directories. Qt DLLs are discovered from the PySide6 package.
    build_env = os.environ.copy()
    windows = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    build_env["PATH"] = os.pathsep.join(dict.fromkeys(map(str, (
        Path(sys.executable).parent,
        Path(sys.base_prefix),
        windows / "System32",
        windows,
    ))))
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", "DubTogether-UA-Installer",
        "--icon", str(ASSETS / "app.ico"),
        "--paths", str(ROOT / "src"),
        "--add-data", f"{ASSETS};dubua/assets",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build" / "pyinstaller"),
        "--specpath", str(ROOT / "build"),
        str(ROOT / "run_installer.py"),
    ], check=True, cwd=ROOT, env=build_env)
    print(ROOT / "dist" / "DubTogether-UA-Installer.exe")


if __name__ == "__main__":
    main()
