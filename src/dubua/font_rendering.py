"""Keep Windows text edges neutral at fractional display scaling."""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QProxyStyle


class GrayscaleTextStyle(QProxyStyle):
    """Draw styled text on transparency before compositing it on a widget.

    Windows ClearType can leave red and blue edges in Qt's direct widget text,
    even with QFont.NoSubpixelAntialias. A transparent intermediate surface
    produces neutral alpha coverage while retaining smooth glyph edges.
    """

    def drawItemText(self, painter, rectangle, alignment, palette, enabled, text, text_role=None):
        if rectangle.width() <= 0 or rectangle.height() <= 0:
            return
        scale = painter.device().devicePixelRatioF()
        image = QImage(
            QSize(round(rectangle.width() * scale), round(rectangle.height() * scale)),
            QImage.Format_ARGB32_Premultiplied,
        )
        image.setDevicePixelRatio(scale)
        image.fill(0)
        image_painter = QPainter(image)
        image_painter.setFont(painter.font())
        logical_rect = QRect(0, 0, rectangle.width(), rectangle.height())
        super().drawItemText(image_painter, logical_rect, alignment, palette, enabled, text, text_role)
        image_painter.end()
        painter.drawImage(rectangle.topLeft(), image)
