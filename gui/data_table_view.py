"""
Таблица данных спецификации с кнопками вставки строк и контекстным меню.
"""

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QMenu, QInputDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QAction

from core.data_model import SpecificationRow, RowType


_TABLE_HEADERS = [
    "Поз.", "Наименование и\nтехн. характеристика", "Тип, марка,\nобозначение",
    "Код\nпродукции", "Поставщик", "Ед.\nизм.", "Кол.", "Масса\n1 ед., кг", "Примечание",
]


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

        text = ""
        if row_type in (RowType.CATEGORY, RowType.SUBCATEGORY):
            label = "категории" if row_type == RowType.CATEGORY else "подкатегории"
            text, ok = QInputDialog.getText(self, f"Название {label}",
                                             f"Введите название {label}:")
            if not ok:
                return

        row = SpecificationRow(name=text, row_type=row_type)
        self.table.insert_row_at(insert_at, row)

    def _delete_row(self):
        current = self.table.currentRow()
        if current >= 0:
            self.table.removeRow(current)
            if current < len(self.table._row_types):
                self.table._row_types.pop(current)

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
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in range(len(_TABLE_HEADERS)):
            if i != 1:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        self.verticalHeader().setDefaultSectionSize(30)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._row_types: list[RowType] = []

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        row = self.rowAt(pos.y())

        act_cat_above = QAction("Вставить категорию выше", self)
        act_cat_above.triggered.connect(lambda: self._ctx_insert(row, RowType.CATEGORY))
        menu.addAction(act_cat_above)

        act_sub_above = QAction("Вставить подкатегорию выше", self)
        act_sub_above.triggered.connect(lambda: self._ctx_insert(row, RowType.SUBCATEGORY))
        menu.addAction(act_sub_above)

        act_data_above = QAction("Вставить строку выше", self)
        act_data_above.triggered.connect(lambda: self._ctx_insert(row, RowType.DATA))
        menu.addAction(act_data_above)

        menu.addSeparator()

        act_data_below = QAction("Вставить строку ниже", self)
        act_data_below.triggered.connect(lambda: self._ctx_insert(row + 1, RowType.DATA))
        menu.addAction(act_data_below)

        menu.addSeparator()

        act_del = QAction("Удалить строку", self)
        act_del.triggered.connect(lambda: self._ctx_delete(row))
        menu.addAction(act_del)

        menu.exec(self.mapToGlobal(pos))

    def _ctx_insert(self, at: int, row_type: RowType):
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

    def _ctx_delete(self, row: int):
        if 0 <= row < self.rowCount():
            self.removeRow(row)
            if row < len(self._row_types):
                self._row_types.pop(row)

    def insert_row_at(self, idx: int, spec_row: SpecificationRow):
        """Вставляет строку в таблицу в позицию idx."""
        self.insertRow(idx)
        self._row_types.insert(idx, spec_row.row_type)

        bold_font = QFont()
        bold_font.setBold(True)
        italic_font = QFont()
        italic_font.setItalic(True)
        cat_bg = QColor(220, 230, 245)
        subcat_bg = QColor(240, 240, 240)

        for col_idx, val in enumerate(spec_row.to_row_values()):
            item = QTableWidgetItem(val)
            if spec_row.row_type == RowType.CATEGORY:
                item.setFont(bold_font)
                item.setBackground(cat_bg)
            elif spec_row.row_type == RowType.SUBCATEGORY:
                item.setFont(italic_font)
                item.setBackground(subcat_bg)
            self.setItem(idx, col_idx, item)

    def load_rows(self, rows: list[SpecificationRow]):
        # Отключаем отрисовку на время загрузки — критично для производительности
        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        try:
            self.setRowCount(len(rows))
            self._row_types = []

            bold_font = QFont()
            bold_font.setBold(True)
            italic_font = QFont()
            italic_font.setItalic(True)
            cat_bg = QColor(220, 230, 245)
            subcat_bg = QColor(240, 240, 240)

            for row_idx, spec_row in enumerate(rows):
                self._row_types.append(spec_row.row_type)
                for col_idx, val in enumerate(spec_row.to_row_values()):
                    item = QTableWidgetItem(val)
                    if spec_row.row_type == RowType.CATEGORY:
                        item.setFont(bold_font)
                        item.setBackground(cat_bg)
                    elif spec_row.row_type == RowType.SUBCATEGORY:
                        item.setFont(italic_font)
                        item.setBackground(subcat_bg)
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

    def clear_data(self):
        self.setRowCount(0)
        self._row_types.clear()
