"""Compatibility checks should follow patched entries, not the whole EXE."""

from __future__ import annotations

import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

import bsdiff4

from dubua.pck import PackError, build_pack, find_game_pack, read_index, verify_game


def _align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & ~(boundary - 1)


def make_pack(files: dict[str, bytes]) -> bytes:
    names = list(files)
    index_length = 100 + sum(4 + _align(len(name.encode()), 4) + 36 for name in names)
    base = _align(index_length, 16)
    offsets: dict[str, int] = {}
    cursor = 0
    for name in names:
        cursor = _align(cursor, 16)
        offsets[name] = cursor
        cursor += len(files[name])

    output = bytearray()
    output += b"GDPC"
    output += struct.pack("<5I", 2, 4, 4, 1, 2)
    output += struct.pack("<Q", base)
    output += bytes(64)
    output += struct.pack("<I", len(names))
    for name in names:
        encoded = name.encode()
        padded = encoded.ljust(_align(len(encoded), 4), b"\0")
        data = files[name]
        output += struct.pack("<I", len(padded)) + padded
        output += struct.pack("<QQ", offsets[name], len(data))
        output += hashlib.md5(data).digest()
        output += struct.pack("<I", 0)
    output += bytes(base - len(output))
    for name in names:
        absolute = base + offsets[name]
        output += bytes(absolute - len(output))
        output += files[name]
    return bytes(output)


class PackCompatibilityTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def write_game(self, marker: bytes, unrelated: bytes) -> Path:
        path = self.root / "DubTogether.exe"
        prefix = b"MZ" + bytes(257) + b"GDPC-not-a-pack" + bytes(19)
        path.write_bytes(prefix + make_pack({
            "autoload/Lang.gdc": marker,
            "unrelated/data.bin": unrelated,
        }))
        return path

    def test_unrelated_hotfix_does_not_break_compatibility(self):
        marker = b"compiled language script"
        expected = {"autoload/Lang.gdc": hashlib.sha256(marker).hexdigest()}
        first = self.write_game(marker, b"before hotfix")
        verify_game(first, expected)

        second = self.write_game(marker, b"after unrelated hotfix")
        layout = verify_game(second, expected)
        self.assertGreater(layout.start, 0)
        self.assertEqual(len(layout.entries), 2)

    def test_changed_patch_target_is_rejected(self):
        game = self.write_game(b"changed language script", b"other")
        with self.assertRaises(PackError):
            verify_game(game, {"autoload/Lang.gdc": hashlib.sha256(b"old").hexdigest()})

    def test_build_pack_uses_discovered_offset_and_checks_result(self):
        original = b"original script"
        modified = b"patched Ukrainian script"
        game = self.write_game(original, b"other")
        output = self.root / "DubTogether-UA.pck"
        name = "autoload/Lang.gdc"
        build_pack(
            game,
            output,
            {name: bsdiff4.diff(original, modified)},
            {"autoload/sprachen/uk.gdc": b"uk catalogue"},
            expected_originals={name: hashlib.sha256(original).hexdigest()},
            expected_results={name: hashlib.sha256(modified).hexdigest()},
        )

        with output.open("rb") as handle:
            base, _, entries = read_index(handle, 0, output.stat().st_size, 3)
            patched = next(entry for entry in entries if entry.name == name)
            handle.seek(base + patched.offset)
            self.assertEqual(handle.read(patched.size), modified)

    def test_pack_locator_ignores_false_magic(self):
        game = self.write_game(b"marker", b"other")
        with game.open("rb") as handle:
            layout = find_game_pack(handle)
        self.assertEqual(layout.entries[0].name, "autoload/Lang.gdc")


if __name__ == "__main__":
    unittest.main()
