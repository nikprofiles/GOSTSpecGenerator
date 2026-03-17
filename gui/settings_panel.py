"""
Панель настроек: штамп, формат, роли с датами, эмблема организации.
"""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLineEdit, QComboBox,
    QGroupBox, QLabel, QGridLayout, QPushButton, QFileDialog, QCheckBox,
    QScrollArea,
)
from PySide6.QtCore import Signal, QSettings

from core.data_model import StampInfo, StampRole, PageFormat, Orientation


class SettingsPanel(QScrollArea):
    """Левая панель с настройками (прокручиваемая)."""

    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self._container = QWidget()
        self.setWidget(self._container)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(5, 5, 5, 5)

        # ── Формат и ориентация ──
        format_group = QGroupBox("Формат листа")
        format_layout = QFormLayout()

        self.format_combo = QComboBox()
        for fmt in PageFormat:
            w, h = fmt.value
            self.format_combo.addItem(f"{fmt.name} ({w}×{h} мм)", fmt)
        format_layout.addRow("Формат:", self.format_combo)

        self.orientation_combo = QComboBox()
        self.orientation_combo.addItem("Книжная", Orientation.PORTRAIT)
        self.orientation_combo.addItem("Альбомная", Orientation.LANDSCAPE)
        format_layout.addRow("Ориентация:", self.orientation_combo)

        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # ── Штамп ──
        stamp_group = QGroupBox("Основная надпись (штамп)")
        stamp_layout = QFormLayout()

        self.designation_edit = QLineEdit()
        self.designation_edit.setPlaceholderText("напр. 1234-5-ОВ")
        stamp_layout.addRow("Обозначение:", self.designation_edit)

        self.organization_edit = QLineEdit()
        self.organization_edit.setPlaceholderText("Название организации")
        stamp_layout.addRow("Организация:", self.organization_edit)

        self.building_edit = QLineEdit()
        self.building_edit.setPlaceholderText("Название объекта")
        stamp_layout.addRow("Объект:", self.building_edit)

        self.sheet_title_edit = QLineEdit()
        self.sheet_title_edit.setPlaceholderText("Содержание листа")
        stamp_layout.addRow("Лист:", self.sheet_title_edit)

        self.user_field_edit = QLineEdit()
        self.user_field_edit.setPlaceholderText("Спецификация оборудования и материалов")
        stamp_layout.addRow("Наименование листа:", self.user_field_edit)

        self.stage_combo = QComboBox()
        self.stage_combo.addItems(["Р", "П", "РП", "И"])
        self.stage_combo.setEditable(True)
        stamp_layout.addRow("Стадия:", self.stage_combo)

        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Times New Roman", "ISOCPEUR (ГОСТ)"])
        self.font_combo.setToolTip(
            "Шрифт для PDF.\n"
            "По ГОСТ 2.304 рекомендуется шрифт типа Б (ISOCPEUR).\n"
            "Arial — универсальный fallback с кириллицей.")
        stamp_layout.addRow("Шрифт PDF:", self.font_combo)

        # Tooltips — пояснения где каждое поле отображается в штампе
        self.designation_edit.setToolTip(
            "Верхняя строка правого блока штампа (Форма 3).\n"
            "Обозначение проектной документации, напр. ТР-01-2022-ЭОМ")
        self.organization_edit.setToolTip(
            "Нижний правый угол штампа (Форма 3).\n"
            "Название организации или эмблема (если включена)")
        self.building_edit.setToolTip(
            "Вторая строка правого блока штампа.\n"
            "Полное наименование объекта строительства")
        self.sheet_title_edit.setToolTip(
            "Третья строка правого блока штампа.\n"
            "Например: «Планы уравнивания потенциалов»")
        self.user_field_edit.setToolTip(
            "Четвёртая строка правого блока штампа.\n"
            "Например: «Спецификация оборудования и материалов»")
        self.stage_combo.setToolTip(
            "Стадия проектирования: Р (рабочая), П (проектная),\n"
            "РП (рабочий проект), И (изыскания)")

        stamp_group.setLayout(stamp_layout)
        layout.addWidget(stamp_group)

        # ── Подписи (роль — фамилия — дата) ──
        sign_group = QGroupBox("Подписи")
        sign_layout = QGridLayout()

        sign_layout.addWidget(QLabel("Роль"), 0, 0)
        sign_layout.addWidget(QLabel("Фамилия"), 0, 1)
        sign_layout.addWidget(QLabel("Дата"), 0, 2)

        self._role_edits: list[tuple[QLineEdit, QLineEdit, QLineEdit]] = []
        default_roles = ["Разраб.", "Пров.", "Н.контр.", "Утв.", ""]

        for i, role_name in enumerate(default_roles):
            role_edit = QLineEdit(role_name)
            role_edit.setPlaceholderText("Роль")
            role_edit.setMaximumWidth(90)
            name_edit = QLineEdit()
            name_edit.setPlaceholderText("Фамилия")
            name_edit.setMaximumWidth(110)
            date_edit = QLineEdit()
            date_edit.setPlaceholderText("дд.мм.гг")
            date_edit.setInputMask("99.99.99")
            date_edit.setMaximumWidth(70)
            sign_layout.addWidget(role_edit, i + 1, 0)
            sign_layout.addWidget(name_edit, i + 1, 1)
            sign_layout.addWidget(date_edit, i + 1, 2)
            self._role_edits.append((role_edit, name_edit, date_edit))

        sign_group.setLayout(sign_layout)
        layout.addWidget(sign_group)

        # ── Эмблема организации ──
        emblem_group = QGroupBox("Эмблема организации")
        emblem_layout = QVBoxLayout()

        self.emblem_check = QCheckBox("Показывать эмблему вместо текста организации")
        emblem_layout.addWidget(self.emblem_check)

        emblem_btn_layout = QHBoxLayout()
        self.emblem_path_edit = QLineEdit()
        self.emblem_path_edit.setPlaceholderText("Путь к файлу (JPEG/PNG)")
        self.emblem_path_edit.setReadOnly(True)
        emblem_btn_layout.addWidget(self.emblem_path_edit)

        btn_browse = QPushButton("Обзор...")
        btn_browse.clicked.connect(self._browse_emblem)
        emblem_btn_layout.addWidget(btn_browse)

        emblem_layout.addLayout(emblem_btn_layout)

        self.emblem_hint = QLabel("Рекомендуемое разрешение: 300+ DPI, формат PNG/JPEG")
        self.emblem_hint.setStyleSheet("color: #888; font-size: 10px;")
        emblem_layout.addWidget(self.emblem_hint)

        emblem_group.setLayout(emblem_layout)
        layout.addWidget(emblem_group)

        # ── Кнопка сброса ──
        btn_reset = QPushButton("Сбросить все настройки")
        btn_reset.setToolTip("Очистить все поля и вернуть значения по умолчанию")
        btn_reset.clicked.connect(self.reset_to_defaults)
        layout.addWidget(btn_reset)

        layout.addStretch()

        # Сигналы
        self.format_combo.currentIndexChanged.connect(self.settings_changed)
        self.orientation_combo.currentIndexChanged.connect(self.settings_changed)

    def _browse_emblem(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл эмблемы", "",
            "Изображения (*.png *.jpg *.jpeg *.bmp);;Все файлы (*)"
        )
        if path:
            self.emblem_path_edit.setText(path)

    def get_stamp_info(self) -> StampInfo:
        roles = []
        for role_edit, name_edit, date_edit in self._role_edits:
            # Маска "99.99.99" возвращает ".." при пустом поле — фильтруем
            raw_date = date_edit.text().replace(".", "").strip()
            date_val = date_edit.text() if raw_date else ""
            roles.append(StampRole(
                role_name=role_edit.text(),
                person_name=name_edit.text(),
                date=date_val,
            ))

        emblem_path = self.emblem_path_edit.text()
        use_emblem = self.emblem_check.isChecked()
        # Сбрасываем эмблему если файл не существует
        if use_emblem and emblem_path:
            if not os.path.exists(emblem_path):
                emblem_path = ""
                use_emblem = False

        return StampInfo(
            designation=self.designation_edit.text(),
            organization=self.organization_edit.text(),
            building_name=self.building_edit.text(),
            sheet_title=self.sheet_title_edit.text(),
            user_field=self.user_field_edit.text(),
            stage=self.stage_combo.currentText(),
            emblem_path=emblem_path,
            use_emblem=use_emblem,
            roles=roles,
        )

    def get_page_format(self) -> PageFormat:
        return self.format_combo.currentData()

    def get_orientation(self) -> Orientation:
        return self.orientation_combo.currentData()

    def get_font_name(self) -> str:
        font_map = {
            "Arial": "arial",
            "Times New Roman": "times",
            "ISOCPEUR (ГОСТ)": "isocpeur",
        }
        return font_map.get(self.font_combo.currentText(), "arial")

    def reset_to_defaults(self):
        """Сбрасывает все поля к значениям по умолчанию."""
        self.format_combo.setCurrentIndex(0)
        self.orientation_combo.setCurrentIndex(0)
        self.designation_edit.clear()
        self.organization_edit.clear()
        self.building_edit.clear()
        self.sheet_title_edit.clear()
        self.user_field_edit.clear()
        self.stage_combo.setCurrentIndex(0)
        self.font_combo.setCurrentIndex(0)
        self.emblem_path_edit.clear()
        self.emblem_check.setChecked(False)

        default_roles = ["Разраб.", "Пров.", "Н.контр.", "Утв.", ""]
        for i, (role_edit, name_edit, date_edit) in enumerate(self._role_edits):
            role_edit.setText(default_roles[i] if i < len(default_roles) else "")
            name_edit.clear()
            date_edit.clear()

        # Очищаем сохранённые настройки
        s = QSettings("GOSTSpecGenerator", "Settings")
        s.clear()

    # ── Сохранение / загрузка настроек ──

    def save_settings(self):
        """Сохраняет все настройки через QSettings."""
        s = QSettings("GOSTSpecGenerator", "Settings")

        s.setValue("format_index", self.format_combo.currentIndex())
        s.setValue("orientation_index", self.orientation_combo.currentIndex())

        s.setValue("designation", self.designation_edit.text())
        s.setValue("organization", self.organization_edit.text())
        s.setValue("building_name", self.building_edit.text())
        s.setValue("sheet_title", self.sheet_title_edit.text())
        s.setValue("user_field", self.user_field_edit.text())
        s.setValue("stage", self.stage_combo.currentText())

        s.setValue("emblem_path", self.emblem_path_edit.text())
        s.setValue("use_emblem", self.emblem_check.isChecked())
        s.setValue("font_index", self.font_combo.currentIndex())

        for i, (role_edit, name_edit, date_edit) in enumerate(self._role_edits):
            s.setValue(f"role_{i}_name", role_edit.text())
            s.setValue(f"role_{i}_person", name_edit.text())
            s.setValue(f"role_{i}_date", date_edit.text())

    def load_settings(self):
        """Загружает настройки из QSettings."""
        s = QSettings("GOSTSpecGenerator", "Settings")

        idx = s.value("format_index", 0, type=int)
        if 0 <= idx < self.format_combo.count():
            self.format_combo.setCurrentIndex(idx)

        idx = s.value("orientation_index", 0, type=int)
        if 0 <= idx < self.orientation_combo.count():
            self.orientation_combo.setCurrentIndex(idx)

        self.designation_edit.setText(s.value("designation", "", type=str))
        self.organization_edit.setText(s.value("organization", "", type=str))
        self.building_edit.setText(s.value("building_name", "", type=str))
        self.sheet_title_edit.setText(s.value("sheet_title", "", type=str))
        self.user_field_edit.setText(s.value("user_field", "", type=str))

        stage = s.value("stage", "", type=str)
        if stage:
            idx = self.stage_combo.findText(stage)
            if idx >= 0:
                self.stage_combo.setCurrentIndex(idx)
            else:
                self.stage_combo.setEditText(stage)

        self.emblem_path_edit.setText(s.value("emblem_path", "", type=str))
        self.emblem_check.setChecked(s.value("use_emblem", False, type=bool))

        font_idx = s.value("font_index", 0, type=int)
        if 0 <= font_idx < self.font_combo.count():
            self.font_combo.setCurrentIndex(font_idx)

        for i, (role_edit, name_edit, date_edit) in enumerate(self._role_edits):
            role_edit.setText(s.value(f"role_{i}_name", role_edit.text(), type=str))
            name_edit.setText(s.value(f"role_{i}_person", "", type=str))
            date_edit.setText(s.value(f"role_{i}_date", "", type=str))
