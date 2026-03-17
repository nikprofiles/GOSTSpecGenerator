"""
Виджет предпросмотра PDF через PyMuPDF (fitz).
Рендерит страницы PDF в QPixmap и отображает в QScrollArea.
- Ctrl + вращение колёсика = масштабирование
- Ctrl + зажатое колёсико (средняя кнопка) + движение мыши = перемещение по листу (pan)
- Обычное колёсико = вертикальный скролл
"""

import os

from PySide6.QtWidgets import QScrollArea, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap, QImage, QCursor

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


class PdfPreviewWidget(QScrollArea):
    """Виджет для предпросмотра PDF-документа."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)

        # Контейнер для страниц
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._layout.setSpacing(10)
        self.setWidget(self._container)

        self._page_labels: list[QLabel] = []
        self._current_pdf_path: str = ""
        self._zoom_dpi: int = 150
        self._zoom_min: int = 50
        self._zoom_max: int = 400
        self._zoom_step: int = 25

        # Pan (перемещение средней кнопкой мыши)
        self._panning: bool = False
        self._pan_start: QPoint = QPoint()

    def show_pdf(self, pdf_path: str, dpi: int | None = None):
        """Отображает PDF-файл в виджете."""
        self._current_pdf_path = pdf_path
        if dpi is not None:
            self._zoom_dpi = dpi
        self._render()

    def _render(self):
        """Рендерит текущий PDF с текущим DPI."""
        self._clear_pages()

        if not HAS_PYMUPDF:
            lbl = QLabel("PyMuPDF не установлен.\nУстановите: pip install PyMuPDF")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(lbl)
            self._page_labels.append(lbl)
            return

        if not self._current_pdf_path or not os.path.exists(self._current_pdf_path):
            lbl = QLabel(f"Файл не найден: {self._current_pdf_path}")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(lbl)
            self._page_labels.append(lbl)
            return

        try:
            doc = fitz.open(self._current_pdf_path)
        except Exception as e:
            lbl = QLabel(f"Ошибка открытия PDF: {e}")
            self._layout.addWidget(lbl)
            self._page_labels.append(lbl)
            return

        try:
            zoom = self._zoom_dpi / 72
            mat = fitz.Matrix(zoom, zoom)

            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=mat)

                img = QImage(pix.samples, pix.width, pix.height,
                             pix.stride, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(img)

                lbl = QLabel()
                lbl.setPixmap(pixmap)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet("border: 1px solid #ccc; background: white;")
                self._layout.addWidget(lbl)
                self._page_labels.append(lbl)
        finally:
            doc.close()

    # ── Zoom: Ctrl + вращение колёсика ──

    def wheelEvent(self, event):
        """Ctrl+колёсико = zoom. Обычное колёсико = скролл."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and self._current_pdf_path:
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom_dpi = min(self._zoom_dpi + self._zoom_step, self._zoom_max)
            elif delta < 0:
                self._zoom_dpi = max(self._zoom_dpi - self._zoom_step, self._zoom_min)
            self._render()
            event.accept()
            return
        super().wheelEvent(event)

    # ── Pan: средняя кнопка мыши (зажатое колёсико) + движение ──

    def mousePressEvent(self, event):
        """Зажатие средней кнопки (колёсика) — начало перемещения."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.globalPosition().toPoint()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Перемещение при зажатой средней кнопке."""
        if self._panning:
            delta = event.globalPosition().toPoint() - self._pan_start
            self._pan_start = event.globalPosition().toPoint()
            # Двигаем скроллбары
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Отпускание средней кнопки — конец перемещения."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # ── Остальное ──

    def show_message(self, text: str):
        """Показывает текстовое сообщение вместо PDF."""
        self._current_pdf_path = ""
        self._clear_pages()
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #666; font-size: 14px; padding: 40px;")
        self._layout.addWidget(lbl)
        self._page_labels.append(lbl)

    def _clear_pages(self):
        """Удаляет все отображённые страницы."""
        for lbl in self._page_labels:
            self._layout.removeWidget(lbl)
            lbl.deleteLater()
        self._page_labels.clear()
