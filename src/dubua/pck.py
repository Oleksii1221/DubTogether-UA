"""Read the supported embedded Godot PCK and write a locally patched copy.

No game files are included in the repository or the installer. Unchanged entries
are copied from the player's own verified DubTogether.exe during installation.
"""

from __future__ import annotations

import hashlib
import os
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

import bsdiff4


GAME_SHA256 = "916ea61397884369e0431b8e393b03d1434d3054b56cf719d43664d1e0f3e72d"
PACK_START = 99_595_264
PACK_LENGTH = 18_524_932
EXPECTED_VERSION = (2, 4, 4, 1, 2)
EXPECTED_COUNT = 260
CHUNK = 1 << 20


class PackError(RuntimeError):
    """The owned game or patch assets differ from the supported build."""


@dataclass(frozen=True)
class Entry:
    name: str
    offset: int
    size: int
    md5: bytes
    flags: int


def _read_exact(handle, length: int) -> bytes:
    data = handle.read(length)
    if len(data) != length:
        raise PackError("Несподіваний кінець файлу гри.")
    return data


def _align16(value: int) -> int:
    return (value + 15) & ~15


def _align4(value: int) -> int:
    return (value + 3) & ~3


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_game(path: Path) -> None:
    if not path.is_file() or path.name.lower() != "dubtogether.exe":
        raise PackError("Файл DubTogether.exe не знайдено.")
    digest = sha256_file(path)
    if digest != GAME_SHA256:
        raise PackError(
            "Ця версія Dub Together поки не підтримується. "
            f"SHA-256: {digest}. Оригінальні файли не змінено."
        )


def read_index(
    handle, pack_start: int = PACK_START, pack_length: int = PACK_LENGTH,
    expected_count: int = EXPECTED_COUNT,
) -> tuple[int, bytes, list[Entry]]:
    handle.seek(pack_start)
    if _read_exact(handle, 4) != b"GDPC":
        raise PackError("У грі не знайдено очікуваний архів Godot.")
    version = struct.unpack("<5I", _read_exact(handle, 20))
    base_offset = struct.unpack("<Q", _read_exact(handle, 8))[0]
    reserved = _read_exact(handle, 64)
    count = struct.unpack("<I", _read_exact(handle, 4))[0]
    if version != EXPECTED_VERSION or count != expected_count:
        raise PackError("Формат або список файлів гри змінився.")
    if base_offset < 100 or base_offset > pack_length:
        raise PackError("Пошкоджений індекс гри.")
    entries: list[Entry] = []
    seen: set[str] = set()
    for _ in range(count):
        name_length = struct.unpack("<I", _read_exact(handle, 4))[0]
        if not 0 < name_length <= 4096:
            raise PackError("Пошкоджене ім’я файлу в архіві.")
        name = _read_exact(handle, name_length).rstrip(b"\0").decode("utf-8")
        offset, size = struct.unpack("<QQ", _read_exact(handle, 16))
        md5 = _read_exact(handle, 16)
        flags = struct.unpack("<I", _read_exact(handle, 4))[0]
        if name in seen or flags != 0 or base_offset + offset + size > pack_length:
            raise PackError("Непідтримуваний запис архіву гри.")
        seen.add(name)
        entries.append(Entry(name, offset, size, md5, flags))
    return base_offset, reserved, entries


def read_entry(game_exe: Path, name: str) -> bytes:
    """Read one original compiled script for local patch generation/testing."""
    with game_exe.open("rb") as handle:
        base, _, entries = read_index(handle)
        entry = next((item for item in entries if item.name == name), None)
        if entry is None:
            raise PackError(f"У грі немає {name}.")
        handle.seek(PACK_START + base + entry.offset)
        return _read_exact(handle, entry.size)


def _copy_exact(source, destination, size: int) -> None:
    while size:
        block = _read_exact(source, min(CHUNK, size))
        destination.write(block)
        size -= len(block)


def build_pack(
    game_exe: Path,
    output: Path,
    binary_patches: Mapping[str, bytes],
    added_files: Mapping[str, bytes],
    progress: Callable[[int, str], None] | None = None,
) -> Path:
    """Build the pack atomically, preserving all unmodified game entries."""
    verify_game(game_exe)
    if progress:
        progress(35, "Версію гри перевірено")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + ".tmp")
    try:
        with game_exe.open("rb") as source:
            base, reserved, originals = read_index(source)
            known = {entry.name for entry in originals}
            if set(binary_patches) - known or set(added_files) & known:
                raise PackError("Патч не відповідає списку файлів гри.")
            contents: dict[str, bytes] = {}
            for name, patch in binary_patches.items():
                original = next(entry for entry in originals if entry.name == name)
                source.seek(PACK_START + base + original.offset)
                contents[name] = bsdiff4.patch(_read_exact(source, original.size), patch)
            contents.update(added_files)
            all_names = [entry.name for entry in originals] + list(added_files)
            sizes = {entry.name: entry.size for entry in originals}
            sizes.update({name: len(data) for name, data in contents.items()})
            md5s = {entry.name: entry.md5 for entry in originals}
            md5s.update({name: hashlib.md5(data).digest() for name, data in contents.items()})

            index_length = 100 + sum(4 + _align4(len(name.encode("utf-8"))) + 36 for name in all_names)
            new_base = _align16(index_length)
            offsets: dict[str, int] = {}
            relative = 0
            for name in all_names:
                relative = _align16(relative)
                offsets[name] = relative
                relative += sizes[name]

            with temp.open("wb") as dest:
                dest.write(b"GDPC")
                dest.write(struct.pack("<5I", *EXPECTED_VERSION))
                dest.write(struct.pack("<Q", new_base))
                dest.write(reserved)
                dest.write(struct.pack("<I", len(all_names)))
                for name in all_names:
                    encoded = name.encode("utf-8")
                    padded = encoded.ljust(_align4(len(encoded)), b"\0")
                    dest.write(struct.pack("<I", len(padded)))
                    dest.write(padded)
                    dest.write(struct.pack("<QQ", offsets[name], sizes[name]))
                    dest.write(md5s[name])
                    dest.write(struct.pack("<I", 0))
                dest.write(b"\0" * (new_base - dest.tell()))
                total = len(all_names)
                for number, name in enumerate(all_names, 1):
                    absolute = new_base + offsets[name]
                    dest.write(b"\0" * (absolute - dest.tell()))
                    if name in contents:
                        dest.write(contents[name])
                    else:
                        original = next(entry for entry in originals if entry.name == name)
                        source.seek(PACK_START + base + original.offset)
                        _copy_exact(source, dest, original.size)
                    if progress and (number % 30 == 0 or number == total):
                        progress(40 + int(50 * number / total), f"Створюємо пак: {number}/{total} файлів")
        with temp.open("rb") as check:
            _, _, result_entries = read_index(check, 0, temp.stat().st_size, total)
            if len(result_entries) != total or temp.stat().st_size < 1_000_000:
                raise PackError("Перевірка створеного пака не пройдена.")
        os.replace(temp, output)
        if progress:
            progress(100, "Український пак готовий")
        return output
    finally:
        temp.unlink(missing_ok=True)
