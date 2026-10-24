"""A small, game-inspired Windows wizard built with PySide6."""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QEventLoop, QPropertyAnimation, QRectF, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QFontDatabase, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QDialog, QFrame, QGraphicsOpacityEffect, QHBoxLayout,
    QLabel, QMainWindow, QProgressBar, QPushButton, QSizePolicy, QStackedWidget,
    QTextEdit, QVBoxLayout, QWidget,
)

from . import __author__, __version__
from .font_rendering import GrayscaleTextStyle
from .game import running_games
from .installer import ASSETS, install, launch_option, output_path

GITHUB = "https://github.com/Oleksii1221/DubTogether-UA"
STEAM = "https://steamcommunity.com/profiles/76561199256076885"
SITE_ASSETS = ASSETS / "screenshots"

STYLESHEET = """
QWidget { background: #0e1328; color: #f9f6ff; font-family: 'Nunito', 'Segoe UI'; font-size: 15px; }
QFrame#windowRoot { background: #0e1328; border: 1px solid #080b1b; }
QFrame#titleBar { background: #0a0f22; border: none; border-bottom: 1px solid #2f274e; }
QFrame#titleBar QLabel { background: transparent; }
QLabel#windowTitle { color: #eee9f7; font-size: 12px; }
QPushButton#windowControl, QPushButton#windowClose {
    background: transparent; color: #b8afd0; border: none; border-radius: 0;
    padding: 0; min-height: 0; font-family: 'Segoe UI'; font-size: 17px; font-weight: 400;
}
QPushButton#windowControl:hover { background: #2b2448; color: #fffaf0; }
QPushButton#windowClose:hover { background: #e85d68; color: #ffffff; }
QFrame#card { background: #18142f; border: 2px solid #080b1b; border-radius: 25px; }
QFrame#inner { background: #241e3c; border: 1px solid #51416b; border-radius: 17px; }
QLabel#brand { font-family: 'Lilita One'; font-size: 25px; font-weight: 400; color: #fff9ed; }
QLabel#heading { font-family: 'Rubik'; font-size: 43px; font-weight: 900; color: #fffaf0; }
QLabel#pageTitle { font-family: 'Rubik'; font-size: 30px; font-weight: 900; color: #fffaf0; }
QLabel#subhead { font-family: 'Rubik'; font-size: 19px; font-weight: 800; color: #fffaf0; }
QLabel#kicker { color: #23c8ac; font-size: 13px; font-weight: 900; letter-spacing: 1px; }
QLabel#muted { color: #b8afd0; }
QLabel#step { color: #9187b0; font-weight: 800; font-size: 12px; }
QLabel#activeStep { color: #ffe17b; font-weight: 900; font-size: 12px; }
QLabel#footer { color: #c4b6e1; font-size: 15px; font-weight: 800; }
QPushButton { padding: 10px 20px; border-radius: 17px; border: 2px solid #080b1b; font-weight: 900; min-height: 23px; }
QPushButton#primary { background: #ffca3b; color: #251e28; }
QPushButton#primary:hover { background: #ffdc6a; }
QPushButton#primary:pressed { background: #f2b924; }
QPushButton#secondary { background: #3b2f58; color: #f9f5ff; }
QPushButton#secondary:hover { background: #554170; }
QPushButton#danger { background: #f47771; color: #281d2c; }
QPushButton#danger:hover { background: #ff9288; }
QPushButton#link { border: none; color: #c4b6e1; background: transparent; text-decoration: underline; padding: 3px; }
QPushButton#link:hover { color: #fff1a0; }
QPushButton:disabled { background: #554b68; color: #aca5b7; }
QLabel#launchOption { background: #0d1022; color: #f9f7ff; border: 1px solid #5e5277; border-radius: 11px; padding: 10px 12px; min-height: 23px; }
QTextEdit { background: #111328; color: #bcb5d3; border: 1px solid #453a62; border-radius: 12px; padding: 10px; }
QProgressBar { background: #0b0d1d; border: 2px solid #4b3e65; border-radius: 10px; text-align: center; min-height: 16px; color: #fff; font-weight: 800; }
QProgressBar::chunk { background: #20bba7; border-radius: 8px; }
QDialog { background: #18142f; }
"""


