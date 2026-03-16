"""
Отрисовка ГОСТ-элементов на ReportLab Canvas:
- Рамка листа (ГОСТ 21.101)
- Штамп первого листа (Форма 3, 185×55мм)
- Штамп последующих листов (Форма 2а, 185×15мм)
- Надпись "Формат" под рамкой
- Заголовок таблицы спецификации (9 колонок)
"""

from reportlab.pdfgen.canvas import Canvas

from core.constants import (
    mm,
    FRAME_MARGIN_LEFT, FRAME_MARGIN_TOP, FRAME_MARGIN_RIGHT, FRAME_MARGIN_BOTTOM,
    LINE_WIDTH_FRAME, LINE_WIDTH_INNER,
    STAMP_F3_WIDTH, STAMP_F3_HEIGHT,
    STAMP_F3_LEFT_W, STAMP_F3_LEFT_COLS, STAMP_F3_LEFT_LABELS,
    STAMP_F3_ROW_H, STAMP_F3_ROLE_ROWS,
    STAMP_F3_RIGHT_W,
    STAMP_F3_AREA1_H, STAMP_F3_AREA2_H, STAMP_F3_AREA3_H, STAMP_F3_AREA4_H,
    STAMP_F3_STAGE_W, STAMP_F3_SHEET_W, STAMP_F3_SHEETS_TOTAL_W, STAMP_F3_BOTTOM_RIGHT_W,
    STAMP_F2A_WIDTH, STAMP_F2A_HEIGHT,
    STAMP_F2A_LEFT_W, STAMP_F2A_LEFT_COLS, STAMP_F2A_LEFT_LABELS,
    STAMP_F2A_RIGHT_DESIG_W, STAMP_F2A_RIGHT_EDGE_W,
    STAMP_F2A_SHEET_H, STAMP_F2A_FORMAT_H, STAMP_F2A_ROW_H,
    TABLE_HEADER_HEIGHT, COL_ORDER, COL_HEADERS,
    FONT_NAME, FONT_SIZE_HEADER, FONT_SIZE_STAMP_LABEL,
    FONT_SIZE_STAMP_VALUE, FONT_SIZE_STAMP_SMALL,
)
from core.data_model import StampInfo


# ── Утилиты ──────────────────────────────────────────────────────────

def _lw(c: Canvas, width_mm: float):
    c.setLineWidth(mm(width_mm))


def _font(c: Canvas, size: float):
    """Установить шрифт, с fallback."""
    try:
        c.setFont(FONT_NAME, size)
        return FONT_NAME
    except KeyError:
        c.setFont("Helvetica", size)
        return "Helvetica"


def _fit_text(c: Canvas, text: str, max_width_mm: float, font_size: float) -> str:
    """
    Автосокращение текста: если не влезает, убирает буквы с конца + ".".
    Возвращает текст, который гарантированно влезает в max_width_mm.
    """
    if not text:
        return ""
    fn = _font(c, font_size)
    max_w_pt = mm(max_width_mm)
    if c.stringWidth(text, fn, font_size) <= max_w_pt:
        return text
    # Сокращаем: убираем по букве, пока не влезет
    for cut in range(1, len(text)):
        shortened = text[:len(text) - cut] + "."
        if c.stringWidth(shortened, fn, font_size) <= max_w_pt:
            return shortened
    return text[0] + "."  # крайний случай


def _text_center(c: Canvas, x_mm: float, y_mm: float, w_mm: float, h_mm: float,
                 text: str, font_size: float = FONT_SIZE_STAMP_LABEL, auto_fit: bool = False):
    """Текст по центру прямоугольника. auto_fit=True — автосокращение + clipping."""
    if not text:
        return
    fn = _font(c, font_size)
    if auto_fit:
        text = _fit_text(c, text, w_mm - 1, font_size)
    tw = c.stringWidth(text, fn, font_size)
    tx = mm(x_mm + w_mm / 2) - tw / 2
    ty = mm(y_mm + h_mm / 2) - font_size * 0.35
    # Clip: не даём тексту вылезать за ячейку
    c.saveState()
    p = c.beginPath()
    p.rect(mm(x_mm), mm(y_mm), mm(w_mm), mm(h_mm))
    c.clipPath(p, stroke=0)
    c.drawString(tx, ty, text)
    c.restoreState()


