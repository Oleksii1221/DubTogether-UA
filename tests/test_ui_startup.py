"""Opening and cancelling the wizard must never start installation."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
