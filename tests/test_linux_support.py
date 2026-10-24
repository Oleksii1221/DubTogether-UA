"""Linux and Steam Proton integration tests."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dubua import game
from dubua.installer import launch_option, output_path


class SteamDiscoveryTest(unittest.TestCase):
    def test_finds_windows_game_in_linux_steam_library(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            steamapps = root / "steamapps"
            game_exe = steamapps / "common" / "Dub Together" / "DubTogether.exe"
            game_exe.parent.mkdir(parents=True)
            game_exe.write_bytes(b"test")
            (steamapps / f"appmanifest_{game.APP_ID}.acf").write_text(
                '"AppState"\n{\n\t"installdir"\t\t"Dub Together"\n}', encoding="utf-8"
            )
            with patch("dubua.game.running_games", return_value=[]), patch(
                "dubua.game.steam_roots", return_value=[root]
            ):
                self.assertEqual(game.find_game_exe(), game_exe)

    def test_linux_stop_request_never_calls_kill(self):
        class Process:
            terminated = False

            def terminate(self):
                self.terminated = True

            def kill(self):
                raise AssertionError("Linux installer must never force-kill the game")

        process = Process()
        game._close_linux_game([process])
        self.assertTrue(process.terminated)


@unittest.skipUnless(sys.platform.startswith("linux"), "Linux path semantics")
class LinuxPathTest(unittest.TestCase):
    def test_output_path_uses_xdg_data_home(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            os.environ, {"XDG_DATA_HOME": folder}
        ):
            self.assertEqual(output_path(), Path(folder) / "DubTogether-UA" / "DubTogether-UA.pck")

    def test_launch_option_uses_proton_z_drive(self):
        pack = Path("/home/player/My Packs/DubTogether-UA.pck")
        self.assertEqual(
            launch_option(pack),
            '--main-pack "Z:\\home\\player\\My Packs\\DubTogether-UA.pck"',
        )


if __name__ == "__main__":
    unittest.main()
