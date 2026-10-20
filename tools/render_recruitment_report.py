#!/usr/bin/env python3
"""Typeset the recruitment report as a self-contained PDF with vector diagrams.

Run with an optional document environment containing ReportLab and Pillow.
These authoring dependencies are intentionally separate from solver dependencies.
All prose, table cells, and chart files are read from the Markdown source.
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, Image, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)


INK = colors.HexColor("#18384a")
TEAL = colors.HexColor("#0a827e")
MUTED = colors.HexColor("#536b7a")
PALE = colors.HexColor("#edf5f5")
LINE = colors.HexColor("#d4e0e6")
PAGE_W, PAGE_H = A4
MARGIN = 34
CONTENT_W = PAGE_W - 2 * MARGIN


def plain_hyphens(text: str) -> str:
    """Normalize dash glyphs while retaining meaningful mathematical symbols."""
    return text.translate(str.maketrans({"—": "-", "–": "-", "‑": "-", "−": "-"}))


def inline(text: str) -> str:
    """Convert the report's small inline Markdown vocabulary into PDF markup."""
    text = html.escape(plain_hyphens(text))
    text = re.sub(r"\[([^]]+)\]\((https?://[^)]+)\)",
                  r'<link href="\2" color="#0a827e"><u>\1</u></link>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return text


def register_fonts(font_dir: Path) -> None:
    """Register embedded fonts so the PDF reads identically on other machines."""
    for name, filename in (("Body", "DejaVuSans.ttf"),
                           ("Body-Bold", "DejaVuSans-Bold.ttf"),
                           ("Body-Italic", "DejaVuSans-Oblique.ttf"),
                           ("Body-BoldItalic", "DejaVuSans-BoldOblique.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
                                  italic="Body-Italic", boldItalic="Body-BoldItalic")


def styles() -> dict[str, ParagraphStyle]:
    """Return a compact but readable hierarchy for a nine-page printed report."""
    base = ParagraphStyle("body", fontName="Body", fontSize=9.25, leading=13.1,
                          textColor=INK, spaceAfter=7, alignment=TA_LEFT)
    return {
        "body": base,
        "title": ParagraphStyle("title", parent=base, fontName="Body-Bold",
                                fontSize=23, leading=27, spaceAfter=15),
        "h2": ParagraphStyle("h2", parent=base, fontName="Body-Bold", fontSize=15,
                             leading=19, spaceBefore=5, spaceAfter=11,
                             keepWithNext=True),
        "h3": ParagraphStyle("h3", parent=base, fontName="Body-Bold", fontSize=10.1,
                             leading=14, spaceBefore=6, spaceAfter=7,
                             keepWithNext=True),
        "cell": ParagraphStyle("cell", parent=base, fontSize=8.65, leading=11.8,
                               spaceAfter=0),
        "small": ParagraphStyle("small", parent=base, fontSize=8, leading=11,
                                textColor=MUTED),
        "diagram": ParagraphStyle("diagram", parent=base, fontSize=8.6,
                                  leading=11.5, spaceAfter=0),
    }


class Diagram(Flowable):
    """Draw readable, selectable vector equivalents of the report's Mermaid."""

    def __init__(self, kind: int, style: ParagraphStyle) -> None:
        super().__init__()
        self.kind = kind
        self.style = style
        self.width = CONTENT_W
        self.height = {0: 105, 1: 198, 2: 212, 3: 94}[kind]

    def box(self, x: float, y: float, width: float, height: float,
            text: str, fill: colors.Color = PALE) -> None:
        """Draw one labelled node with consistent internal padding."""
        self.canv.setFillColor(fill)
        self.canv.setStrokeColor(LINE)
        self.canv.roundRect(x, y, width, height, 6, fill=1, stroke=1)
        p = Paragraph(text, self.style)
        _, ph = p.wrap(width - 18, height - 12)
        p.drawOn(self.canv, x + 9, y + (height - ph) / 2)

    def arrow(self, x1: float, y1: float, x2: float, y2: float,
              label: str = "") -> None:
        """Draw an arrow and an optional compact outcome label."""
        import math
        self.canv.setStrokeColor(TEAL)
        self.canv.setLineWidth(1.2)
        self.canv.line(x1, y1, x2, y2)
        angle = math.atan2(y2 - y1, x2 - x1)
        for delta in (-0.45, 0.45):
            self.canv.line(x2, y2, x2 - 5 * math.cos(angle + delta),
                           y2 - 5 * math.sin(angle + delta))
        if label:
            self.canv.setFillColor(MUTED)
            self.canv.setFont("Body", 7.5)
            if abs(x2 - x1) < 1:
                self.canv.drawString(x1 + 6, (y1 + y2) / 2 - 2, label)
            else:
                self.canv.drawCentredString((x1 + x2) / 2, (y1 + y2) / 2 + 5, label)

    def draw(self) -> None:
        """Render the chosen diagram without changing its decision semantics."""
        w = self.width
        if self.kind == 0:
            bw = (w - 32) / 3
            texts = [
                "<b>Stage 1: stone + roads</b><br/>Exact search, cached geometry, investment DP",
                "<b>Stage 2: add ore</b><br/>Reuse search; keep resources separate; saving and relaxed policies",
                "<b>Stage 3: add iron manufacturing</b><br/>Reuse typed engine; order whole projects; optional production + on-demand DP",
            ]
            for i, text in enumerate(texts):
                self.box(i * (bw + 16), 8, bw, 92, text)
                if i < 2:
                    self.arrow((i + 1) * bw + i * 16 + 2, 54,
                               (i + 1) * (bw + 16) - 2, 54)
        elif self.kind == 1:
            self.box(0, 140, 102, 48, "<b>Original task</b>")
            self.box(131, 140, 160, 48, "<b>Quick policy plans</b>")
            self.box(340, 140, w - 340, 48, "<b>Independent replay</b>")
            self.box(131, 63, 160, 54, "<b>Full search</b><br/>Order, memoize, prune")
            self.box(340, 63, w - 340, 54, "<b>Submit once and verify credit</b>")
            self.box(131, 0, 160, 40, "<b>UNKNOWN: do not submit</b>", colors.HexColor("#fff4e7"))
            self.arrow(104, 164, 129, 164)
            self.arrow(293, 164, 338, 164, "win")
            self.arrow(211, 138, 211, 119, "miss")
            self.arrow(293, 103, 338, 151, "win")
            self.arrow(432, 138, 432, 119, "valid")
            self.arrow(211, 61, 211, 42, "deadline")
        elif self.kind == 2:
            bw = (w - 24) / 2
            self.box(0, 144, bw, 61, "<b>Observe</b><br/>States, duplicates, probe outcomes, DP work, time and memory")
            self.box(bw + 24, 144, bw, 61, "<b>Form a hypothesis</b><br/>Identify the expensive or missing work")
            self.box(bw + 24, 69, bw, 61, "<b>Compare on fixed inputs</b><br/>Baseline / candidate / combinations")
            self.box(0, 69, bw, 61, "<b>Promote only with evidence</b><br/>Coverage first, then time and cost")
            self.box(0, 0, bw, 55, "<b>Replay, submit once, verify credit</b><br/>Retain each input as a regression")
            self.arrow(bw + 2, 175, bw + 22, 175)
            self.arrow(bw * 1.5 + 24, 142, bw * 1.5 + 24, 132)
            self.arrow(bw + 22, 100, bw + 2, 100)
            self.arrow(bw / 2, 67, bw / 2, 57)
            self.canv.setStrokeColor(TEAL)
            self.canv.line(8, 27, -11, 27)
            self.canv.line(-11, 27, -11, 175)
            self.arrow(-11, 175, -2, 175)
        else:
            bw = (w - 32) / 3
            texts = [
                "<b>Observed stop</b><br/>100,000-state cap<br/>4.247 s; no submission",
                "<b>Test the obvious fix</b><br/>Remove cap only<br/>Still UNKNOWN at 24 s",
                "<b>Inspect route decisions</b><br/>Correct resource-specific ordering<br/>Same map wins in 49.658 ms",
            ]
            for i, text in enumerate(texts):
                self.box(i * (bw + 16), 5, bw, 84, text)
                if i < 2:
                    self.arrow((i + 1) * bw + i * 16 + 2, 47,
                               (i + 1) * (bw + 16) - 2, 47)


def table(block: list[str], style: dict[str, ParagraphStyle]) -> Table:
    """Create a repeating-header table with readable, wrapping cells."""
    rows = [[cell.strip() for cell in row.strip().strip("|").split("|")]
            for row in block if not re.fullmatch(r"[\s|:\-]+", row)]
    ncols = len(rows[0])
    if ncols == 3:
        widths = [CONTENT_W * 0.68, CONTENT_W * 0.10, CONTENT_W * 0.22]
    else:
        widths = [CONTENT_W * 0.345, CONTENT_W * 0.655]
    data = [[Paragraph(inline(cell), style["cell"]) for cell in row] for row in rows]
    result = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fb")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, LINE),
    ]))
    result.spaceAfter = 10
    return result


