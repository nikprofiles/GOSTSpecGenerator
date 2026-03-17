"""
Модуль автонумерации позиций спецификации.

3-уровневая иерархия:
- Категория (CATEGORY)       → 1, 2, 3...          (жирный)
- Подкатегория (SUBCATEGORY)  → 1.1, 1.2, 2.1...    (курсив)
- Данные (DATA)               → 1.1.1, 1.1.2...     (обычный)

Если DATA идёт без SUBCATEGORY → cat.item (1.1, 1.2...)
Если DATA идёт без CATEGORY   → простой номер (1, 2, 3...)
"""

from core.data_model import SpecificationRow, RowType


def autonumber(rows: list[SpecificationRow]) -> list[SpecificationRow]:
    """Автонумерация: 3-уровневая иерархия."""
    if not rows:
        return rows

    cat_num = 0         # номер текущей категории
    sub_num = 0         # номер текущей подкатегории внутри категории
    item_num = 0        # номер данных внутри подкатегории
    in_category = False
    in_subcategory = False

    for row in rows:
        if row.row_type == RowType.CATEGORY:
            cat_num += 1
            sub_num = 0
            item_num = 0
            in_category = True
            in_subcategory = False
            row.position = str(cat_num)

        elif row.row_type == RowType.SUBCATEGORY:
            item_num = 0
            in_subcategory = True

            if in_category:
                sub_num += 1
                row.position = f"{cat_num}.{sub_num}"
            else:
                # Подкатегория без категории — простая нумерация
                sub_num += 1
                row.position = str(sub_num)

        elif row.row_type == RowType.DATA:
            item_num += 1

            if in_subcategory and in_category:
                # 3-уровневая: cat.sub.item
                row.position = f"{cat_num}.{sub_num}.{item_num}"
            elif in_category and not in_subcategory:
                # 2-уровневая: cat.item (данные без подкатегории)
                row.position = f"{cat_num}.{item_num}"
            elif in_subcategory and not in_category:
                # 2-уровневая: sub.item (подкатегория без категории)
                row.position = f"{sub_num}.{item_num}"
            else:
                # Простая нумерация (без категории и подкатегории)
                row.position = str(item_num)

    return rows


def needs_autonumber(rows: list[SpecificationRow]) -> bool:
    """Проверяет, нужна ли автонумерация."""
    return any(
        not r.position.strip() and r.row_type in (RowType.DATA, RowType.SUBCATEGORY, RowType.CATEGORY)
        for r in rows
    )
