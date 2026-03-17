"""
Модели данных: спецификация, штамп, форматы.
"""

from dataclasses import dataclass, field
from enum import Enum


class PageFormat(Enum):
    A4 = (210, 297)
    A3 = (297, 420)
    A2 = (420, 594)
    A1 = (594, 841)


class Orientation(Enum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class RowType(Enum):
    """Тип строки спецификации."""
    DATA = "data"               # Обычные данные (3+ заполненных колонок)
    CATEGORY = "category"       # Категория 1-го уровня ("Этаж -1") — жирный
    SUBCATEGORY = "subcategory"  # Подкатегория 2-го уровня ("1. Низковольтное") — курсив


@dataclass
class StampRole:
    role_name: str = ""
    person_name: str = ""
    date: str = ""          # Дата напротив роли


@dataclass
class StampInfo:
    designation: str = ""
    organization: str = ""
    building_name: str = ""
    sheet_title: str = ""
    user_field: str = ""
    stage: str = "Р"
    emblem_path: str = ""       # Путь к файлу эмблемы (JPEG/PNG)
    use_emblem: bool = False    # Показывать эмблему вместо текста организации
    roles: list[StampRole] = field(default_factory=lambda: [
        StampRole(role_name="Разраб."),
        StampRole(role_name="Пров."),
        StampRole(role_name="Н.контр."),
        StampRole(role_name="Утв."),
        StampRole(role_name=""),
    ])


@dataclass
class SpecificationRow:
    """Одна строка спецификации — 9 колонок + тип строки."""
    position: str = ""
    name: str = ""
    type_brand: str = ""
    product_code: str = ""
    supplier: str = ""
    unit: str = "шт."
    quantity: str = ""
    mass_unit_kg: str = ""
    notes: str = ""
    row_type: RowType = RowType.DATA

    def to_row_values(self) -> list[str]:
        return [
            self.position, self.name, self.type_brand, self.product_code,
            self.supplier, self.unit, self.quantity, self.mass_unit_kg, self.notes,
        ]

    def display_text(self) -> str:
        """Текст для объединённой строки (категория/подкатегория)."""
        parts = [self.position, self.name]
        return " ".join(p for p in parts if p).strip()


@dataclass
class SpecificationDocument:
    stamp: StampInfo = field(default_factory=StampInfo)
    rows: list[SpecificationRow] = field(default_factory=list)
    page_format: PageFormat = PageFormat.A4
    orientation: Orientation = Orientation.PORTRAIT
    font_name: str = "Arial"

    def get_page_size_mm(self) -> tuple[float, float]:
        w, h = self.page_format.value
        if self.orientation == Orientation.LANDSCAPE:
            w, h = h, w
        return w, h
