"""تولید PDF فارسی — با فونت وزیرمتن و راست‌به‌چپ.

از reportlab + arabic_reshaper + python-bidi برای نمایش صحیح فارسی استفاده می‌شود.
"""
from __future__ import annotations

import io
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import APP_DIR

FONT_DIR = APP_DIR / "assets" / "fonts"
_FONTS_REGISTERED = False


def _register_fonts() -> None:
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    regular = FONT_DIR / "Vazirmatn-Regular.ttf"
    bold = FONT_DIR / "Vazirmatn-Bold.ttf"
    pdfmetrics.registerFont(TTFont("Vazirmatn", str(regular)))
    if bold.exists():
        pdfmetrics.registerFont(TTFont("Vazirmatn-Bold", str(bold)))
    else:
        pdfmetrics.registerFont(TTFont("Vazirmatn-Bold", str(regular)))
    _FONTS_REGISTERED = True


def fa(text) -> str:
    """آماده‌سازی متن فارسی برای PDF (شکل‌دهی حروف + جهت RTL)."""
    import arabic_reshaper
    from bidi.algorithm import get_display

    return get_display(arabic_reshaper.reshape(str(text if text is not None else "")))


def fa_num(value) -> str:
    """تبدیل ارقام به فارسی برای نمایش."""
    mapping = str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫")
    return str(value).translate(mapping)


def build_pdf(title: str, sections: list[dict]) -> bytes:
    """ساخت PDF از بخش‌ها.

    sections: [{"heading": str, "rows": list[list[str]], "header_row": list[str] | None}]
    """
    _register_fonts()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, topPadding=15 * mm, bottomPadding=15 * mm,
        leftPadding=15 * mm, rightPadding=15 * mm, title=title,
    )
    story: list = []
    story.append(Paragraph(fa(title), pdfmetrics.getFont("Vazirmatn-Bold") and _style("Vazirmatn-Bold", 16)))
    story.append(Spacer(1, 6 * mm))

    for section in sections:
        if section.get("heading"):
            story.append(Paragraph(fa(section["heading"]), _style("Vazirmatn-Bold", 13)))
            story.append(Spacer(1, 3 * mm))
        rows = section.get("rows") or []
        header = section.get("header_row")
        if rows or header:
            table_rows = []
            if header:
                table_rows.append([fa(h) for h in header])
            for row in rows:
                table_rows.append([fa(c) for c in row])
            table = Table(table_rows, hAlign="RIGHT")
            table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), "Vazirmatn"),
                ("FONTNAME", (0, 0), (-1, 0), "Vazirmatn-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [None, "#f5f6fa"]),
                ("GRID", (0, 0), (-1, -1), 0.4, "#c9cdd6"),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(table)
        story.append(Spacer(1, 5 * mm))

    doc.build(story)
    return buffer.getvalue()


def _style(font: str, size: int):
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT

    return ParagraphStyle(
        f"style-{font}-{size}", fontName=font, fontSize=size,
        alignment=TA_RIGHT, leading=size * 1.6,
    )
