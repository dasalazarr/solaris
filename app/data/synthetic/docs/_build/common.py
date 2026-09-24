"""Helpers deterministas para generar DOCX, XLSX y PDF del corpus sintético (ADR-0004).

Todo binario se normaliza (fechas del zip y de docProps fijas) para que regenerar dé el mismo md5.
"""
from __future__ import annotations

import re
import zipfile
from datetime import date, datetime
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Cm
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

DOCS = Path(__file__).resolve().parents[1]
COMPANY = "Componentes Arga S.L."
COMPANY_ADDR = "Pol. Ind. Arga Norte, Orkoien (Navarra)"
FIXED_DT = datetime(2026, 9, 25, 8, 0, 0)
ZIP_DT = (2026, 9, 25, 8, 0, 0)

# --------------------------------------------------------------------------- formatos


def fdate(d: date, lang: str = "ES") -> str:
    return d.strftime("%d/%m/%Y") if lang == "ES" else d.strftime("%Y-%m-%d")


def fnum(n: int | float, lang: str = "ES") -> str:
    s = f"{n:,}"
    return s.replace(",", ".") if lang == "ES" else s


# --------------------------------------------------------------------------- normalización


def normalize_zip(path: Path, created: datetime = FIXED_DT) -> None:
    """Reescribe un OOXML con fechas fijas (zip y docProps/core.xml)."""
    with zipfile.ZipFile(path) as zin:
        items = [(i.filename, zin.read(i.filename)) for i in zin.infolist()]
    iso = created.strftime("%Y-%m-%dT%H:%M:%SZ")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in sorted(items, key=lambda kv: (kv[0] != "[Content_Types].xml", kv[0])):
            if name == "docProps/core.xml":
                txt = data.decode("utf-8")
                txt = re.sub(r"(<dcterms:created[^>]*>)[^<]*(</dcterms:created>)", rf"\g<1>{iso}\2", txt)
                txt = re.sub(r"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)", rf"\g<1>{iso}\2", txt)
                data = txt.encode("utf-8")
            zi = zipfile.ZipInfo(name, date_time=ZIP_DT)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zout.writestr(zi, data)


# --------------------------------------------------------------------------- DOCX


