"""Find Dub Together in Steam and ask the game to close gracefully."""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

import psutil

if sys.platform == "win32":
    import ctypes
    import winreg


APP_ID = "5020310"
GAME_EXE = "DubTogether.exe"
IS_WINDOWS = sys.platform == "win32"


def running_games() -> list[psutil.Process]:
    result = []
    for process in psutil.process_iter(["name", "exe"]):
        try:
            name = process.info["name"] or ""
            executable = Path(process.info["exe"] or "").name
            if GAME_EXE.casefold() in {name.casefold(), executable.casefold()}:
                result.append(process)
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
            continue
    return result


def _windows_steam_roots() -> list[Path]:
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
    return roots


def _linux_steam_roots() -> list[Path]:
    home = Path.home()
    roots = [
        home / ".steam" / "steam",
        home / ".steam" / "root",
        home / ".local" / "share" / "Steam",
        home / ".var" / "app" / "com.valvesoftware.Steam" / ".local" / "share" / "Steam",
        home / ".var" / "app" / "com.valvesoftware.Steam" / "data" / "Steam",
    ]
    for name in ("STEAM_DIR", "STEAM_ROOT"):
        value = os.environ.get(name)
        if value:
            roots.insert(0, Path(value).expanduser())
    return roots


def steam_roots() -> list[Path]:
    if IS_WINDOWS:
        return _windows_steam_roots()
    if sys.platform.startswith("linux"):
        return _linux_steam_roots()
    return []


def _libraries(root: Path) -> list[Path]:
    libraries = [root]
    vdf = root / "steamapps" / "libraryfolders.vdf"
    if not vdf.is_file():
        return libraries
    text = vdf.read_text(encoding="utf-8-sig", errors="replace")
    for match in re.findall(r'"path"\s*"([^"]+)"', text):
        # Valve escapes backslashes in VDF; Linux paths otherwise remain unchanged.
        libraries.append(Path(match.replace("\\\\", "\\")))
    return libraries


def find_game_exe() -> Path | None:
    for process in running_games():
        try:
            path = Path(process.exe())
            # Wine/Proton can report its loader as process.exe(); use Steam metadata instead.
            if path.is_file() and (IS_WINDOWS or path.name.casefold() == GAME_EXE.casefold()):
                return path
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
            continue

    libraries: list[Path] = []
    for root in dict.fromkeys(steam_roots()):
        if root.is_dir():
            libraries.extend(_libraries(root))
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


def _wait_until_closed(targets: list[psutil.Process], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if all(not process.is_running() for process in targets):
            return
        time.sleep(0.25)
    raise RuntimeError("Гра ще працює. Закрий її вручну й натисни «Спробувати ще».")


def _close_windows_game(targets: list[psutil.Process]) -> None:
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


def _close_linux_game(targets: list[psutil.Process]) -> None:
    # SIGTERM is the conventional graceful-stop request on Linux. Never follow it with SIGKILL.
    try:
        for process in targets:
            process.terminate()
    except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
        raise RuntimeError("Не вдалося попросити гру завершитися. Закрий її вручну.") from exc


def close_game_gracefully(game_exe: Path, timeout: float = 20.0) -> None:
    """Request a graceful exit from the matching game process; never force-kill it."""
    targets = []
    for process in running_games():
        try:
            same_executable = Path(process.exe()).resolve() == game_exe.resolve()
            linux_game_name = (
                sys.platform.startswith("linux")
                and process.name().casefold() == GAME_EXE.casefold()
            )
            if same_executable or linux_game_name:
                targets.append(process)
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
            continue
    if not targets:
        return

    if IS_WINDOWS:
        _close_windows_game(targets)
    elif sys.platform.startswith("linux"):
        _close_linux_game(targets)
    else:
        raise RuntimeError("Автоматичне закриття гри на цій системі не підтримується.")
    _wait_until_closed(targets, timeout)
