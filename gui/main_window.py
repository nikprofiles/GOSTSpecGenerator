"""
Главное окно приложения — объединяет все панели и логику.
"""

import os
import platform
import subprocess
import tempfile

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTabWidget, QPushButton, QToolBar, QFileDialog,
    QMessageBox, QStatusBar, QSplitter, QApplication,
    QScrollArea, QLabel,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPixmap, QImage

from gui.settings_panel import SettingsPanel
from gui.data_table_view import DataTableWidget
from gui.pdf_preview_widget import PdfPreviewWidget
from core.data_model import SpecificationDocument
from core.excel_reader import read_excel, ExcelReaderError
from core.pdf_generator import SpecPdfGenerator
from core.constants import APP_VERSION
from core.autonumber import autonumber, needs_autonumber


class MainWindow(QMainWindow):
    """Главное окно генератора спецификаций."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Генератор спецификаций ГОСТ 21.110-2013 — v{APP_VERSION}")
        self.setMinimumSize(1000, 700)
        self._temp_pdf_path = None
        self._current_excel_path = None
        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()
        self.settings_panel.load_settings()

    def _init_ui(self):
        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Splitter: настройки | данные/превью
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Левая панель — настройки
        self.settings_panel = SettingsPanel()
        self.settings_panel.setMaximumWidth(350)
        self.settings_panel.setMinimumWidth(250)
        splitter.addWidget(self.settings_panel)

        # Правая панель — вкладки
        self.tab_widget = QTabWidget()

        # Вкладка "Данные"
        self.data_table = DataTableWidget()
        self.tab_widget.addTab(self.data_table, "Данные")

        # Вкладка "Предпросмотр PDF"
        self.pdf_preview = PdfPreviewWidget()
        self.pdf_preview.show_message("Загрузите Excel-файл и нажмите «Предпросмотр»")
        self.tab_widget.addTab(self.pdf_preview, "Предпросмотр PDF")

        # Вкладка "Справка"
        self.tab_widget.addTab(self._create_help_tab(), "Справка")

        splitter.addWidget(self.tab_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # При смене формата/ориентации — подсказка в statusbar
        self.settings_panel.settings_changed.connect(self._on_settings_changed)

        # Lazy-загрузка изображения штампа при переключении на вкладку «Справка»
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

    def _init_menu(self):
        menubar = self.menuBar()

        # Файл
        file_menu = menubar.addMenu("Файл")

        open_action = QAction("Загрузить Excel...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_load_excel)
        file_menu.addAction(open_action)

        export_action = QAction("Сохранить PDF...", self)
        export_action.setShortcut("Ctrl+S")
        export_action.triggered.connect(self._on_save_pdf)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Помощь
        help_menu = menubar.addMenu("Помощь")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _init_toolbar(self):
        toolbar = QToolBar("Основные действия")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        btn_load = QPushButton("Загрузить Excel")
        btn_load.clicked.connect(self._on_load_excel)
        toolbar.addWidget(btn_load)

        btn_autonumber = QPushButton("Автонумерация")
        btn_autonumber.clicked.connect(self._on_autonumber)
        toolbar.addWidget(btn_autonumber)

        toolbar.addSeparator()

        btn_preview = QPushButton("Предпросмотр")
        btn_preview.clicked.connect(self._on_preview)
        toolbar.addWidget(btn_preview)

        btn_save = QPushButton("Сохранить PDF")
        btn_save.clicked.connect(self._on_save_pdf)
        toolbar.addWidget(btn_save)

        toolbar.addSeparator()

        btn_save_settings = QPushButton("Сохранить настройки")
        btn_save_settings.setToolTip("Сохранить текущие настройки штампа для следующего запуска")
        btn_save_settings.clicked.connect(self._on_save_settings)
        toolbar.addWidget(btn_save_settings)

    def _init_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")

    # ── Обработчики ──

    def _on_load_excel(self):
        """Загрузка Excel-файла."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл спецификации",
            "", "Excel файлы (*.xlsx *.xls);;Все файлы (*)"
        )
        if not path:
            return

        try:
            rows, warnings = read_excel(path)
        except ExcelReaderError as e:
            QMessageBox.critical(self, "Ошибка чтения", str(e))
            return

        self._current_excel_path = path

        # Проверяем: нужна ли автонумерация?
        if needs_autonumber(rows):
            reply = QMessageBox.question(
                self, "Автонумерация",
                "В файле обнаружены строки без позиций.\n"
                "Выполнить автоматическую нумерацию?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                autonumber(rows)

        self.data_table.load_rows(rows)
        self.tab_widget.setCurrentIndex(0)

        msg = f"Загружено {len(rows)} строк из {os.path.basename(path)}"
        if warnings:
            msg += f" ({len(warnings)} предупр.)"
            QMessageBox.warning(
                self, "Предупреждения при загрузке",
                "\n".join(warnings),
            )

        self.status_bar.showMessage(msg)

    def _on_tab_changed(self, index: int):
        """Lazy-генерация изображения штампа для вкладки «Справка»."""
        if index == 2 and hasattr(self, '_help_stamp_generated') and not self._help_stamp_generated:
            self._help_stamp_generated = True
            pixmap = self._generate_help_stamp_image()
            if pixmap and hasattr(self, '_help_stamp_label'):
                self._help_stamp_label.setPixmap(pixmap)
                self._help_stamp_label.setStyleSheet("border: 1px solid #ccc; background: white; padding: 5px;")

    def _on_save_settings(self):
        """Ручное сохранение настроек."""
        self.settings_panel.save_settings()
        self.status_bar.showMessage("Настройки сохранены", 5000)

    def _on_settings_changed(self):
        """Подсказка при смене формата/ориентации."""
        self.status_bar.showMessage("Формат изменён. Нажмите «Предпросмотр» для обновления.", 8000)

    def _on_autonumber(self):
        """Ручной запуск автонумерации — быстрое обновление только позиций."""
        rows = self.data_table.get_rows()
        if not rows:
            QMessageBox.warning(self, "Нет данных", "Сначала загрузите Excel-файл.")
            return

        autonumber(rows)
        # Быстрое обновление: только колонка "Поз.", без пересоздания всей таблицы
        self.data_table.table.update_positions(rows)
        self.status_bar.showMessage("Автонумерация выполнена")

    def _build_document(self) -> SpecificationDocument:
        """Собирает документ из GUI."""
        return SpecificationDocument(
            stamp=self.settings_panel.get_stamp_info(),
            rows=self.data_table.get_rows(),
            page_format=self.settings_panel.get_page_format(),
            orientation=self.settings_panel.get_orientation(),
            font_name=self.settings_panel.get_font_name(),
        )

    def _on_preview(self):
        """Генерация PDF для предпросмотра."""
        doc = self._build_document()
        if not doc.rows:
            self.pdf_preview.show_message("Нет данных для предпросмотра.\nЗагрузите Excel-файл.")
            self.tab_widget.setCurrentIndex(1)
            return

        self.status_bar.showMessage("Генерация предпросмотра...")
        QApplication.processEvents()

        try:
            # Удаляем предыдущий временный файл
            if self._temp_pdf_path:
                try:
                    os.unlink(self._temp_pdf_path)
                except OSError:
                    pass

            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()
            self._temp_pdf_path = tmp.name

            generator = SpecPdfGenerator(doc)
            generator.generate(self._temp_pdf_path)

            self.pdf_preview.show_pdf(self._temp_pdf_path)
            self.tab_widget.setCurrentIndex(1)
            self.status_bar.showMessage("Предпросмотр готов")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка генерации", str(e))
            self.status_bar.showMessage("Ошибка генерации PDF")
            # Удаляем временный файл при ошибке
            if self._temp_pdf_path and os.path.exists(self._temp_pdf_path):
                try:
                    os.unlink(self._temp_pdf_path)
                except OSError:
                    pass
            self._temp_pdf_path = None

    def _on_save_pdf(self):
        """Сохранение PDF на диск."""
        doc = self._build_document()
        if not doc.rows:
            QMessageBox.warning(self, "Нет данных", "Загрузите Excel-файл перед сохранением.")
            return

        # Предлагаем имя файла на основе обозначения документа
        default_name = doc.stamp.designation or "specification"
        default_name = default_name.replace("/", "_").replace("\\", "_")

        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить PDF",
            f"{default_name}.pdf",
            "PDF файлы (*.pdf);;Все файлы (*)"
        )
        if not path:
            return

        self.status_bar.showMessage("Генерация PDF...")
        QApplication.processEvents()

        try:
            generator = SpecPdfGenerator(doc)
            generator.generate(path)
            self.status_bar.showMessage(f"PDF сохранён: {path}")

            # Предлагаем открыть
            reply = QMessageBox.question(
                self, "PDF создан",
                f"Файл сохранён:\n{path}\n\nОткрыть?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                system = platform.system()
                if system == "Windows":
                    os.startfile(path)
                elif system == "Darwin":
                    subprocess.Popen(["open", path])
                else:
                    subprocess.Popen(["xdg-open", path])

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать PDF:\n{e}")

    def _create_help_tab(self) -> QWidget:
        """Создаёт вкладку «Справка» с пустым штампом и горячими клавишами.
        Изображение штампа генерируется лениво при первом показе."""

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)

        # Placeholder для изображения штампа (генерируется лениво)
        self._help_stamp_label = QLabel("Загрузка схемы штампа...")
        self._help_stamp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._help_stamp_generated = False
        layout.addWidget(self._help_stamp_label)

        # HTML-часть: горячие клавиши и типы строк
        html_label = QLabel()
        html_label.setWordWrap(True)
        html_label.setTextFormat(Qt.TextFormat.RichText)
        html_label.setText("""
        <h3>Горячие клавиши</h3>
        <table border="0" cellpadding="4" style="font-size:13px;">
          <tr><td><b>Ctrl+O</b></td><td>Загрузить Excel-файл</td></tr>
          <tr><td><b>Ctrl+S</b></td><td>Сохранить PDF</td></tr>
          <tr><td><b>Ctrl+Z</b></td><td>Отменить последнее действие</td></tr>
          <tr><td><b>Ctrl+Y</b></td><td>Повторить отменённое действие</td></tr>
          <tr><td><b>Ctrl+C</b></td><td>Копировать выделенные ячейки</td></tr>
          <tr><td><b>Ctrl+V</b></td><td>Вставить из буфера обмена</td></tr>
          <tr><td><b>Ctrl+колёсико</b></td><td>Масштаб в предпросмотре PDF</td></tr>
          <tr><td><b>ПКМ на строке</b></td><td>Контекстное меню: вставка, удаление, назначение типа</td></tr>
        </table>
        <br>
        <h3>Типы строк</h3>
        <table border="0" cellpadding="4" style="font-size:13px;">
          <tr><td style="background:#dce6f5;padding:4px 12px;"><b>Категория</b></td>
              <td>Жирный шрифт, голубой фон. Номер: 1, 2, 3...</td></tr>
          <tr><td style="background:#f0f0f0;padding:4px 12px;"><i>Подкатегория</i></td>
              <td>Курсив, серый фон. Номер: 1.1, 1.2, 2.1...</td></tr>
          <tr><td style="padding:4px 12px;">Строка данных</td>
              <td>Обычный шрифт. Номер: 1.1.1, 1.1.2...</td></tr>
        </table>
        <p style="color:#888;font-size:11px;">Назначить тип строки: ПКМ на строке → «Назначить тип»</p>
        """)

        layout.addWidget(html_label)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _generate_help_stamp_image(self):
        """Генерирует PNG только области штампа с названиями полей."""
        try:
            from core.data_model import StampInfo, StampRole, SpecificationDocument, PageFormat, Orientation
            from core.pdf_generator import SpecPdfGenerator
            from core.constants import FRAME_MARGIN_BOTTOM, STAMP_F3_HEIGHT, FRAME_MARGIN_RIGHT, STAMP_F3_WIDTH, MM

            help_stamp = StampInfo(
                designation="Обозначение документа",
                organization="Организация / Эмблема",
                building_name="Объект строительства",
                sheet_title="Содержание листа",
                user_field="Наименование листа",
                stage="Ст.",
                roles=[
                    StampRole(role_name="Роль", person_name="Фамилия", date="Дата"),
                    StampRole(role_name="Роль", person_name="Фамилия", date="Дата"),
                    StampRole(role_name="Роль", person_name="Фамилия", date="Дата"),
                    StampRole(role_name="Роль", person_name="Фамилия", date="Дата"),
                    StampRole(role_name="", person_name="", date=""),
                ],
            )

            doc = SpecificationDocument(
                stamp=help_stamp, rows=[],
                page_format=PageFormat.A4, orientation=Orientation.PORTRAIT,
            )

            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()
            gen = SpecPdfGenerator(doc)
            gen.generate(tmp.name)

            import fitz
            pdf_doc = fitz.open(tmp.name)
            page = pdf_doc[0]

            # Обрезаем только область штампа (нижние ~65мм страницы)
            page_h_pt = page.rect.height
            page_w_pt = page.rect.width
            # Штамп: от (sx, 0) до (page_w - margin_right, stamp_h + margin_bottom) в PDF-координатах
            # В PyMuPDF Y=0 сверху, поэтому штамп внизу
            stamp_top_pt = page_h_pt - (STAMP_F3_HEIGHT + FRAME_MARGIN_BOTTOM + 5) * MM
            clip = fitz.Rect(0, stamp_top_pt, page_w_pt, page_h_pt)

            pix = page.get_pixmap(dpi=150, clip=clip)
            img = QImage(pix.samples, pix.width, pix.height,
                         pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            # Масштабируем до разумной ширины
            pixmap = pixmap.scaledToWidth(min(800, pixmap.width()),
                                          Qt.TransformationMode.SmoothTransformation)

            pdf_doc.close()
            os.unlink(tmp.name)
            return pixmap
        except Exception:
            return None

    def _on_about(self):
        QMessageBox.about(
            self,
            "О программе",
            f"GOSTSpecGenerator v{APP_VERSION}\n"
            "Генератор спецификаций по ГОСТ 21.110-2013\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Программа формирует PDF-спецификации\n"
            "оборудования и материалов с рамками\n"
            "и штампами по ГОСТ 21.101.\n\n"
            "Что нового (v1.0.10 -> v1.1.7):\n"
            "  + 3-уровневая автонумерация (1 > 1.1 > 1.1.1)\n"
            "  + Ручное назначение типа строки (ПКМ)\n"
            "  + Сохранение настроек между сессиями\n"
            "  + Undo/Redo (Ctrl+Z/Y)\n"
            "  + Copy/Paste (Ctrl+C/V)\n"
            "  + Zoom предпросмотра (Ctrl+колёсико)\n"
            "  + Pan перемещение (зажать колёсико)\n"
            "  + Выбор шрифта (Arial/Times/ISOCPEUR)\n"
            "  + Вкладка Справка со схемой штампа\n"
            "  + Tooltips на полях настроек\n"
            "  + Кнопка сброса настроек\n"
            "  + Исправлена ориентация A3/A2/A1\n"
            "  + Дата в правильном столбце штампа\n"
            "  + Фамилия по левому краю без разрыва\n"
            "  + Рефакторинг и оптимизация кода\n\n"
            "Для кого:\n"
            "  Проектировщики, инженеры ПГС/ЭС/ОВ/ВК,\n"
            "  студенты технических вузов.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Developers: Egorov N.O., Kozlov M.S.\n"
            "Старая гвардия ППП\n\n"
            "GitHub: github.com/nikprofiles/GOSTSpecGenerator"
        )

    def closeEvent(self, event):
        """Сохраняем настройки и чистим временные файлы."""
        self.settings_panel.save_settings()
        if self._temp_pdf_path and os.path.exists(self._temp_pdf_path):
            try:
                os.unlink(self._temp_pdf_path)
            except OSError:
                pass
        super().closeEvent(event)
