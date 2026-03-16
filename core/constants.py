"""
Все размеры по ГОСТ 21.101 / ГОСТ 21.110 в миллиметрах.
Конвертация в points для ReportLab.
"""

# ── Конвертация мм → points ──────────────────────────────────────────

MM = 2.834645669  # 1 мм = 72 / 25.4 points


def mm(value: float) -> float:
    """Перевод миллиметров в ReportLab points."""
    return value * MM


# ── Форматы листов (ширина, высота в мм, книжная ориентация) ─────────

PAGE_FORMATS = {
    "A4": (210, 297),
    "A3": (420, 297),
    "A2": (594, 420),
    "A1": (841, 594),
}

# ── Отступы рамки (ГОСТ 21.101) ─────────────────────────────────────

FRAME_MARGIN_LEFT = 20    # мм
FRAME_MARGIN_TOP = 5      # мм
FRAME_MARGIN_RIGHT = 5    # мм
FRAME_MARGIN_BOTTOM = 5   # мм

# ── Толщина линий ────────────────────────────────────────────────────

LINE_WIDTH_FRAME = 0.7        # мм — внешняя рамка
LINE_WIDTH_INNER = 0.35       # мм — внутренние линии таблицы и штампа
LINE_WIDTH_THIN = 0.18        # мм — тонкие разделители

# ══════════════════════════════════════════════════════════════════════
# ШТАМП ПЕРВОГО ЛИСТА (Форма 3) — по скриншоту 3
# Размер: 185 × 55 мм
# ══════════════════════════════════════════════════════════════════════

STAMP_F3_WIDTH = 185   # мм
STAMP_F3_HEIGHT = 55   # мм

# ── Левый блок (таблица изменений + подписи) ──
# 6 колонок: Изм.(10) + Кол.уч.(10) + Лист(10) + №док.(10) + Подп.(15) + Дата(10) = 65мм
STAMP_F3_LEFT_W = 65   # мм
STAMP_F3_LEFT_COLS = [10, 10, 10, 10, 15, 10]  # ширины колонок
STAMP_F3_LEFT_LABELS = ["Изм.", "Кол.уч.", "Лист", "№ док.", "Подп.", "Дата"]

# Строки левого блока: 5 строк ролей + 1 строка заголовков + пустые строки сверху
# Высота каждой строки: 5 мм
STAMP_F3_ROW_H = 5   # мм

# Роли по умолчанию (пользователь может менять в GUI) — снизу вверх
STAMP_F3_DEFAULT_ROLES = ["Н.контр.", "Разраб.", "Консульт.", "Руковод.", "Зав.каф."]
STAMP_F3_ROLE_ROWS = 5   # количество строк под роли

# ── Правый блок (120мм = 185 - 65) ──
STAMP_F3_RIGHT_W = 120  # мм

# Правый блок: высоты секций СВЕРХУ ВНИЗ
STAMP_F3_AREA1_H = 10   # (1) — обозначение документа
STAMP_F3_AREA2_H = 15   # (2) — название организации
STAMP_F3_AREA3_H = 15   # (3) — название объекта, справа: Стадия/Лист/Листов labels
STAMP_F3_AREA4_H = 15   # (4) нижняя левая + (5) нижняя правая

# Нижняя правая часть правого блока: Стадия(15) + Лист(15) + Листов(20) = 50мм
STAMP_F3_STAGE_W = 15
STAMP_F3_SHEET_W = 15
STAMP_F3_SHEETS_TOTAL_W = 20
STAMP_F3_BOTTOM_RIGHT_W = 50  # мм (15+15+20)

# ══════════════════════════════════════════════════════════════════════
# ШТАМП ПОСЛЕДУЮЩИХ ЛИСТОВ (Форма 2а) — по скриншоту 4
# Левый блок: 65мм (те же 6 колонок), 3 строки × 5мм = 15мм высота
# Правый блок: 110мм для обозначения (1) + 10мм для Лист/Формат
# ══════════════════════════════════════════════════════════════════════

STAMP_F2A_WIDTH = 185   # мм
STAMP_F2A_HEIGHT = 15   # мм (3 строки × 5мм)
STAMP_F2A_LEFT_W = 65   # мм
STAMP_F2A_LEFT_COLS = [10, 10, 10, 10, 15, 10]  # те же что и F3
STAMP_F2A_LEFT_LABELS = ["Изм.", "Кол.уч.", "Лист", "№ док.", "Подп.", "Дата"]
STAMP_F2A_RIGHT_DESIG_W = 110  # мм — обозначение (1)
STAMP_F2A_RIGHT_EDGE_W = 10    # мм — Лист(7мм) + Формат(8мм)
STAMP_F2A_SHEET_H = 7   # мм — высота ячейки "Лист"
STAMP_F2A_FORMAT_H = 8  # мм — высота ячейки "Формат"
STAMP_F2A_ROW_H = 5     # мм

