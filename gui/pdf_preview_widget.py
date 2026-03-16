"""
Виджет предпросмотра PDF через PyMuPDF (fitz).
Рендерит страницы PDF в QPixmap и отображает в QScrollArea.
"""

import os
import tempfile

from PySide6.QtWidgets import QScrollArea, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage

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

    def show_pdf(self, pdf_path: str, dpi: int = 150):
        """Отображает PDF-файл в виджете."""
        self._clear_pages()

        if not HAS_PYMUPDF:
            lbl = QLabel("PyMuPDF не установлен.\nУстановите: pip install PyMuPDF")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(lbl)
            self._page_labels.append(lbl)
            return

        if not os.path.exists(pdf_path):
            lbl = QLabel(f"Файл не найден: {pdf_path}")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(lbl)
            self._page_labels.append(lbl)
            return

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            lbl = QLabel(f"Ошибка открытия PDF: {e}")
            self._layout.addWidget(lbl)
            self._page_labels.append(lbl)
            return

        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)

        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=mat)

            # Конвертация в QImage → QPixmap
            img = QImage(pix.samples, pix.width, pix.height,
                         pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)

            lbl = QLabel()
            lbl.setPixmap(pixmap)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("border: 1px solid #ccc; background: white;")
            self._layout.addWidget(lbl)
            self._page_labels.append(lbl)

        doc.close()

    def show_message(self, text: str):
        """Показывает текстовое сообщение вместо PDF."""
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
