"""Opening and cancelling the wizard must never start installation."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from dubua.ui import MainWindow  # noqa: E402


class StartupSafetyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_open_and_cancel_do_not_install(self):
        with patch("dubua.ui.install") as installer, patch("dubua.ui.ConfirmDialog.exec", return_value=QDialog.Rejected):
            window = MainWindow()
            self.app.processEvents()
            self.assertEqual(window.pages.currentIndex(), 0)
            window._confirm_start()
            self.assertEqual(window.pages.currentIndex(), 0)
            self.assertIsNone(window.worker)
            installer.assert_not_called()
            window.close()

    def test_last_steam_step_finishes_and_closes_window(self):
        window = MainWindow()
        self.assertFalse(window.windowIcon().isNull())
        window.pack = Path(r"C:\Users\Player\AppData\Local\DubTogether-UA\DubTogether-UA.pck")
        window._show_guide()
        window.show()
        QTest.qWait(320)
        self.assertEqual(window.next_step.text(), "Далі >")
        window.next_step.click()
        self.assertEqual(window.guide_step, 1)
        self.assertEqual(window.next_step.text(), "Готово")
        window.next_step.click()
        self.assertFalse(window.isVisible())


if __name__ == "__main__":
    unittest.main()