def _text_left(c: Canvas, x_mm: float, y_mm: float, w_mm: float, h_mm: float,
               text: str, font_size: float = FONT_SIZE_STAMP_LABEL, pad_mm: float = 1,
               auto_fit: bool = False):
    """Текст с левым выравниванием + clipping."""
    if not text:
        return
    fn = _font(c, font_size)
    if auto_fit:
        text = _fit_text(c, text, w_mm - pad_mm - 0.5, font_size)
    tx = mm(x_mm + pad_mm)
    ty = mm(y_mm + h_mm / 2) - font_size * 0.35
    c.saveState()
    p = c.beginPath()
    p.rect(mm(x_mm), mm(y_mm), mm(w_mm), mm(h_mm))
    c.clipPath(p, stroke=0)
    c.drawString(tx, ty, text)
    c.restoreState()


def _text_multiline_center(c: Canvas, x_mm: float, y_mm: float, w_mm: float, h_mm: float,
                            text: str, font_size: float = FONT_SIZE_STAMP_VALUE,
                            auto_fit: bool = False, auto_scale: bool = True):
    """Многострочный текст по центру. auto_scale=True — уменьшает шрифт если не влезает."""
    if not text:
        return

    max_w_pt = mm(w_mm - 2)  # доступная ширина с отступами
    max_h_pt = mm(h_mm - 1)  # доступная высота

    # Авто-перенос по словам: разбиваем длинные строки
    from reportlab.lib.utils import simpleSplit

    # Автомасштабирование: уменьшаем шрифт пока текст не влезет
    current_size = font_size
    while current_size >= 4:
        fn = _font(c, current_size)
        # Разбиваем текст на строки с учётом переносов
        raw_lines = text.split("\n")
        all_lines = []
        for raw in raw_lines:
            split = simpleSplit(raw, fn, current_size, max_w_pt)
            all_lines.extend(split if split else [""])

        line_h = current_size * 1.2
        total_h = len(all_lines) * line_h

        if total_h <= max_h_pt or not auto_scale:
            break
        current_size -= 0.5

    fn = _font(c, current_size)
    line_h = current_size * 1.2
    total = len(all_lines) * line_h
    start_y = mm(y_mm + h_mm / 2) + total / 2 - line_h * 0.7

    # Clipping
    c.saveState()
    p = c.beginPath()
    p.rect(mm(x_mm), mm(y_mm), mm(w_mm), mm(h_mm))
    c.clipPath(p, stroke=0)

    for i, line in enumerate(all_lines):
        tw = c.stringWidth(line, fn, current_size)
        tx = mm(x_mm + w_mm / 2) - tw / 2
        ty = start_y - i * line_h
        c.drawString(tx, ty, line)

    c.restoreState()


# ══════════════════════════════════════════════════════════════════════
# РАМКА
# ══════════════════════════════════════════════════════════════════════

def draw_frame(c: Canvas, page_w_mm: float, page_h_mm: float):
    """Внешняя рамка листа по ГОСТ 21.101."""
    _lw(c, LINE_WIDTH_FRAME)
    x0, y0 = mm(FRAME_MARGIN_LEFT), mm(FRAME_MARGIN_BOTTOM)
    x1, y1 = mm(page_w_mm - FRAME_MARGIN_RIGHT), mm(page_h_mm - FRAME_MARGIN_TOP)
    c.rect(x0, y0, x1 - x0, y1 - y0, stroke=1, fill=0)


def draw_format_label(c: Canvas, page_w_mm: float, page_h_mm: float, format_name: str):
    """
    Надпись 'Формат А3' ПОД рамкой — в нижнем поле 5мм,
    справа, между рамкой и краем бумаги.
    """
    if not format_name:
        return
    text = f"Формат {format_name}"
    font_size = FONT_SIZE_STAMP_SMALL
    fn = _font(c, font_size)

    # Позиция: правый нижний угол, под рамкой
    # Рамка заканчивается на y = FRAME_MARGIN_BOTTOM = 5мм
    # Текст рисуем в полосе от 0 до 5мм от низа, справа
    tw = c.stringWidth(text, fn, font_size)
    tx = mm(page_w_mm - FRAME_MARGIN_RIGHT) - tw - mm(1)  # 1мм отступ от правого края рамки
    ty = mm(1)  # 1мм от нижнего края бумаги
    c.drawString(tx, ty, text)


