"""
Таблица данных спецификации с кнопками вставки строк и контекстным меню.
"""

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QMenu, QInputDialog,
    QApplication,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QAction

from core.data_model import SpecificationRow, RowType


_TABLE_HEADERS = [
    "Поз.", "Наименование и\nтехн. характеристика", "Тип, марка,\nобозначение",
    "Код\nпродукции", "Поставщик", "Ед.\nизм.", "Кол.", "Масса\n1 ед., кг", "Примечание",
]

# Стили строк (создаются один раз, используются везде)
_BOLD_FONT = QFont()
_BOLD_FONT.setBold(True)
_ITALIC_FONT = QFont()
_ITALIC_FONT.setItalic(True)
_NORMAL_FONT = QFont()
_CAT_BG = QColor(220, 230, 245)
_SUBCAT_BG = QColor(240, 240, 240)
_NORMAL_BG = QColor(255, 255, 255)


def _style_item(item: QTableWidgetItem, row_type: RowType):
    """Применяет визуальный стиль к ячейке по типу строки."""
    if row_type == RowType.CATEGORY:
        item.setFont(_BOLD_FONT)
        item.setBackground(_CAT_BG)
    elif row_type == RowType.SUBCATEGORY:
        item.setFont(_ITALIC_FONT)
        item.setBackground(_SUBCAT_BG)
    else:
        item.setFont(_NORMAL_FONT)
        item.setBackground(_NORMAL_BG)


