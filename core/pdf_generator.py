"""
Оркестратор генерации PDF-документа спецификации по ГОСТ 21.110-2013.
Поддержка категорий/подкатегорий, clipping, автоперенос.
"""

import logging
import os
import sys

from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit

from core.constants import (
    mm, MM,
    FRAME_MARGIN_LEFT, FRAME_MARGIN_RIGHT, FRAME_MARGIN_TOP,
    LINE_WIDTH_THIN, LINE_WIDTH_INNER, CELL_PADDING, ROW_MIN_HEIGHT,
    FONT_NAME, FONT_NAME_ITALIC,
    FONT_SIZE_DATA,
    FONT_SCALE,
    BASELINE_OFFSET_RATIO, LINE_HEIGHT_FACTOR,
    scale_col_widths,
)
from core.data_model import SpecificationDocument, SpecificationRow, RowType
from core.gost_templates import draw_frame, draw_stamp_form3, draw_stamp_form2a, draw_table_header, draw_format_label, _clipped, _font
from core.pagination import paginate, calc_row_height


def _resource_path(relative_path: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), relative_path)


class SpecPdfGenerator:

    def __init__(self, document: SpecificationDocument):
        self.doc = document
        self.page_w_mm, self.page_h_mm = document.get_page_size_mm()
        drawable_w = self.page_w_mm - FRAME_MARGIN_LEFT - FRAME_MARGIN_RIGHT
        if drawable_w <= 0:
            raise ValueError(
                f"Недопустимые размеры страницы: drawable_w={drawable_w}мм "
                f"(page_w={self.page_w_mm}, margins={FRAME_MARGIN_LEFT}+{FRAME_MARGIN_RIGHT})"
            )
        self.col_widths = scale_col_widths(drawable_w)
        self.total_col_width = sum(self.col_widths)
        self._fonts_registered = False
        user_font = getattr(document, 'font_name', 'arial')
        self.font_scale = FONT_SCALE.get(user_font, 1.0)

    def _register_fonts(self):
        if self._fonts_registered:
            return

        font_dir = _resource_path("fonts")

        # Приоритет: шрифт выбранный пользователем → bundled → системные fallback
        import platform
        user_font = getattr(self.doc, 'font_name', 'arial')
        sys_fonts = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts") \
            if platform.system() == "Windows" else "/usr/share/fonts"

        # Пользовательский выбор → конкретные TTF файлы
        font_candidates = {
            "arial": [
                os.path.join(font_dir, "arial.ttf"),
                os.path.join(sys_fonts, "arial.ttf"),
            ],
            "times": [
                os.path.join(sys_fonts, "times.ttf"),
                os.path.join(sys_fonts, "Times New Roman.ttf"),
            ],
            "isocpeur": [
                os.path.join(font_dir, "ISOCPEUR.ttf"),
                os.path.join(sys_fonts, "ISOCPEUR.ttf"),
                os.path.join(sys_fonts, "isocpeur.ttf"),
            ],
        }

        # Собираем: сначала preferred, потом fallback
        candidates = font_candidates.get(user_font, [])
        # Fallback: arial (бандлен)
        if user_font != "arial":
            candidates += font_candidates["arial"]

        # Очищаем кэш шрифта чтобы перерегистрация сработала
        for name in [FONT_NAME, FONT_NAME_ITALIC]:
            if name in pdfmetrics._fonts:
                del pdfmetrics._fonts[name]

        for fp in candidates:
            try:
                pdfmetrics.registerFont(TTFont(FONT_NAME, fp))
                logging.info(f"Шрифт зарегистрирован: {fp}")
                break
            except Exception:
                continue

        # Italic — используем тот же шрифт как fallback (ReportLab не поддерживает italic без отдельного TTF)
        italic_path = os.path.join(font_dir, "ISOCPEUR_Italic.ttf")
        if os.path.exists(italic_path):
            try:
                pdfmetrics.registerFont(TTFont(FONT_NAME_ITALIC, italic_path))
            except (IOError, OSError, ValueError) as e:
                logging.warning(f"Не удалось зарегистрировать italic шрифт: {e}")

        self._fonts_registered = True

    def _get_font(self, bold: bool = False, italic: bool = False) -> str:
        """Возвращает имя шрифта. Bold/italic — пока используем тот же шрифт."""
        # В будущем можно добавить bold/italic варианты
        if italic:
            try:
                pdfmetrics.getFont(FONT_NAME_ITALIC)
                return FONT_NAME_ITALIC
            except KeyError:
                return FONT_NAME
        return FONT_NAME

    def generate(self, output_path: str) -> None:
        self._register_fonts()

        c = Canvas(output_path, pagesize=(mm(self.page_w_mm), mm(self.page_h_mm)))
        c.setTitle("Спецификация по ГОСТ 21.110-2013")
        c.setAuthor("GOST Spec Generator")

        pages = paginate(self.doc.rows, self.col_widths, self.page_h_mm,
                         FONT_NAME, FONT_SIZE_DATA)
        total_sheets = len(pages)
        format_name = self.doc.page_format.name

        for page_idx, page_rows in enumerate(pages):
            is_first = (page_idx == 0)
            sheet_num = page_idx + 1

            draw_frame(c, self.page_w_mm, self.page_h_mm)

            if is_first:
                draw_stamp_form3(c, self.page_w_mm, self.page_h_mm,
                                 self.doc.stamp, sheet_num, total_sheets,
                                 font_scale=self.font_scale)
            else:
                draw_stamp_form2a(c, self.page_w_mm, self.page_h_mm,
                                  self.doc.stamp, sheet_num, format_name,
                                  font_scale=self.font_scale)

            draw_format_label(c, self.page_w_mm, self.page_h_mm, format_name)

            x_start = FRAME_MARGIN_LEFT
            y_top = self.page_h_mm - FRAME_MARGIN_TOP
            y_after_header = draw_table_header(c, x_start, y_top, self.col_widths)

            self._draw_data_rows(c, x_start, y_after_header, page_rows)

            c.showPage()

        c.save()

    def _draw_data_rows(self, c: Canvas, x_mm: float, y_top_mm: float,
                        rows: list[SpecificationRow]):
        y = y_top_mm

        for row in rows:
            total_w = self.total_col_width

            if row.row_type in (RowType.CATEGORY, RowType.SUBCATEGORY):
                # Объединённая строка на всю ширину
                row_h = ROW_MIN_HEIGHT
                y_bottom = y - row_h

                c.setLineWidth(mm(LINE_WIDTH_INNER))
                # Горизонтальная линия снизу
                c.line(mm(x_mm), mm(y_bottom), mm(x_mm + total_w), mm(y_bottom))
                # Левая и правая границы
                c.line(mm(x_mm), mm(y_bottom), mm(x_mm), mm(y))
                c.line(mm(x_mm + total_w), mm(y_bottom), mm(x_mm + total_w), mm(y))

                # Текст
                text = row.display_text()
                if row.row_type == RowType.CATEGORY:
                    # Жирный, крупный, левое выравнивание
                    self._draw_merged_row_text(c, x_mm, y_bottom, total_w, row_h,
                                                text, bold=True)
                else:
                    # Курсив, левое выравнивание
                    self._draw_merged_row_text(c, x_mm, y_bottom, total_w, row_h,
                                                text, italic=True)
            else:
                # Обычная строка данных
                row_h = calc_row_height(row, self.col_widths, FONT_NAME, FONT_SIZE_DATA)
                y_bottom = y - row_h

                c.setLineWidth(mm(LINE_WIDTH_THIN))
                c.line(mm(x_mm), mm(y_bottom), mm(x_mm + total_w), mm(y_bottom))

                values = row.to_row_values()
                cx = x_mm

                for i, (val, col_w) in enumerate(zip(values, self.col_widths)):
                    if i > 0:
                        c.line(mm(cx), mm(y_bottom), mm(cx), mm(y))
                    self._draw_cell_text(c, cx, y_bottom, col_w, row_h, val)
                    cx += col_w

                c.line(mm(cx), mm(y_bottom), mm(cx), mm(y))
                c.line(mm(x_mm), mm(y_bottom), mm(x_mm), mm(y))

            y = y_bottom

    def _draw_merged_row_text(self, c: Canvas, x_mm: float, y_bottom_mm: float,
                               w_mm: float, h_mm: float, text: str,
                               bold: bool = False, italic: bool = False):
        """Текст в объединённой строке (категория/подкатегория)."""
        if not text:
            return

        font_name = self._get_font(bold=bold, italic=italic)
        font_size = FONT_SIZE_DATA + 1 if bold else FONT_SIZE_DATA

        font_name = _font(c, font_size)

        padding_pt = mm(CELL_PADDING + 1)
        ty = mm(y_bottom_mm + h_mm / 2) - font_size * BASELINE_OFFSET_RATIO

        with _clipped(c, x_mm, y_bottom_mm, w_mm, h_mm):
            if bold and font_name == FONT_NAME:
                c.drawString(mm(x_mm) + padding_pt, ty, text)
                c.drawString(mm(x_mm) + padding_pt + 0.3, ty, text)
            else:
                c.drawString(mm(x_mm) + padding_pt, ty, text)

    def _draw_cell_text(self, c: Canvas, x_mm: float, y_bottom_mm: float,
                        w_mm: float, h_mm: float, text: str):
        """Текст ячейки с автопереносом и clipping."""
        if not text:
            return

        font_size = FONT_SIZE_DATA
        fn = _font(c, font_size)

        padding_pt = mm(CELL_PADDING)
        available_w = mm(w_mm) - 2 * padding_pt
        if available_w <= 0:
            return

        lines = simpleSplit(text, fn, font_size, available_w)
        line_h = font_size * LINE_HEIGHT_FACTOR

        total_text_h = len(lines) * line_h
        start_y = mm(y_bottom_mm + h_mm / 2) + total_text_h / 2 - line_h * 0.7

        with _clipped(c, x_mm, y_bottom_mm, w_mm, h_mm):
            for i, line in enumerate(lines):
                tx = mm(x_mm) + padding_pt
                ty = start_y - i * line_h
                c.drawString(tx, ty, line)
