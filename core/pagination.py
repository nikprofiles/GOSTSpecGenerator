"""
Разбиение строк спецификации по страницам с учётом переноса текста.
"""

from reportlab.lib.utils import simpleSplit

from core.constants import (
    mm, MM,
    ROW_MIN_HEIGHT, CELL_PADDING, TABLE_HEADER_HEIGHT,
    COL_ORDER, FONT_NAME, FONT_SIZE_DATA,
    FRAME_MARGIN_TOP, FRAME_MARGIN_BOTTOM,
    STAMP_F3_HEIGHT, STAMP_F2A_HEIGHT,
)
from core.data_model import SpecificationRow


def calc_cell_height_mm(text: str, col_width_mm: float,
                        font_name: str = FONT_NAME,
                        font_size: float = FONT_SIZE_DATA) -> float:
    """
    Рассчитывает необходимую высоту ячейки в мм с учётом переноса текста.
    """
    if not text:
        return ROW_MIN_HEIGHT

    available_width_pt = mm(col_width_mm) - 2 * mm(CELL_PADDING)
    if available_width_pt <= 0:
        return ROW_MIN_HEIGHT

    lines = simpleSplit(text, font_name, font_size, available_width_pt)
    line_height_mm = (font_size * 1.2) / MM
    text_height = len(lines) * line_height_mm + 2 * CELL_PADDING
    return max(ROW_MIN_HEIGHT, text_height)


def calc_row_height(row: SpecificationRow, col_widths: list[float],
                    font_name: str = FONT_NAME,
                    font_size: float = FONT_SIZE_DATA) -> float:
    """
    Рассчитывает высоту строки в мм — максимум по всем ячейкам.
    """
    values = row.to_row_values()
    max_h = ROW_MIN_HEIGHT

    for i, val in enumerate(values):
        if i < len(col_widths):
            h = calc_cell_height_mm(val, col_widths[i], font_name, font_size)
            if h > max_h:
                max_h = h

    return max_h


def available_height(page_h_mm: float, is_first_page: bool) -> float:
    """
    Доступная высота для данных таблицы (без заголовка) в мм.
    """
    y_top = page_h_mm - FRAME_MARGIN_TOP
    if is_first_page:
        y_bottom = FRAME_MARGIN_BOTTOM + STAMP_F3_HEIGHT
    else:
        y_bottom = FRAME_MARGIN_BOTTOM + STAMP_F2A_HEIGHT

    return y_top - y_bottom - TABLE_HEADER_HEIGHT


def paginate(rows: list[SpecificationRow],
             col_widths: list[float],
             page_h_mm: float,
             font_name: str = FONT_NAME,
             font_size: float = FONT_SIZE_DATA) -> list[list[SpecificationRow]]:
    """
    Разбивает строки по страницам.
    Возвращает список страниц, каждая — список строк.
    """
    if not rows:
        return [[]]  # одна пустая страница для рамки и штампа

    pages: list[list[SpecificationRow]] = []
    current_page: list[SpecificationRow] = []
    is_first = True
    remaining_h = available_height(page_h_mm, is_first)

    for row in rows:
        row_h = calc_row_height(row, col_widths, font_name, font_size)

        if row_h > remaining_h and current_page:
            # Текущая страница заполнена — начинаем новую
            pages.append(current_page)
            current_page = []
            is_first = False
            remaining_h = available_height(page_h_mm, is_first)

        current_page.append(row)
        remaining_h -= row_h

    if current_page:
        pages.append(current_page)

    return pages