class DataTableWidget(QWidget):
    """Обёртка: кнопки вставки + таблица."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Кнопки
        btn_layout = QHBoxLayout()

        btn_cat = QPushButton("+ Категория")
        btn_cat.setToolTip("Вставить заголовок категории (жирный)")
        btn_cat.clicked.connect(lambda: self._insert_row(RowType.CATEGORY))
        btn_layout.addWidget(btn_cat)

        btn_sub = QPushButton("+ Подкатегория")
        btn_sub.setToolTip("Вставить подкатегорию (курсив)")
        btn_sub.clicked.connect(lambda: self._insert_row(RowType.SUBCATEGORY))
        btn_layout.addWidget(btn_sub)

        btn_data = QPushButton("+ Строка данных")
        btn_data.setToolTip("Вставить пустую строку данных")
        btn_data.clicked.connect(lambda: self._insert_row(RowType.DATA))
        btn_layout.addWidget(btn_data)

        btn_del = QPushButton("Удалить строку")
        btn_del.clicked.connect(self._delete_row)
        btn_layout.addWidget(btn_del)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Таблица
        self.table = DataTableView(self)
        layout.addWidget(self.table)

    def _insert_row(self, row_type: RowType):
        """Вставить строку выше текущей позиции."""
        current = self.table.currentRow()
        insert_at = current if current >= 0 else self.table.rowCount()
        self.table.prompt_and_insert(insert_at, row_type)

    def _delete_row(self):
        current = self.table.currentRow()
        if current >= 0:
            self.table.save_snapshot()
            if current < len(self.table._row_types):
                self.table._row_types.pop(current)
            self.table.removeRow(current)

    # Проксирование методов таблицы
    def load_rows(self, rows):
        self.table.load_rows(rows)

    def get_rows(self):
        return self.table.get_rows()

    def clear_data(self):
        self.table.clear_data()


class DataTableView(QTableWidget):
    """Таблица данных спецификации (9 колонок) с контекстным меню."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(_TABLE_HEADERS))
        self.setHorizontalHeaderLabels(_TABLE_HEADERS)

        header = self.horizontalHeader()
        header.setMinimumSectionSize(30)
        header.setStretchLastSection(True)
        # Все столбцы Interactive — пользователь может двигать границы с обеих сторон
        for i in range(len(_TABLE_HEADERS)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        # Начальные ширины столбцов
        default_widths = [50, 300, 150, 80, 100, 50, 50, 70, 80]
        for i, w in enumerate(default_widths):
            if i < self.columnCount():
                self.setColumnWidth(i, w)

        self.verticalHeader().setDefaultSectionSize(30)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._row_types: list[RowType] = []

        # Undo/Redo стек (snapshot-based)
        from collections import deque
        self._undo_stack: deque[list[SpecificationRow]] = deque(maxlen=30)
        self._redo_stack: list[list[SpecificationRow]] = []

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        row = self.rowAt(pos.y())

        act_cat_above = QAction("Вставить категорию выше", self)
        act_cat_above.triggered.connect(lambda: self.prompt_and_insert(row, RowType.CATEGORY))
        menu.addAction(act_cat_above)

        act_sub_above = QAction("Вставить подкатегорию выше", self)
        act_sub_above.triggered.connect(lambda: self.prompt_and_insert(row, RowType.SUBCATEGORY))
        menu.addAction(act_sub_above)

        act_data_above = QAction("Вставить строку выше", self)
        act_data_above.triggered.connect(lambda: self.prompt_and_insert(row, RowType.DATA))
        menu.addAction(act_data_above)

        menu.addSeparator()

        act_data_below = QAction("Вставить строку ниже", self)
        act_data_below.triggered.connect(lambda: self.prompt_and_insert(row + 1, RowType.DATA))
        menu.addAction(act_data_below)

        menu.addSeparator()

        # Подменю «Назначить тип»
        if row >= 0:
            type_menu = menu.addMenu("Назначить тип")
            for rtype, label in [
                (RowType.CATEGORY, "Категория"),
                (RowType.SUBCATEGORY, "Подкатегория"),
                (RowType.DATA, "Строка данных"),
            ]:
                act = QAction(label, self)
                act.triggered.connect(lambda checked=False, r=row, t=rtype: self._set_row_type(r, t))
                type_menu.addAction(act)

        menu.addSeparator()

        act_del = QAction("Удалить строку", self)
        act_del.setEnabled(row >= 0)
        act_del.triggered.connect(lambda: self._ctx_delete(row))
        menu.addAction(act_del)

        menu.exec(self.mapToGlobal(pos))

    def prompt_and_insert(self, at: int, row_type: RowType):
        """Запрашивает имя (для категории/подкатегории) и вставляет строку."""
        self.save_snapshot()
        if at < 0:
            at = self.rowCount()

        text = ""
        if row_type in (RowType.CATEGORY, RowType.SUBCATEGORY):
            label = "категории" if row_type == RowType.CATEGORY else "подкатегории"
            text, ok = QInputDialog.getText(self, f"Название {label}",
                                             f"Введите название {label}:")
            if not ok:
                return

        self.insert_row_at(at, SpecificationRow(name=text, row_type=row_type))

    def _set_row_type(self, row: int, row_type: RowType):
        """Меняет тип строки и обновляет визуальное оформление."""
        if row < 0 or row >= self.rowCount():
            return
        self.save_snapshot()
        if row < len(self._row_types):
            self._row_types[row] = row_type

        for col in range(self.columnCount()):
            item = self.item(row, col)
            if not item:
                item = QTableWidgetItem("")
                self.setItem(row, col, item)
            _style_item(item, row_type)

    def _ctx_delete(self, row: int):
        if 0 <= row < self.rowCount():
            self.save_snapshot()
            if row < len(self._row_types):
                self._row_types.pop(row)
            self.removeRow(row)

    def insert_row_at(self, idx: int, spec_row: SpecificationRow):
        """Вставляет строку в таблицу в позицию idx."""
        self.insertRow(idx)
        self._row_types.insert(idx, spec_row.row_type)

        for col_idx, val in enumerate(spec_row.to_row_values()):
            item = QTableWidgetItem(val)
            _style_item(item, spec_row.row_type)
            self.setItem(idx, col_idx, item)

    def load_rows(self, rows: list[SpecificationRow]):
        # Отключаем отрисовку на время загрузки — критично для производительности
        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        try:
            self.setRowCount(len(rows))
            self._row_types = []

            for row_idx, spec_row in enumerate(rows):
                self._row_types.append(spec_row.row_type)
                for col_idx, val in enumerate(spec_row.to_row_values()):
                    item = QTableWidgetItem(val)
                    _style_item(item, spec_row.row_type)
                    self.setItem(row_idx, col_idx, item)
        finally:
            self.blockSignals(False)
            self.setUpdatesEnabled(True)

    def update_positions(self, rows: list[SpecificationRow]):
        """Быстрое обновление только колонки Поз. (для автонумерации)."""
        self.setUpdatesEnabled(False)
        try:
            for row_idx, spec_row in enumerate(rows):
                if row_idx < self.rowCount():
                    item = self.item(row_idx, 0)
                    if item:
                        item.setText(spec_row.position)
                    else:
                        self.setItem(row_idx, 0, QTableWidgetItem(spec_row.position))
                    if row_idx < len(self._row_types):
                        self._row_types[row_idx] = spec_row.row_type
        finally:
            self.setUpdatesEnabled(True)

    def get_rows(self) -> list[SpecificationRow]:
        rows = []
        for row_idx in range(self.rowCount()):
            values = []
            for col_idx in range(self.columnCount()):
                item = self.item(row_idx, col_idx)
                values.append(item.text() if item else "")

            rt = self._row_types[row_idx] if row_idx < len(self._row_types) else RowType.DATA

            rows.append(SpecificationRow(
                position=values[0], name=values[1], type_brand=values[2],
                product_code=values[3], supplier=values[4], unit=values[5],
                quantity=values[6], mass_unit_kg=values[7], notes=values[8],
                row_type=rt,
            ))
        return rows

    def save_snapshot(self):
        """Сохраняет текущее состояние в undo-стек."""
        snapshot = self.get_rows()
        self._undo_stack.append(snapshot)  # deque(maxlen=30) автоматически убирает старые
        self._redo_stack.clear()

    def undo(self):
        """Откатывает последнее действие."""
        if not self._undo_stack:
            return
        # Сохраняем текущее состояние в redo
        self._redo_stack.append(self.get_rows())
        # Восстанавливаем из undo
        snapshot = self._undo_stack.pop()
        self.load_rows(snapshot)

    def redo(self):
        """Повторяет отменённое действие."""
        if not self._redo_stack:
            return
        # Сохраняем текущее в undo
        self._undo_stack.append(self.get_rows())
        # Восстанавливаем из redo
        snapshot = self._redo_stack.pop()
        self.load_rows(snapshot)

    def keyPressEvent(self, event):
        """Обработка Ctrl+Z, Ctrl+Y, Ctrl+C, Ctrl+V."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Z:
                self.undo()
                return
            elif event.key() == Qt.Key.Key_Y:
                self.redo()
                return
            elif event.key() == Qt.Key.Key_C:
                self._copy_selection()
                return
            elif event.key() == Qt.Key.Key_V:
                self._paste_selection()
                return
        super().keyPressEvent(event)

    def _copy_selection(self):
        """Копирует выделенные ячейки в буфер обмена (TSV-формат)."""
        selection = self.selectedRanges()
        if not selection:
            return
        sr = selection[0]
        lines = []
        for row in range(sr.topRow(), sr.bottomRow() + 1):
            cells = []
            for col in range(sr.leftColumn(), sr.rightColumn() + 1):
                item = self.item(row, col)
                cells.append(item.text() if item else "")
            lines.append("\t".join(cells))
        text = "\n".join(lines)
        QApplication.clipboard().setText(text)

    def _paste_selection(self):
        """Вставляет из буфера обмена в таблицу."""
        text = QApplication.clipboard().text()
        if not text:
            return
        self.save_snapshot()
        current_row = self.currentRow()
        current_col = self.currentColumn()
        if current_row < 0:
            current_row = 0
        if current_col < 0:
            current_col = 0
        for r_offset, line in enumerate(text.split("\n")):
            row = current_row + r_offset
            if row >= self.rowCount():
                break
            for c_offset, val in enumerate(line.split("\t")):
                col = current_col + c_offset
                if col >= self.columnCount():
                    break
                item = self.item(row, col)
                if item:
                    item.setText(val)
                else:
                    self.setItem(row, col, QTableWidgetItem(val))

    def clear_data(self):
        self.setRowCount(0)
        self._row_types.clear()
