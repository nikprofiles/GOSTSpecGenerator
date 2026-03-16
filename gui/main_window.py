"""
Главное окно приложения — объединяет все панели и логику.
"""

import os
import tempfile

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTabWidget, QPushButton, QToolBar, QFileDialog,
    QMessageBox, QStatusBar, QSplitter, QApplication,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon

from gui.settings_panel import SettingsPanel
from gui.data_table_view import DataTableWidget
from gui.pdf_preview_widget import PdfPreviewWidget
from core.data_model import SpecificationDocument
from core.excel_reader import read_excel, ExcelReaderError
from core.pdf_generator import SpecPdfGenerator
from core.autonumber import autonumber, needs_autonumber


class MainWindow(QMainWindow):
    """Главное окно генератора спецификаций."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор спецификаций ГОСТ 21.110-2013")
        self.setMinimumSize(1000, 700)
        self._temp_pdf_path = None
        self._current_excel_path = None
        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()

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

        splitter.addWidget(self.tab_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

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
            for w in warnings:
                self.status_bar.showMessage(w, 5000)

        self.status_bar.showMessage(msg)

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
            # Временный файл
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
                os.startfile(path)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать PDF:\n{e}")

    def _on_about(self):
        QMessageBox.about(
            self,
            "О программе",
            "GOSTSpecGenerator v1.0.9\n"
            "Генератор спецификаций по ГОСТ 21.110-2013\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Программа автоматически формирует PDF-документы\n"
            "спецификаций оборудования, изделий и материалов\n"
            "с рамками и штампами по ГОСТ 21.101.\n\n"
            "Возможности:\n"
            "  - Импорт данных из Excel (.xlsx)\n"
            "  - Форматы А4, А3, А2, А1 (книжная/альбомная)\n"
            "  - Штамп первого листа (Форма 3) и последующих (Форма 2а)\n"
            "  - Автоопределение категорий и подкатегорий\n"
            "  - Иерархическая автонумерация позиций\n"
            "  - Вставка строк вручную (кнопки + ПКМ)\n"
            "  - Настраиваемые роли с датами в штампе\n"
            "  - Эмблема организации (PNG/JPEG)\n"
            "  - Автосокращение длинных текстов\n"
            "  - Округление десятичных чисел\n\n"
            "Кому полезна:\n"
            "  Проектировщикам, инженерам ПГС/ЭС/ОВ/ВК,\n"
            "  студентам технических вузов — всем, кто\n"
            "  оформляет спецификации по ГОСТ.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "ВНИМАНИЕ: Это черновая версия программы.\n"
            "Она будет обязательно дорабатываться\n"
            "и совершенствоваться в будущих обновлениях.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Developers: Egorov N.O., Kozlov M.S.\n"
            "Старая гвардия ППП\n\n"
            "GitHub: github.com/nikprofiles/GOSTSpecGenerator"
        )

    def closeEvent(self, event):
        """Очистка временных файлов."""
        if self._temp_pdf_path and os.path.exists(self._temp_pdf_path):
            try:
                os.unlink(self._temp_pdf_path)
            except OSError:
                pass
        super().closeEvent(event)