def paragraphs(source: str, source_dir: Path,
               style: dict[str, ParagraphStyle], diagram_offset: int = 0) -> list:
    """Parse report blocks in order, preserving all prose and table content."""
    lines = source.strip().splitlines()
    result = []
    i = 0
    diagram_index = diagram_offset
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("```mermaid"):
            result.append(Diagram(diagram_index, style["diagram"]))
            result.append(Spacer(1, 10))
            diagram_index += 1
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                i += 1
            i += 1
            continue
        if line.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            result.append(table(block, style))
            continue
        image_match = re.fullmatch(r"!\[([^]]+)\]\(([^)]+)\)", line)
        if image_match:
            from PIL import Image as PILImage
            path = source_dir / image_match.group(2)
            width, height = PILImage.open(path).size
            draw_width = 485 if path.name == "recruitment-stage3-decisions.png" else CONTENT_W
            image = Image(str(path), width=draw_width, height=draw_width * height / width)
            image.hAlign = "CENTER"
            image.spaceBefore = 6
            image.spaceAfter = 10
            result.append(image)
            i += 1
            continue
        if line.startswith("# "):
            result.append(Paragraph(inline(line[2:]), style["title"]))
            i += 1
            continue
        if line.startswith("## "):
            result.append(Paragraph(inline(line[3:]), style["h2"]))
            i += 1
            continue
        block = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "```", "![", "- ")):
            block.append(lines[i].strip())
            i += 1
        text = " ".join(block)
        if text.startswith("- "):
            p = Paragraph(inline(text[2:]), style["body"], bulletText="•")
            result.append(p)
        elif re.fullmatch(r"\*\*[^*]+\*\*", text):
            result.append(Paragraph(inline(text), style["h3"]))
        else:
            result.append(Paragraph(inline(text), style["body"]))
    return result