def _shade(cell, hex_fill: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


class Doc:
    """Documento Word con cabecera corporativa de Arga (o del OEM ficticio)."""

    def __init__(self, doc_code: str, version: str, title: str, *, lang: str = "ES",
                 header_left: str = COMPANY, header_right: str | None = None,
                 author: str = "Calidad Arga", when: datetime = FIXED_DT, accent: str = "1F4E79"):
        self.d = Document()
        self.lang = lang
        self.accent = accent
        st = self.d.styles["Normal"]
        st.font.name = "Calibri"
        st.font.size = Pt(10)
        for s in self.d.sections:
            s.left_margin = s.right_margin = Cm(2)
            s.top_margin = Cm(1.6)
            s.bottom_margin = Cm(1.6)
            hdr = s.header.paragraphs[0]
            hdr.text = f"{header_left}    |    {doc_code}  {version}    |    {header_right or title}"
            hdr.runs[0].font.size = Pt(8)
            hdr.runs[0].font.color.rgb = RGBColor(0x59, 0x59, 0x59)
            ftr = s.footer.paragraphs[0]
            conf = "Uso interno" if lang == "ES" else "Internal use"
            ftr.text = f"{COMPANY} · {COMPANY_ADDR} · {conf} · IATF 16949"
            ftr.runs[0].font.size = Pt(7)
        cp = self.d.core_properties
        cp.author = author
        cp.last_modified_by = author
        cp.title = f"{doc_code} {title}"
        cp.created = when
        cp.modified = when
        cp.revision = 1

    # bloques ---------------------------------------------------------------
    def title(self, text: str, sub: str | None = None) -> None:
        p = self.d.add_paragraph()
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(16)
        r.font.color.rgb = RGBColor.from_string(self.accent)
        if sub:
            p2 = self.d.add_paragraph()
            r2 = p2.add_run(sub)
            r2.italic = True
            r2.font.size = Pt(10)

    def h(self, text: str, level: int = 1) -> None:
        p = self.d.add_heading(text, level=level)
        for r in p.runs:
            r.font.color.rgb = RGBColor.from_string(self.accent)

    def p(self, text: str, bold: bool = False, italic: bool = False, size: int | None = None) -> None:
        para = self.d.add_paragraph()
        r = para.add_run(text)
        r.bold, r.italic = bold, italic
        if size:
            r.font.size = Pt(size)

    def kv(self, label: str, value: str) -> None:
        para = self.d.add_paragraph()
        para.add_run(f"{label}: ").bold = True
        para.add_run(value)

    def bullets(self, items: list[str]) -> None:
        for it in items:
            self.d.add_paragraph(it, style="List Bullet")

    def numbered(self, items: list[str]) -> None:
        for it in items:
            self.d.add_paragraph(it, style="List Number")

    def table(self, header: list[str] | None, rows: list[list], widths: list[float] | None = None,
              font: int = 8, head_fill: str | None = None) -> None:
        ncols = len(header) if header else len(rows[0])
        t = self.d.add_table(rows=0, cols=ncols)
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        if header:
            cells = t.add_row().cells
            for c, txt in zip(cells, header):
                c.text = str(txt)
                for r in c.paragraphs[0].runs:
                    r.bold = True
                    r.font.size = Pt(font)
                    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                _shade(c, head_fill or self.accent)
        for row in rows:
            cells = t.add_row().cells
            for c, txt in zip(cells, row):
                c.text = "" if txt is None else str(txt)
                for par in c.paragraphs:
                    for r in par.runs:
                        r.font.size = Pt(font)
        if widths:
            for row in t.rows:
                for c, w in zip(row.cells, widths):
                    c.width = Cm(w)
        self.d.add_paragraph()

    def form(self, pairs: list[tuple[str, str]], cols: int = 2, font: int = 8) -> None:
        """Tabla de cabecera tipo formulario: etiqueta sombreada + valor."""
        t = self.d.add_table(rows=0, cols=cols * 2)
        t.style = "Table Grid"
        for i in range(0, len(pairs), cols):
            cells = t.add_row().cells
            for j, (k, v) in enumerate(pairs[i:i + cols]):
                cells[2 * j].text = k
                cells[2 * j + 1].text = v
                _shade(cells[2 * j], "DDE5EE")
                for c in (cells[2 * j], cells[2 * j + 1]):
                    for r in c.paragraphs[0].runs:
                        r.font.size = Pt(font)
                cells[2 * j].paragraphs[0].runs[0].bold = True
        self.d.add_paragraph()

    def page_break(self) -> None:
        self.d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def signatures(self, rows: list[tuple[str, str, str, str]], lang: str | None = None) -> None:
        lang = lang or self.lang
        hdr = ["Función", "Nombre", "Fecha", "Firma"] if lang == "ES" else ["Role", "Name", "Date", "Signature"]
        self.table(hdr, [list(r) for r in rows], font=8)

    def save(self, rel_path: str) -> Path:
        out = DOCS / rel_path
        out.parent.mkdir(parents=True, exist_ok=True)
        self.d.save(out)
        normalize_zip(out)
        return out


# --------------------------------------------------------------------------- XLSX

THIN = Side(style="thin", color="808080")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEAD_FILL = PatternFill("solid", fgColor="1F4E79")
HEAD_FONT = Font(bold=True, color="FFFFFF", size=9)
WRAP = Alignment(wrap_text=True, vertical="top")


def new_workbook(creator: str = "Calidad Arga") -> Workbook:
    wb = Workbook()
    wb.properties.creator = creator
    wb.properties.lastModifiedBy = creator
    wb.properties.created = FIXED_DT
    wb.properties.modified = FIXED_DT
    return wb


def write_table(ws, top: int, header: list[str], rows: list[list], widths: list[int] | None = None,
                left: int = 1) -> int:
    for j, h in enumerate(header):
        c = ws.cell(row=top, column=left + j, value=h)
        c.fill, c.font, c.border, c.alignment = HEAD_FILL, HEAD_FONT, BORDER, WRAP
    for i, row in enumerate(rows, start=1):
        for j, v in enumerate(row):
            c = ws.cell(row=top + i, column=left + j, value=v)
            c.border, c.alignment = BORDER, WRAP
            c.font = Font(size=9)
    if widths:
        from openpyxl.utils import get_column_letter
        for j, w in enumerate(widths):
            ws.column_dimensions[get_column_letter(left + j)].width = w
    return top + len(rows)


def xlsx_header_block(ws, lines: list[tuple[str, str]], top: int = 1) -> int:
    for i, (k, v) in enumerate(lines):
        ws.cell(row=top + i, column=1, value=k).font = Font(bold=True, size=9)
        ws.cell(row=top + i, column=2, value=v).font = Font(size=9)
    return top + len(lines) + 1


def save_wb(wb: Workbook, rel_path: str) -> Path:
    out = DOCS / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    normalize_zip(out)
    return out