def label(text: str, role: str | None = None, wrap: bool = True) -> QLabel:
    item = QLabel(text)
    if role:
        item.setObjectName(role)
    item.setWordWrap(wrap)
    return item


def button(text: str, role: str, callback=None) -> QPushButton:
    item = QPushButton(text)
    item.setObjectName(role)
    item.setCursor(Qt.PointingHandCursor)
    if callback:
        item.clicked.connect(callback)
    return item


class TitleBar(QFrame):
    """Theme-owned title bar so Windows light mode cannot recolor the app."""

    def __init__(self, owner: QWidget, title: str, show_minimize: bool = True):
        super().__init__(owner)
        self.owner = owner
        self._drag_offset = None
        self.setObjectName("titleBar")
        self.setFixedHeight(34)

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 0, 0, 0)
        row.setSpacing(8)

        icon = QLabel()
        icon.setPixmap(QPixmap(str(ASSETS / "app.png")).scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon.setFixedSize(18, 18)
        row.addWidget(icon)

        caption = label(title, "windowTitle", False)
        row.addWidget(caption)
        row.addStretch()

        if show_minimize:
            minimize = QPushButton("−")
            minimize.setObjectName("windowControl")
            minimize.setAccessibleName("Згорнути")
            minimize.setFixedSize(44, 33)
            minimize.setCursor(Qt.PointingHandCursor)
            minimize.clicked.connect(owner.showMinimized)
            row.addWidget(minimize)

        close = QPushButton("×")
        close.setObjectName("windowClose")
        close.setAccessibleName("Закрити")
        close.setFixedSize(46, 33)
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(owner.close)
        row.addWidget(close)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.owner.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.owner.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        event.accept()


class Flag(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(35, 24)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#2479ba"))
        painter.drawRoundedRect(QRectF(1, 1, 33, 22), 5, 5)
        painter.setBrush(QColor("#ffd34d"))
        painter.drawRect(QRectF(1, 12, 33, 11))


class Waveform(QWidget):
    """Animated voice-wave and microphone art shared with the website."""

    def __init__(self):
        super().__init__()
        self.phase = 0.0
        self.setMinimumSize(280, 220)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(42)

    def tick(self):
        self.phase += 0.055
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        diameter = min(w * .88, h * .86)
        inner = diameter * .67
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#30264f"))
        p.drawEllipse(QRectF((w - diameter) / 2, (h - diameter) / 2, diameter, diameter))
        p.setBrush(QColor("#463468"))
        p.drawEllipse(QRectF((w - inner) / 2, (h - inner) / 2, inner, inner))
        for color, scale, phase in (("#6f61aa", 1.0, 0), ("#20bca8", .70, 1.0)):
            path = QPainterPath()
            for x in range(0, w + 2, 2):
                envelope = math.sin(math.pi * x / max(1, w)) ** 2
                wave = math.sin(x * .065 - self.phase + phase) * math.sin(x * .023 + self.phase) * 42 * scale * envelope
                y = h * .5 + wave
                if x == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            p.setPen(QPen(QColor(color), 5 if scale == .70 else 3, Qt.SolidLine, Qt.RoundCap))
            p.drawPath(path)

        # Match the CSS microphone on the website, including its slight sway.
        mic_scale = diameter / 360
        p.save()
        p.translate(w * .52, h * .5)
        p.rotate(-9 + math.sin(self.phase * .55) * 2)
        p.scale(mic_scale, mic_scale)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#0b0d1d"))
        p.drawRoundedRect(QRectF(-42, -85, 100, 127), 50, 50)
        p.drawRoundedRect(QRectF(1, 28, 14, 62), 7, 7)
        p.drawRoundedRect(QRectF(-37, 86, 90, 14), 7, 7)

        head_gradient = QLinearGradient(-50, -95, 50, 32)
        head_gradient.setColorAt(0, QColor("#51486d"))
        head_gradient.setColorAt(1, QColor("#28243f"))
        p.setBrush(head_gradient)
        p.setPen(QPen(QColor("#111322"), 7))
        p.drawRoundedRect(QRectF(-50, -95, 100, 127), 50, 50)
        p.setPen(QPen(QColor("#a69bc8"), 4))
        p.drawLine(-22, -70, -22, 8)
        p.drawLine(22, -70, 22, 8)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1a1b2e"))
        p.drawRoundedRect(QRectF(-7, 20, 14, 64), 7, 7)
        p.setBrush(QColor("#17192b"))
        p.drawRoundedRect(QRectF(-45, 78, 90, 14), 7, 7)
        p.restore()

        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffce41"))
        p.drawEllipse(QRectF(w * .13, h * .29, 24, 24))
        p.setBrush(QColor("#fff8d9"))
        p.drawEllipse(QRectF(w * .13 + 7, h * .29 + 7, 10, 10))


class InstallThread(QThread):
    stage = Signal(int, str)
    installed = Signal(str)
    failed = Signal(str)

    def run(self):
        try:
            result = install(progress=lambda percent, text: self.stage.emit(percent, text))
            self.installed.emit(str(result))
        except Exception as exc:
            self.failed.emit(str(exc))


class ConfirmDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle("Підтвердження")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setFixedWidth(520)
        shell = QVBoxLayout(self)
        shell.setContentsMargins(1, 1, 1, 1)
        shell.setSpacing(0)
        shell.addWidget(TitleBar(self, "Підтвердження", show_minimize=False))
        content = QWidget()
        shell.addWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(30, 25, 30, 26)
        root.setSpacing(19)
        root.addWidget(label("ПЕРЕД ВСТАНОВЛЕННЯМ", "kicker"))
        root.addWidget(label("Dub Together буде закрито", "pageTitle"))
        root.addWidget(label("Збережи прогрес у грі. Після підтвердження програма закриє її вікно й створить український пак. Відповідь «Назад» залишить гру відкритою.", "muted"))
        if not running_games():
            root.addWidget(label("Зараз гра не запущена. Інсталятор продовжить без закриття вікна.", "kicker"))
        row = QHBoxLayout()
        cancel = button("Назад", "secondary", self.reject)
        proceed = button("Закрити гру та встановити", "danger", self.accept)
        cancel.setDefault(True)
        row.addWidget(cancel)
        row.addWidget(proceed)
        root.addLayout(row)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dub Together UA — український переклад")
        self.setWindowIcon(QIcon(str(ASSETS / "app.png")))
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setFixedSize(970, 772)
        self.setStyleSheet(STYLESHEET)
        self.pack: Path | None = None
        self.worker: InstallThread | None = None
        self.guide_step = 0
        self.animation = None
        outer = QFrame()
        outer.setObjectName("windowRoot")
        self.setCentralWidget(outer)
        shell = QVBoxLayout(outer)
        shell.setContentsMargins(1, 1, 1, 1)
        shell.setSpacing(0)
        shell.addWidget(TitleBar(self, self.windowTitle()))

        content = QWidget()
        shell.addWidget(content, 1)
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 23, 28, 19)
        root.setSpacing(17)

        header = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QPixmap(str(ASSETS / "app.png")).scaled(38, 38, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAccessibleName("Логотип Dub Together UA")
        header.addWidget(logo)
        header.addWidget(label("DUB  TOGETHER  /  UA", "brand", False))
        header.addStretch()
        flag = Flag()
        header.addWidget(flag)
        header.addWidget(label("Грайте українською", "muted", False))
        root.addLayout(header)

        steps = QHBoxLayout()
        self.step_labels = []
        for i, title in enumerate(("01  ВІТАННЯ", "02  ВСТАНОВЛЕННЯ", "03  STEAM")):
            item = label(title, "activeStep" if i == 0 else "step", False)
            self.step_labels.append(item)
            steps.addWidget(item)
            if i < 2:
                line = QFrame()
                line.setFixedHeight(2)
                line.setStyleSheet("background: #4b4365; border: none;")
                steps.addWidget(line, 1)
        root.addLayout(steps)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 27, 35, 26)
        self.pages = QStackedWidget()
        card_layout.addWidget(self.pages)
        root.addWidget(card, 1)
        self._make_welcome()
        self._make_progress()
        self._make_guide()

        footer = QHBoxLayout()
        footer.setSpacing(16)
        footer.addWidget(label(f"v{__version__}   ·   {__author__}", "footer", False))
        footer.addStretch()
        footer.addWidget(button("Steam", "link", lambda: QDesktopServices.openUrl(QUrl(STEAM))))
        footer.addWidget(button("GitHub", "link", lambda: QDesktopServices.openUrl(QUrl(GITHUB))))
        root.addLayout(footer)

    def _make_welcome(self):
        page = QWidget()
        row = QHBoxLayout(page)
        row.setSpacing(14)
        left = QVBoxLayout()
        left.setSpacing(14)
        left.addStretch(1)
        left.addWidget(label("УКРАЇНСЬКИЙ ПЕРЕКЛАД  ·  WINDOWS", "kicker"))
        left.addWidget(label("Грайте\nукраїнською", "heading"))
        left.addWidget(label("Переклад меню, підказок і реплік інтерфейсу Dub Together. Встановлення займає кілька кроків — ми покажемо кожен із них.", "muted"))
        left.addSpacing(10)
        actions = QHBoxLayout()
        actions.addWidget(button("Почати встановлення  >", "primary", self._confirm_start))
        actions.addStretch()
        left.addLayout(actions)
        try:
            existing = output_path()
            if existing.is_file() and existing.stat().st_size > 1_000_000:
                self.pack = existing
                left.addWidget(button("Пак уже є · перейти до інструкції", "link", self._open_existing))
        except OSError:
            pass
        left.addStretch(1)
        row.addLayout(left, 6)
        row.addWidget(Waveform(), 5)
        self.pages.addWidget(page)

    def _make_progress(self):
        page = QWidget()
        body = QVBoxLayout(page)
        body.setSpacing(17)
        body.addWidget(label("КРОК 02  /  ВСТАНОВЛЕННЯ", "kicker"))
        body.addWidget(label("Створюємо український пак", "pageTitle"))
        body.addWidget(label("Гра закриється після твого підтвердження. Оригінальні файли залишаться на місці.", "muted"))
        body.addSpacing(16)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        body.addWidget(self.progress)
        self.stage = label("Очікуємо початку…", "subhead")
        body.addWidget(self.stage)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(160)
        body.addWidget(self.log)
        body.addStretch()
        self.retry = button("Спробувати ще", "secondary", self._return_to_welcome)
        self.retry.hide()
        body.addWidget(self.retry, 0, Qt.AlignLeft)
        self.pages.addWidget(page)

    def _make_guide(self):
        page = QWidget()
        body = QVBoxLayout(page)
        body.setSpacing(11)
        body.addWidget(label("КРОК 03  /  STEAM", "kicker"))
        body.addWidget(label("Пак готовий. Залишився один рядок.", "pageTitle"))
        body.addWidget(label("Скопіюй весь параметр і встав його в Steam > Dub Together > Властивості > Загальні > Параметри запуску.", "muted"))
        option_row = QHBoxLayout()
        self.option = label("", "launchOption", False)
        self.option.setAccessibleName("Параметр запуску Steam")
        self.option.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        option_row.addWidget(self.option, 1)
        option_row.addWidget(button("Копіювати", "primary", self._copy_option))
        body.addLayout(option_row)

        visual = QFrame()
        visual.setObjectName("inner")
        visual_layout = QVBoxLayout(visual)
        visual_layout.setContentsMargins(14, 12, 14, 12)
        self.guide_title = label("", "subhead")
        visual_layout.addWidget(self.guide_title)
        self.guide_image = QLabel()
        self.guide_image.setAlignment(Qt.AlignCenter)
        self.guide_image.setFixedHeight(180)
        visual_layout.addWidget(self.guide_image)
        body.addWidget(visual, 1)
        nav = QHBoxLayout()
        self.prev_step = button("< Назад", "secondary", lambda: self._set_guide_step(0))
        self.next_step = button("Далі >", "primary", self._guide_next)
        nav.addWidget(self.prev_step)
        nav.addWidget(self.next_step)
        nav.addStretch()
        nav.addWidget(button("На початок", "link", self._return_to_welcome))
        body.addLayout(nav)
        self.pages.addWidget(page)
        self._set_guide_step(0)

    def _set_page(self, number: int):
        self.pages.setCurrentIndex(number)
        for i, item in enumerate(self.step_labels):
            item.setObjectName("activeStep" if i == number else "step")
            item.style().unpolish(item)
            item.style().polish(item)
        effect = QGraphicsOpacityEffect(self.pages.currentWidget())
        self.pages.currentWidget().setGraphicsEffect(effect)
        self.animation = QPropertyAnimation(effect, b"opacity", self)
        self.animation.setDuration(230)
        self.animation.setStartValue(0.25)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()

    def _confirm_start(self):
        dialog = ConfirmDialog(self)
        dialog.setStyleSheet(STYLESHEET)
        if dialog.exec() != QDialog.Accepted:
            return
        self._set_page(1)
        self.progress.setValue(0)
        self.stage.setText("Починаємо…")
        self.current_stage = "Початок"
        self.log.clear()
        self.retry.hide()
        self.worker = InstallThread()
        self.worker.stage.connect(self._on_stage)
        self.worker.installed.connect(self._on_installed)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_stage(self, percent: int, text: str):
        self.current_stage = text
        self.progress.setValue(percent)
        self.stage.setText(text)
        self.log.append(f"{percent:>3}%   {text}")

    def _on_installed(self, path: str):
        self.pack = Path(path)
        self._show_guide()

    def _on_failed(self, message: str):
        self.stage.setText("Помилка на етапі: " + self.current_stage)
        self.stage.setStyleSheet("color: #ff938e")
        self.log.append("\n" + message)
        self.retry.show()

    def _open_existing(self):
        self._show_guide()

    def _show_guide(self):
        if self.pack is None:
            return
        self.option.setText(launch_option(self.pack))
        self.option.setToolTip(self.option.text())
        self._set_guide_step(0)
        self._set_page(2)

    def _set_guide_step(self, number: int):
        self.guide_step = number
        names = ["1 / 2   У бібліотеці Steam відкрий шестерню > Властивості", "2 / 2   У розділі «Загальні» знайди «Параметри запуску»"]
        files = ["steam-library-clean.png", "steam-launch-options.png"]
        self.guide_title.setText(names[number])
        source = SITE_ASSETS / files[number]
        pixmap = QPixmap(str(source))
        if not pixmap.isNull():
            if number == 0:
                pixmap = pixmap.copy(0, 410, pixmap.width(), 360)
            else:
                pixmap = pixmap.copy(250, 405, 800, 230)
            self.guide_image.setPixmap(pixmap.scaled(820, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.guide_image.setText("Зображення інструкції недоступне")
        self.prev_step.setEnabled(number > 0)
        self.next_step.setText("Готово" if number == 1 else "Далі >")

    def _guide_next(self):
        if self.guide_step == 0:
            self._set_guide_step(1)
        else:
            self.close()

    def _copy_option(self):
        QApplication.clipboard().setText(self.option.text())
        self.guide_title.setText("Рядок скопійовано · встав його в параметри запуску Steam")

    def _return_to_welcome(self):
        self.stage.setStyleSheet("")
        self._set_page(0)


def run_app(screenshot: Path | None = None, guide: bool = False) -> int:
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv[:1])
    grayscale_style = GrayscaleTextStyle()
    app.setStyle(grayscale_style)
    app.setWindowIcon(QIcon(str(ASSETS / "app.png")))
    font_id = QFontDatabase.addApplicationFont(str(ASSETS / "Nunito.ttf"))
    QFontDatabase.addApplicationFont(str(ASSETS / "Rubik.ttf"))
    QFontDatabase.addApplicationFont(str(ASSETS / "LilitaOne.ttf"))
    if font_id >= 0:
        font = QFont("Nunito", 10)
        font.setStyleStrategy(QFont.StyleStrategy.NoSubpixelAntialias)
        app.setFont(font)
    window = MainWindow()
    if screenshot:
        if guide:
            window.pack = Path(r"C:\Users\Player\AppData\Local\DubTogether-UA\DubTogether-UA.pck")
            window._show_guide()
        window.show()
        app.processEvents()
        loop = QEventLoop()
        QTimer.singleShot(310, loop.quit)
        loop.exec()
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        window.grab().save(str(screenshot))
        window.close()
        return 0
    window.show()
    return app.exec()
