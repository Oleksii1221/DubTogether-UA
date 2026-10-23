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
    # Image/PDF tools in developer runtimes carry unrelated ICU and CRT DLLs.
    # Keep those directories out of PyInstaller's dependency scan.
    build_env = os.environ.copy()
    build_env["PATH"] = os.pathsep.join(
        part for part in build_env.get("PATH", "").split(os.pathsep)
        if "poppler" not in part.casefold()
        and not ("codex-primary-runtime" in part.casefold()
                 and "dependencies\\native" in part.casefold())
    )
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
