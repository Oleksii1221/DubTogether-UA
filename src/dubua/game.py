"""Find the user's Steam installation and ask the game to close gracefully."""

from __future__ import annotations

import ctypes
import re
import time
import winreg
from pathlib import Path

import psutil

APP_ID = "5020310"
GAME_EXE = "DubTogether.exe"


def running_games() -> list[psutil.Process]:
    result = []
    for process in psutil.process_iter(["name", "exe"]):
        try:
            if (process.info["name"] or "").lower() == GAME_EXE.lower():
                result.append(process)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return result


def find_game_exe() -> Path | None:
    for process in running_games():
        try:
            path = Path(process.exe())
            if path.is_file():
                return path
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    roots: list[Path] = []
    for key_name in (r"Software\Valve\Steam", r"SOFTWARE\WOW6432Node\Valve\Steam"):
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hive, key_name) as key:
                    for value_name in ("SteamPath", "InstallPath"):
                        try:
                            roots.append(Path(winreg.QueryValueEx(key, value_name)[0]))
                        except OSError:
                            pass
            except OSError:
                pass
    roots += [Path(r"C:\Program Files (x86)\Steam"), Path(r"C:\Program Files\Steam")]
    libraries: list[Path] = []
    for root in dict.fromkeys(roots):
        if not root.is_dir():
            continue
        libraries.append(root)
        vdf = root / "steamapps" / "libraryfolders.vdf"
        if vdf.is_file():
            text = vdf.read_text(encoding="utf-8-sig", errors="replace")
            libraries += [Path(match.replace("\\\\", "\\")) for match in re.findall(r'"path"\s*"([^"]+)"', text)]
    for library in dict.fromkeys(libraries):
        manifest = library / "steamapps" / f"appmanifest_{APP_ID}.acf"
        if not manifest.is_file():
            continue
        text = manifest.read_text(encoding="utf-8-sig", errors="replace")
        match = re.search(r'"installdir"\s*"([^"]+)"', text)
        if match:
            candidate = library / "steamapps" / "common" / match.group(1) / GAME_EXE
            if candidate.is_file():
                return candidate
    return None


def close_game_gracefully(game_exe: Path, timeout: float = 20.0) -> None:
    """Send WM_CLOSE to matching game windows; never force-kill the process."""
    targets = []
    for process in running_games():
        try:
            if Path(process.exe()).resolve() == game_exe.resolve():
                targets.append(process)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    if not targets:
        return

    user32 = ctypes.windll.user32
    wnd_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    pids = {process.pid for process in targets}
    sent = set()

    def visit(hwnd, _):
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids and user32.IsWindowVisible(hwnd):
            user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
            sent.add(pid.value)
        return True

    callback = wnd_proc(visit)
    user32.EnumWindows(callback, 0)
    if sent != pids:
        raise RuntimeError("Не вдалося закрити вікно гри. Збережи прогрес і закрий її вручну.")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if all(not process.is_running() for process in targets):
            return
        time.sleep(0.25)
    raise RuntimeError("Гра ще працює. Закрий її вручну й натисни «Спробувати ще».")