# ══════════════════════════════════════════════════════════════════════
# ШТАМП ПЕРВОГО ЛИСТА (Форма 3) — 185×55мм
#
# Правый блок (120мм) сверху вниз:
#   (1) обозначение  — 10мм
#   (2) организация  — 15мм (БЫЛО: отдельная, ТЕПЕРЬ: нижняя правая зона)
#   (3) объект       — 15мм  |  справа: Стадия/Лист/Листов (50мм)
#   (4) содержание   — 15мм  |  справа: организация (50мм) — ОДНА ячейка
#
# Стадия/Лист/Листов — ТОЛЬКО в зоне (3), НЕ дублируется
# Нижняя правая 50мм — организация
# ══════════════════════════════════════════════════════════════════════

def draw_stamp_form3(c: Canvas, page_w_mm: float, page_h_mm: float,
                     stamp: StampInfo, sheet_num: int = 1, total_sheets: int = 1):
    """Штамп первого листа (185×55мм)."""
    import os

    sx = page_w_mm - FRAME_MARGIN_RIGHT - STAMP_F3_WIDTH
    sy = FRAME_MARGIN_BOTTOM
    rh = STAMP_F3_ROW_H  # 5мм

    _lw(c, LINE_WIDTH_INNER)

    # Внешний прямоугольник
    c.rect(mm(sx), mm(sy), mm(STAMP_F3_WIDTH), mm(STAMP_F3_HEIGHT), stroke=1, fill=0)

    left_right_x = sx + STAMP_F3_LEFT_W
    right_end_x = sx + STAMP_F3_WIDTH
    top_y = sy + STAMP_F3_HEIGHT

    # ══ ПРАВЫЙ БЛОК (120мм) ══
    y1 = top_y - STAMP_F3_AREA1_H           # низ зоны (1)
    y2 = y1 - STAMP_F3_AREA2_H              # низ зоны (2)
    y3 = y2 - STAMP_F3_AREA3_H              # низ зоны (3)

    c.line(mm(left_right_x), mm(y1), mm(right_end_x), mm(y1))
    c.line(mm(left_right_x), mm(y2), mm(right_end_x), mm(y2))
    c.line(mm(left_right_x), mm(y3), mm(right_end_x), mm(y3))
    c.line(mm(left_right_x), mm(sy), mm(left_right_x), mm(top_y))

    # Стадия/Лист/Листов — в зоне (3)
    br_x = right_end_x - STAMP_F3_BOTTOM_RIGHT_W
    c.line(mm(br_x), mm(y3), mm(br_x), mm(y2))
    stage_x = br_x + STAMP_F3_STAGE_W
    sheet_x = stage_x + STAMP_F3_SHEET_W
    c.line(mm(stage_x), mm(y3), mm(stage_x), mm(y2))
    c.line(mm(sheet_x), mm(y3), mm(sheet_x), mm(y2))
    label3_y = y3 + 5
    c.line(mm(br_x), mm(label3_y), mm(right_end_x), mm(label3_y))

    # Организация — нижняя правая
    c.line(mm(br_x), mm(sy), mm(br_x), mm(y3))

    # ══ ЛЕВЫЙ БЛОК (65мм × 55мм) ══
    # Снизу вверх:
    #   Строка 0 (sy → sy+5): Labels "Изм./Кол.уч./Лист/№док./Подп./Дата"
    #   Строки 1-5 (sy+5 → sy+30): Роли (Разраб./Пров./Н.контр./Утв./пусто)
    #   Строки 6-10 (sy+30 → sy+55): Пустые строки с 6 колонками (табл. изменений)
    # Всего 11 строк × 5мм = 55мм — заполняет ВСЮ высоту штампа

    total_rows = int(STAMP_F3_HEIGHT / rh)  # 55/5 = 11 строк
    roles_count = STAMP_F3_ROLE_ROWS  # 5
    labels_count = 1  # 1 строка для "Изм."...
    change_rows = total_rows - roles_count - labels_count  # 11-5-1 = 5 пустых строк сверху

    # Граница ролей/изменений
    roles_top_y = sy + rh * (labels_count + roles_count)  # sy + 30

    # ── Все горизонтальные линии (через каждые 5мм на всю высоту) ──
    for i in range(1, total_rows):
        ry = sy + rh * i
        c.line(mm(sx), mm(ry), mm(left_right_x), mm(ry))

    # ── Вертикальные колонки 6шт в зоне labels + изменений (от sy до roles_top_y) ──
    cx = sx
    for i, col_w in enumerate(STAMP_F3_LEFT_COLS):
        cx += col_w
        if i < len(STAMP_F3_LEFT_COLS) - 1:
            c.line(mm(cx), mm(sy), mm(cx), mm(roles_top_y))

    # ── Также 6 колонок продолжаются ВВЕРХ от roles_top_y до top_y ──
    cx = sx
    for i, col_w in enumerate(STAMP_F3_LEFT_COLS):
        cx += col_w
        if i < len(STAMP_F3_LEFT_COLS) - 1:
            c.line(mm(cx), mm(roles_top_y), mm(cx), mm(top_y))

    # ── Вертикальные линии в зоне ролей: роль(10) | фамилия(20) | дата(35) ──
    role_col1_x = sx + STAMP_F3_LEFT_COLS[0]
    role_col2_x = role_col1_x + STAMP_F3_LEFT_COLS[1] + STAMP_F3_LEFT_COLS[2]

    c.line(mm(role_col1_x), mm(sy + rh), mm(role_col1_x), mm(roles_top_y))
    c.line(mm(role_col2_x), mm(sy + rh), mm(role_col2_x), mm(roles_top_y))

    # ══ ТЕКСТ ══

    # Labels: Изм., Кол.уч., Лист, № док., Подп., Дата
    cx = sx
    for i, label in enumerate(STAMP_F3_LEFT_LABELS):
        w = STAMP_F3_LEFT_COLS[i]
        _text_center(c, cx, sy, w, rh, label, FONT_SIZE_STAMP_SMALL)
        cx += w

    # Роли + фамилии + даты (строки 1-5, от sy+5 до sy+30)
    for i, role in enumerate(stamp.roles):
        if i >= STAMP_F3_ROLE_ROWS:
            break
        row_y = sy + rh * (i + 1)  # строка 1 = sy+5, строка 5 = sy+25
        # Роль (10мм)
        _text_left(c, sx, row_y, STAMP_F3_LEFT_COLS[0], rh,
                   role.role_name, FONT_SIZE_STAMP_SMALL, pad_mm=0.5, auto_fit=True)
        # Фамилия (20мм)
        name_w = STAMP_F3_LEFT_COLS[1] + STAMP_F3_LEFT_COLS[2]
        _text_center(c, role_col1_x, row_y, name_w, rh,
                     role.person_name, FONT_SIZE_STAMP_SMALL, auto_fit=True)
        # Дата (35мм оставшихся = 65-30)
        date_w = STAMP_F3_LEFT_W - STAMP_F3_LEFT_COLS[0] - name_w
        _text_center(c, role_col2_x, row_y, date_w, rh,
                     role.date, FONT_SIZE_STAMP_SMALL, auto_fit=True)

    # Правый блок: тексты
    # (1) Обозначение
    _text_center(c, left_right_x, y1, STAMP_F3_RIGHT_W, STAMP_F3_AREA1_H,
                 stamp.designation, FONT_SIZE_STAMP_VALUE + 2, auto_fit=True)

    # (2) Объект (название здания)
    _text_multiline_center(c, left_right_x, y2, STAMP_F3_RIGHT_W, STAMP_F3_AREA2_H,
                            stamp.building_name, FONT_SIZE_STAMP_VALUE, auto_fit=True)

    # (3) Содержание листа (левая часть)
    obj_w = STAMP_F3_RIGHT_W - STAMP_F3_BOTTOM_RIGHT_W
    _text_multiline_center(c, left_right_x, y3, obj_w, STAMP_F3_AREA3_H,
                            stamp.sheet_title, FONT_SIZE_STAMP_VALUE, auto_fit=True)

    # Стадия/Лист/Листов labels
    _text_center(c, br_x, label3_y, STAMP_F3_STAGE_W, y2 - label3_y,
                 "Стадия", FONT_SIZE_STAMP_SMALL)
    _text_center(c, stage_x, label3_y, STAMP_F3_SHEET_W, y2 - label3_y,
                 "Лист", FONT_SIZE_STAMP_SMALL)
    _text_center(c, sheet_x, label3_y, STAMP_F3_SHEETS_TOTAL_W, y2 - label3_y,
                 "Листов", FONT_SIZE_STAMP_SMALL)

    # Стадия/Лист/Листов values
    _text_center(c, br_x, y3, STAMP_F3_STAGE_W, 5,
                 stamp.stage, FONT_SIZE_STAMP_VALUE)
    _text_center(c, stage_x, y3, STAMP_F3_SHEET_W, 5,
                 str(sheet_num), FONT_SIZE_STAMP_VALUE)
    _text_center(c, sheet_x, y3, STAMP_F3_SHEETS_TOTAL_W, 5,
                 str(total_sheets), FONT_SIZE_STAMP_VALUE)

    # (4) Доп. поле — нижняя ЛЕВАЯ (70мм)
    _text_multiline_center(c, left_right_x, sy, obj_w, STAMP_F3_AREA4_H,
                            stamp.user_field, FONT_SIZE_STAMP_VALUE, auto_fit=True)

    # Организация / Эмблема — нижняя ПРАВАЯ (50мм)
    if stamp.use_emblem and stamp.emblem_path and os.path.exists(stamp.emblem_path):
        # Вставляем изображение, масштабируя пропорционально
        try:
            from reportlab.lib.utils import ImageReader
            img = ImageReader(stamp.emblem_path)
            iw, ih = img.getSize()
            # Доступная зона
            max_w = mm(STAMP_F3_BOTTOM_RIGHT_W - 2)  # 2мм padding
            max_h = mm(STAMP_F3_AREA4_H - 2)
            # Пропорциональное масштабирование
            scale = min(max_w / iw, max_h / ih)
            draw_w = iw * scale
            draw_h = ih * scale
            # Центрирование
            img_x = mm(br_x + 1) + (max_w - draw_w) / 2
            img_y = mm(sy + 1) + (max_h - draw_h) / 2
            c.drawImage(stamp.emblem_path, img_x, img_y, draw_w, draw_h,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            # Fallback: текст организации
            _text_multiline_center(c, br_x, sy, STAMP_F3_BOTTOM_RIGHT_W, STAMP_F3_AREA4_H,
                                    stamp.organization, FONT_SIZE_STAMP_VALUE - 1, auto_fit=True)
    else:
        _text_multiline_center(c, br_x, sy, STAMP_F3_BOTTOM_RIGHT_W, STAMP_F3_AREA4_H,
                                stamp.organization, FONT_SIZE_STAMP_VALUE - 1, auto_fit=True)


# ══════════════════════════════════════════════════════════════════════
# ШТАМП ПОСЛЕДУЮЩИХ ЛИСТОВ (Форма 2а) — 185×15мм
#
# Правая ячейка: только "Лист" + номер
# "Формат А3" — выводится ОТДЕЛЬНО, под рамкой (draw_format_label)
# ══════════════════════════════════════════════════════════════════════

def draw_stamp_form2a(c: Canvas, page_w_mm: float, page_h_mm: float,
                      stamp: StampInfo, sheet_num: int, format_name: str = ""):
    """Штамп последующих листов (185×15мм)."""

    sx = page_w_mm - FRAME_MARGIN_RIGHT - STAMP_F2A_WIDTH
    sy = FRAME_MARGIN_BOTTOM

    _lw(c, LINE_WIDTH_INNER)

    # Внешний прямоугольник
    c.rect(mm(sx), mm(sy), mm(STAMP_F2A_WIDTH), mm(STAMP_F2A_HEIGHT), stroke=1, fill=0)

    left_right_x = sx + STAMP_F2A_LEFT_W
    right_end_x = sx + STAMP_F2A_WIDTH

    # Вертикальная: левый | правый
    c.line(mm(left_right_x), mm(sy), mm(left_right_x), mm(sy + STAMP_F2A_HEIGHT))

    # Левый блок: горизонтальные строки (3 по 5мм)
    for i in range(1, 3):
        ry = sy + i * STAMP_F2A_ROW_H
        c.line(mm(sx), mm(ry), mm(left_right_x), mm(ry))

    # Левый блок: вертикальные колонки
    cx = sx
    for i, col_w in enumerate(STAMP_F2A_LEFT_COLS):
        cx += col_w
        if i < len(STAMP_F2A_LEFT_COLS) - 1:
            c.line(mm(cx), mm(sy), mm(cx), mm(sy + STAMP_F2A_HEIGHT))

    # Правая ячейка "Лист" — вертикальная линия
    edge_x = right_end_x - STAMP_F2A_RIGHT_EDGE_W
    c.line(mm(edge_x), mm(sy), mm(edge_x), mm(sy + STAMP_F2A_HEIGHT))

    # Горизонтальная линия внутри правой ячейки: "Лист" label (7мм) / номер (8мм)
    split_y = sy + STAMP_F2A_FORMAT_H
    c.line(mm(edge_x), mm(split_y), mm(right_end_x), mm(split_y))

    # ══ ТЕКСТ ══

    # Заголовки левого блока
    cx = sx
    for i, label in enumerate(STAMP_F2A_LEFT_LABELS):
        w = STAMP_F2A_LEFT_COLS[i]
        _text_center(c, cx, sy, w, STAMP_F2A_ROW_H, label, FONT_SIZE_STAMP_SMALL)
        cx += w

    # Обозначение — большая центральная зона
    desig_w = edge_x - left_right_x
    _text_center(c, left_right_x, sy, desig_w, STAMP_F2A_HEIGHT,
                 stamp.designation, FONT_SIZE_STAMP_VALUE, auto_fit=True)

    # Правая ячейка верх: "Лист" label
    _text_center(c, edge_x, split_y, STAMP_F2A_RIGHT_EDGE_W, STAMP_F2A_SHEET_H,
                 "Лист", FONT_SIZE_STAMP_SMALL)

    # Правая ячейка низ: номер листа
    _text_center(c, edge_x, sy, STAMP_F2A_RIGHT_EDGE_W, STAMP_F2A_FORMAT_H,
                 str(sheet_num), FONT_SIZE_STAMP_VALUE)


# ══════════════════════════════════════════════════════════════════════
# ЗАГОЛОВОК ТАБЛИЦЫ (9 колонок)
# ══════════════════════════════════════════════════════════════════════

def draw_table_header(c: Canvas, x_mm: float, y_top_mm: float,
                      col_widths: list[float]) -> float:
    """Рисует заголовок таблицы. Возвращает y_bottom_mm."""
    header_h = TABLE_HEADER_HEIGHT
    y_bottom = y_top_mm - header_h

    _lw(c, LINE_WIDTH_INNER)

    total_w = sum(col_widths)
    c.rect(mm(x_mm), mm(y_bottom), mm(total_w), mm(header_h), stroke=1, fill=0)

    # Вертикальные разделители
    cx = x_mm
    for i, w in enumerate(col_widths):
        if i > 0:
            c.line(mm(cx), mm(y_bottom), mm(cx), mm(y_top_mm))
        cx += w

    # Тексты заголовков (автосокращение)
    cx = x_mm
    for i, col_key in enumerate(COL_ORDER):
        w = col_widths[i]
        header_text = COL_HEADERS[col_key]
        _text_multiline_center(c, cx, y_bottom, w, header_h,
                                header_text, font_size=FONT_SIZE_HEADER, auto_fit=True)
        cx += w

    return y_bottom