def page_chrome(canvas: Canvas, doc: BaseDocTemplate) -> None:
    """Add consistent running identification and page numbers."""
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, PAGE_H - 32, PAGE_W - MARGIN, PAGE_H - 32)
    canvas.setFont("Body", 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, PAGE_H - 24, "BLADE RUNNER  /  SOLVER DELIVERY REPORT")
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 24, "Dan Xiao")
    canvas.line(MARGIN, 30, PAGE_W - MARGIN, 30)
    canvas.drawString(MARGIN, 19, "Measured local evidence • Three stages • One Python application")
    canvas.drawRightString(PAGE_W - MARGIN, 19, str(doc.page))
    canvas.restoreState()


def make_pdf(root: Path, output: Path, font_dir: Path) -> None:
    """Build the PDF from the current report with intentional page transitions."""
    source = root / "docs/reports/recruitment-delivery-report.md"
    text = source.read_text()
    register_fonts(font_dir)
    style = styles()
    boundaries = [
        "```mermaid",
        "## Stage 1",
        "## Stage 2",
        "**Stage 2 delivery summary**",
        "**Decision A: on-demand DP.**",
        "**What the delivered code demonstrates**",
        "**Time accounting: development, comparison and validation**",
        "The game-completion turn ends",
    ]
    parts = []
    cursor = 0
    for marker in boundaries:
        index = text.index(marker, cursor)
        parts.append(text[cursor:index])
        cursor = index
    parts.append(text[cursor:])
    titles = {
        1: "How the solver works and improves",
        5: "Stage 3 decisions and delivery",
        6: "Correctness, validation and reviewability",
        8: "Scope, follow-ups and references",
    }
    story = []
    diagram_offset = 0
    for i, part in enumerate(parts):
        if i:
            story.append(PageBreak())
        if i in titles:
            story.append(Paragraph(titles[i], style["h2"]))
        section_styles = style
        if i == 8:
            section_styles = dict(style)
            section_styles["body"] = ParagraphStyle("closing_body", parent=style["body"],
                                                     fontSize=8.95, leading=12.3, spaceAfter=6)
            section_styles["cell"] = ParagraphStyle("closing_cell", parent=style["cell"],
                                                     fontSize=8.3, leading=11.2)
        story.extend(paragraphs(part, source.parent, section_styles, diagram_offset))
        diagram_offset += part.count("```mermaid")
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(output), pagesize=A4, leftMargin=MARGIN,
                          rightMargin=MARGIN, topMargin=45, bottomMargin=42,
                          title="Blade Runner: an evidence-led path through three stages",
                          author="Dan Xiao", subject="Solver design, performance comparisons, quality and delivery evidence")
    frame = Frame(MARGIN, 42, CONTENT_W, PAGE_H - 87, leftPadding=0,
                  bottomPadding=0, rightPadding=0, topPadding=0)
    doc.addPageTemplates([PageTemplate(id="report", frames=[frame], onPage=page_chrome)])
    doc.build(story)


def main() -> None:
    """Parse authoring paths without introducing runtime solver dependencies."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--font-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output or args.root / "output/pdf/blade-runner-delivery-report.pdf"
    make_pdf(args.root, output, args.font_dir)
    print(output)


if __name__ == "__main__":
    main()