# ══════════════════════════════════════════════════════════════════════
# ТАБЛИЦА СПЕЦИФИКАЦИИ — 9 колонок
# ══════════════════════════════════════════════════════════════════════

TABLE_HEADER_HEIGHT = 15    # мм — высота заголовка
ROW_MIN_HEIGHT = 8          # мм — минимальная высота строки данных
CELL_PADDING = 1            # мм — отступ текста от границ ячейки

# 9 колонок, суммарно 185 мм (для А4)
COL_ORDER = [
    "pos", "name", "type_brand", "product_code", "supplier",
    "unit", "quantity", "mass_unit", "notes",
]

BASE_COL_WIDTHS = {
    "pos":          10,   # 1. Поз.
    "name":         50,   # 2. Наименование и техническая характеристика
    "type_brand":   30,   # 3. Тип, марка, обозначение документа, опросного листа
    "product_code": 18,   # 4. Код продукции
    "supplier":     22,   # 5. Поставщик
    "unit":         10,   # 6. Ед. измерения
    "quantity":     12,   # 7. Кол.
    "mass_unit":    15,   # 8. Масса 1 ед., кг
    "notes":        18,   # 9. Примечание
}
# Сумма: 10+50+30+18+22+10+12+15+18 = 185

COL_HEADERS = {
    "pos":          "Поз.",
    "name":         "Наименование и\nтехническая\nхарактеристика",
    "type_brand":   "Тип, марка,\nобозначение\nдокумента,\nопросного листа",
    "product_code": "Код\nпродукции",
    "supplier":     "Поставщик",
    "unit":         "Ед.\nизм.",
    "quantity":     "Кол.",
    "mass_unit":    "Масса\n1 ед., кг",
    "notes":        "Примечание",
}

# Колонки с фиксированной шириной (не масштабируются на больших форматах)
FIXED_WIDTH_COLS = {"pos", "unit", "quantity", "mass_unit"}

# ── Шрифты ───────────────────────────────────────────────────────────

FONT_NAME = "GOST"
FONT_NAME_ITALIC = "GOST-Italic"
FONT_FALLBACK = "DejaVuSans"

FONT_SIZE_HEADER = 8     # pt — заголовок таблицы
FONT_SIZE_DATA = 7       # pt — данные ячеек
FONT_SIZE_STAMP_LABEL = 7    # pt — подписи в штампе
FONT_SIZE_STAMP_VALUE = 10   # pt — значения в штампе
FONT_SIZE_STAMP_SMALL = 6    # pt — мелкий текст штампа


def drawable_area(page_w_mm: float, page_h_mm: float) -> tuple[float, float, float, float]:
    """(x, y, width, height) рабочей области внутри рамки в мм."""
    x = FRAME_MARGIN_LEFT
    y = FRAME_MARGIN_BOTTOM
    w = page_w_mm - FRAME_MARGIN_LEFT - FRAME_MARGIN_RIGHT
    h = page_h_mm - FRAME_MARGIN_TOP - FRAME_MARGIN_BOTTOM
    return x, y, w, h


def table_area(page_w_mm: float, page_h_mm: float, is_first_page: bool) -> tuple[float, float, float, float]:
    """(x_mm, y_top_mm, width_mm, available_height_mm) области таблицы."""
    x, _, w, _ = drawable_area(page_w_mm, page_h_mm)
    y_top = page_h_mm - FRAME_MARGIN_TOP

    if is_first_page:
        stamp_top = FRAME_MARGIN_BOTTOM + STAMP_F3_HEIGHT
    else:
        stamp_top = FRAME_MARGIN_BOTTOM + STAMP_F2A_HEIGHT

    available_h = y_top - stamp_top
    return x, y_top, w, available_h


def scale_col_widths(drawable_width_mm: float) -> list[float]:
    """Масштабирует ширины колонок под доступную ширину."""
    base_total = sum(BASE_COL_WIDTHS[c] for c in COL_ORDER)
    if abs(drawable_width_mm - base_total) < 0.1:
        return [BASE_COL_WIDTHS[c] for c in COL_ORDER]

    fixed_total = sum(BASE_COL_WIDTHS[c] for c in FIXED_WIDTH_COLS)
    expandable_total = base_total - fixed_total
    extra = drawable_width_mm - base_total
    scale = (expandable_total + extra) / expandable_total

    result = []
    for col in COL_ORDER:
        if col in FIXED_WIDTH_COLS:
            result.append(BASE_COL_WIDTHS[col])
        else:
            result.append(round(BASE_COL_WIDTHS[col] * scale, 1))
    return result
