"""
Модуль автонумерации позиций спецификации.

Логика:
- Категория (CATEGORY) — НЕ нумеруется
- Подкатегория (SUBCATEGORY) — сквозной номер: 1, 2, 3...
  Если уже есть номер (напр. "1" из Excel) — используем его
- Данные (DATA) — N.M где N = номер текущей подкатегории, M = счётчик
  ВСЕГДА перенумеровываем данные внутри подкатегории
"""

from core.data_model import SpecificationRow, RowType


def autonumber(rows: list[SpecificationRow]) -> list[SpecificationRow]:
    """Автонумерация: подкатегории и данные."""
    if not rows:
        return rows

    section_num = 0       # текущий номер подкатегории
    section_label = ""    # строковое представление номера подкатегории
    item_num = 0          # счётчик данных внутри подкатегории
    in_section = False

    for row in rows:
        if row.row_type == RowType.CATEGORY:
            in_section = False
            item_num = 0
            # Категория — позицию не трогаем (или очищаем)
            continue

        elif row.row_type == RowType.SUBCATEGORY:
            item_num = 0
            in_section = True

            if row.position.strip():
                # У подкатегории уже есть номер из Excel — используем его
                section_label = row.position.strip()
                # Пытаемся извлечь числовой номер для инкремента
                try:
                    section_num = int(section_label.split(".")[0])
                except ValueError:
                    section_num += 1
            else:
                # Автоприсваиваем номер
                section_num += 1
                section_label = str(section_num)
                row.position = section_label
            continue

        elif row.row_type == RowType.DATA:
            if in_section and section_label:
                item_num += 1
                row.position = f"{section_label}.{item_num}"
            elif not row.position.strip():
                # Нет подкатегории — простая нумерация
                item_num += 1
                row.position = str(item_num)
            # Если позиция есть и нет подкатегории — не трогаем

    return rows


def needs_autonumber(rows: list[SpecificationRow]) -> bool:
    """Проверяет, нужна ли автонумерация."""
    return any(
        not r.position.strip() and r.row_type in (RowType.DATA, RowType.SUBCATEGORY)
        for r in rows
    )
