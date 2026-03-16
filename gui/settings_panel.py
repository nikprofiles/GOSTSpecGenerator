"""
Панель настроек: штамп, формат, роли с датами, эмблема организации.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLineEdit, QComboBox,
    QGroupBox, QLabel, QGridLayout, QPushButton, QFileDialog, QCheckBox,
    QScrollArea,
)
from PySide6.QtCore import Signal

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
        self.user_field_edit.setPlaceholderText("Заполняется пользователем")
        stamp_layout.addRow("Доп. поле:", self.user_field_edit)

        self.stage_combo = QComboBox()
        self.stage_combo.addItems(["Р", "П", "РП", "И"])
        self.stage_combo.setEditable(True)
        stamp_layout.addRow("Стадия:", self.stage_combo)

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
            roles.append(StampRole(
                role_name=role_edit.text(),
                person_name=name_edit.text(),
                date=date_edit.text(),
            ))

        return StampInfo(
            designation=self.designation_edit.text(),
            organization=self.organization_edit.text(),
            building_name=self.building_edit.text(),
            sheet_title=self.sheet_title_edit.text(),
            user_field=self.user_field_edit.text(),
            stage=self.stage_combo.currentText(),
            emblem_path=self.emblem_path_edit.text(),
            use_emblem=self.emblem_check.isChecked(),
            roles=roles,
        )

    def get_page_format(self) -> PageFormat:
        return self.format_combo.currentData()

    def get_orientation(self) -> Orientation:
        return self.orientation_combo.currentData()
