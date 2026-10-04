from __future__ import annotations

import binascii
import struct
import tempfile
import zlib
from pathlib import Path

from odf.draw import Frame, Image
from odf.dc import Subject, Title
from odf.opendocument import OpenDocumentText
from odf.style import (
    Footer,
    Header,
    MasterPage,
    PageLayout,
    PageLayoutProperties,
    ParagraphProperties,
    Style,
    TableCellProperties,
    TableColumnProperties,
    TextProperties,
)
from odf.table import CoveredTableCell, Table, TableCell, TableColumn, TableHeaderRows, TableRow
from odf.text import (
    A,
    H,
    List,
    ListItem,
    ListLevelStyleBullet,
    ListStyle,
    Note,
    NoteBody,
    NoteCitation,
    P,
    PageNumber,
    Span,
)


OUTPUT = Path(__file__).resolve().parent / "samples"


def add_style(doc, name, family, *, paragraph=None, text=None, cell=None):
    style = Style(name=name, family=family)
    if paragraph:
        style.addElement(ParagraphProperties(**paragraph))
    if text:
        style.addElement(TextProperties(**text))
    if cell:
        style.addElement(TableCellProperties(**cell))
    doc.styles.addElement(style)
    return style


def add_common_styles(doc):
    add_style(
        doc,
        "BodyText",
        "paragraph",
        paragraph={"marginbottom": "0.08in", "lineheight": "120%"},
        text={"fontfamily": "Liberation Serif", "fontsize": "11pt", "language": "en", "country": "US"},
    )
    add_style(
        doc,
        "DocumentTitle",
        "paragraph",
        paragraph={"marginbottom": "0.12in", "keepwithnext": "always"},
        text={"fontfamily": "Liberation Sans", "fontsize": "24pt", "fontweight": "bold", "color": "#174a5b"},
    )
    add_style(
        doc,
        "SectionHeading",
        "paragraph",
        paragraph={"margintop": "0.18in", "marginbottom": "0.07in", "keepwithnext": "always"},
        text={"fontfamily": "Liberation Sans", "fontsize": "15pt", "fontweight": "bold", "color": "#174a5b"},
    )
    add_style(
        doc,
        "Subheading",
        "paragraph",
        paragraph={"margintop": "0.12in", "marginbottom": "0.04in", "keepwithnext": "always"},
        text={"fontfamily": "Liberation Sans", "fontsize": "12pt", "fontweight": "bold", "color": "#287271"},
    )
    add_style(
        doc,
        "PageBreakHeading",
        "paragraph",
        paragraph={"breakbefore": "page", "margintop": "0.18in", "marginbottom": "0.07in", "keepwithnext": "always"},
        text={"fontfamily": "Liberation Sans", "fontsize": "15pt", "fontweight": "bold", "color": "#174a5b"},
    )
    add_style(
        doc,
        "Caption",
        "paragraph",
        paragraph={"textalign": "center", "margintop": "0.04in", "marginbottom": "0.12in"},
        text={"fontfamily": "Liberation Sans", "fontsize": "9pt", "fontstyle": "italic", "color": "#444444"},
    )
    add_style(
        doc,
        "HeaderText",
        "paragraph",
        paragraph={"textalign": "end"},
        text={"fontfamily": "Liberation Sans", "fontsize": "8pt", "color": "#555555"},
    )
    add_style(
        doc,
        "CellText",
        "paragraph",
        paragraph={"marginbottom": "0in"},
        text={"fontfamily": "Liberation Sans", "fontsize": "9pt"},
    )
    add_style(
        doc,
        "CellHeader",
        "paragraph",
        paragraph={"marginbottom": "0in"},
        text={"fontfamily": "Liberation Sans", "fontsize": "9pt", "fontweight": "bold", "color": "#ffffff"},
    )
    add_style(
        doc,
        "TableCell",
        "table-cell",
        cell={"border": "0.5pt solid #8da5a5", "padding": "0.06in", "verticalalign": "middle"},
    )
    add_style(
        doc,
        "TableHeaderCell",
        "table-cell",
        cell={"border": "0.5pt solid #174a5b", "padding": "0.07in", "backgroundcolor": "#287271", "verticalalign": "middle"},
    )
    add_style(
        doc,
        "TableAltCell",
        "table-cell",
        cell={"border": "0.5pt solid #8da5a5", "padding": "0.06in", "backgroundcolor": "#e9f1ef", "verticalalign": "middle"},
    )


def new_document(title, *, landscape=False, running_header=False):
    doc = OpenDocumentText()
    doc.meta.addElement(Title(text=title))
    doc.meta.addElement(Subject(text="Word processor compatibility test sample"))
    add_common_styles(doc)

    page_layout = PageLayout(name="TestPageLayout")
    page_layout.addElement(
        PageLayoutProperties(
            pagewidth="11in" if landscape else "8.5in",
            pageheight="8.5in" if landscape else "11in",
            printorientation="landscape" if landscape else "portrait",
            margin="0.7in",
        )
    )
    doc.automaticstyles.addElement(page_layout)
    master = MasterPage(name="Standard", pagelayoutname="TestPageLayout")
    if running_header:
        header = Header()
        header.addElement(P(stylename="HeaderText", text=title))
        master.addElement(header)
        footer = Footer()
        footer_line = P(stylename="HeaderText")
        footer_line.addText("Compatibility sample  |  Page ")
        footer_line.addElement(PageNumber(selectpage="current"))
        footer.addElement(footer_line)
        master.addElement(footer)
    doc.masterstyles.addElement(master)
    return doc


def paragraph(doc, text, style="BodyText"):
    doc.text.addElement(P(stylename=style, text=text))


def heading(doc, text, level=1):
    doc.text.addElement(H(outlinelevel=str(level), stylename="SectionHeading" if level == 1 else "Subheading", text=text))


def add_bullet_list(doc, entries):
    list_style = ListStyle(name="SampleBullets")
    list_style.addElement(ListLevelStyleBullet(level="1", bulletchar="\u2022"))
    doc.styles.addElement(list_style)
    sample_list = List(stylename="SampleBullets")
    for entry in entries:
        item = ListItem()
        item.addElement(P(stylename="BodyText", text=entry))
        sample_list.addElement(item)
    doc.text.addElement(sample_list)


def add_column(doc, width):
    style = Style(name="Column" + width.replace(".", "_").replace("in", ""), family="table-column")
    style.addElement(TableColumnProperties(columnwidth=width))
    doc.automaticstyles.addElement(style)
    return style


def cell(text, *, header=False, alternate=False, span=1):
    if span > 1:
        target = TableCell(numbercolumnsspanned=str(span), stylename="TableHeaderCell" if header else "TableCell")
    else:
        target = TableCell(stylename="TableHeaderCell" if header else "TableAltCell" if alternate else "TableCell")
    target.addElement(P(stylename="CellHeader" if header else "CellText", text=text))
    return target


def add_data_table(doc, *, many_rows=False, merged=False):
    table = Table(name="CompatibilityTable")
    for width in ("1.55in", "1.75in", "2.1in"):
        table.addElement(TableColumn(stylename=add_column(doc, width)))

    if merged:
        row = TableRow()
        row.addElement(cell("Merged heading spans two columns", header=True, span=2))
        row.addElement(CoveredTableCell())
        row.addElement(cell("Third column", header=True))
        table.addElement(row)

    header_rows = TableHeaderRows()
    header_row = TableRow()
    for label in ("Case", "Expected behavior", "Notes"):
        header_row.addElement(cell(label, header=True))
    header_rows.addElement(header_row)
    table.addElement(header_rows)

    rows = [
        ("Inline formatting", "Bold, italic, underline", "Mixed runs in a paragraph"),
        ("Page furniture", "Header and page number", "Repeated on each page"),
        ("Raster graphic", "Image remains embedded", "PNG with multiple colors"),
        ("Vector graphic", "Shapes remain visible", "Embedded SVG artwork"),
    ]
    if many_rows:
        rows.extend(
            (f"Pagination case {index:02d}", "Rows should stay readable", "Repeated header across pages")
            for index in range(5, 79)
        )
    for index, row_data in enumerate(rows):
        row = TableRow()
        for value in row_data:
            row.addElement(cell(value, alternate=index % 2 == 1))
        table.addElement(row)
    doc.text.addElement(table)


def make_png(path):
    width, height = 360, 200
    pixels = bytearray()
    for y in range(height):
        pixels.append(0)
        for x in range(width):
            if x < 120:
                color = (31, 112, 124)
            elif x < 240:
                color = (225, 158, 57)
            else:
                color = (173, 76, 65)
            if 45 < y < 155 and (x - 180) ** 2 + (y - 100) ** 2 < 48**2:
                color = (245, 241, 226)
            pixels.extend(color)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(pixels)))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def make_svg(path):
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="240" viewBox="0 0 480 240">'
        '<rect width="480" height="240" fill="#f3f6f4"/>'
        '<path d="M55 195H440M65 35V195" stroke="#536b6d" stroke-width="2"/>'
        '<path d="M65 155H440M65 115H440M65 75H440" stroke="#cad5d1" stroke-width="1"/>'
        '<rect x="105" y="115" width="58" height="80" fill="#1f707c"/>'
        '<rect x="210" y="75" width="58" height="120" fill="#e19e39"/>'
        '<rect x="315" y="45" width="58" height="150" fill="#ad4c41"/>'
        '<path d="M134 103L239 60L344 31" fill="none" stroke="#263e40" stroke-width="4"/>'
        '<circle cx="134" cy="103" r="6" fill="#263e40"/><circle cx="239" cy="60" r="6" fill="#263e40"/><circle cx="344" cy="31" r="6" fill="#263e40"/>'
        '</svg>'
    )
    path.write_text(svg, encoding="utf-8")


def add_image(doc, path, name, width, height):
    href = doc.addPicture(str(path))
    frame = Frame(name=name, anchortype="paragraph", width=width, height=height)
    frame.addElement(Image(href=href, type="simple", show="embed", actuate="onLoad"))
    image_paragraph = P(stylename="BodyText")
    image_paragraph.addElement(frame)
    doc.text.addElement(image_paragraph)


def create_basic(output):
    doc = new_document("01 - Text and formatting")
    paragraph(doc, "Compatibility Test Documents", "DocumentTitle")
    paragraph(doc, "This short sample checks ordinary paragraphs, character styles, lists, links, and Unicode text.")
    heading(doc, "Character formatting")
    line = P(stylename="BodyText")
    line.addText("A single paragraph contains ")
    line.addElement(Span(text="bold text", stylename="BoldRun"))
    line.addText(", ")
    line.addElement(Span(text="italic text", stylename="ItalicRun"))
    line.addText(", and ")
    line.addElement(Span(text="colored text", stylename="ColorRun"))
    line.addText(".")
    doc.text.addElement(line)
    add_style(doc, "BoldRun", "text", text={"fontweight": "bold"})
    add_style(doc, "ItalicRun", "text", text={"fontstyle": "italic"})
    add_style(doc, "ColorRun", "text", text={"color": "#ad4c41"})
    heading(doc, "Lists and links")
    add_bullet_list(doc, ["First item with a short line.", "Second item with a longer sentence to check wrapping in a list paragraph.", "Third item."])
    link_line = P(stylename="BodyText")
    link_line.addText("Example link: ")
    link_line.addElement(A(href="https://example.invalid/compatibility", text="compatibility test destination"))
    doc.text.addElement(link_line)
    heading(doc, "Unicode and punctuation")
    paragraph(doc, "Accents: caf\u00e9, na\u00efve, S\u00e3o Paulo. Symbols: \u00a9 \u00b1 \u20ac \u03a9. CJK: \u6f22\u5b57. Quotes: \u201ccurly\u201d and \u2018single\u2019.")
    doc.save(str(output))


def create_layout(output):
    doc = new_document("02 - Page layout", landscape=True, running_header=True)
    paragraph(doc, "Page layout and repeated furniture", "DocumentTitle")
    paragraph(doc, "Landscape letter page with a running header, an automatic page number, varied paragraph spacing, and a deliberate page break.")
    heading(doc, "First page")
    paragraph(doc, "The top and bottom margins leave room for the repeating header and footer. Text should remain inside the printable area without colliding with either.")
    for index in range(1, 5):
        paragraph(doc, f"Layout paragraph {index}: A compact line of text used to check line spacing and alignment across a wide page.")
    doc.text.addElement(H(outlinelevel="1", stylename="PageBreakHeading", text="Second page begins here"))
    paragraph(doc, "The page number in the footer should advance on this page. The header should repeat at the same position.")
    heading(doc, "Alignment samples")
    for name, align in (("Left aligned", "start"), ("Centered", "center"), ("Right aligned", "end")):
        style_name = name.replace(" ", "")
        add_style(doc, style_name, "paragraph", paragraph={"textalign": align}, text={"fontfamily": "Liberation Sans", "fontsize": "11pt"})
        paragraph(doc, name + " paragraph", style_name)
    doc.save(str(output))


def create_tables(output):
    doc = new_document("03 - Tables and pagination", running_header=True)
    paragraph(doc, "Tables and pagination", "DocumentTitle")
    paragraph(doc, "This sample combines a merged heading cell, a repeated table header, alternating row fills, and enough rows to cross page boundaries.")
    heading(doc, "Merged cells and table header")
    add_data_table(doc, many_rows=True, merged=True)
    doc.save(str(output))


def create_graphics(output, assets):
    doc = new_document("04 - Images and graphics")
    paragraph(doc, "Embedded images and graphics", "DocumentTitle")
    paragraph(doc, "Both figures below are embedded in the document package, rather than linked to an external file.")
    heading(doc, "Raster image")
    add_image(doc, assets / "sample.png", "Embedded color test image", "4.8in", "2.67in")
    paragraph(doc, "Figure 1. Embedded PNG with broad color regions and a contrasting central shape.", "Caption")
    heading(doc, "Vector graphic")
    add_image(doc, assets / "sample.svg", "Embedded vector chart", "5.2in", "2.6in")
    paragraph(doc, "Figure 2. Embedded SVG chart made from vector shapes and strokes.", "Caption")
    paragraph(doc, "Image checks: preserve aspect ratio, retain colors, and avoid clipping or unexpected anchoring.")
    doc.save(str(output))


def create_mixed(output, assets):
    doc = new_document("05 - Mixed content stress", running_header=True)
    paragraph(doc, "Mixed content stress sample", "DocumentTitle")
    paragraph(doc, "A longer document mixing styles, a table, embedded graphics, a footnote, and page transitions.")
    heading(doc, "Summary")
    paragraph(doc, "This file is intentionally varied. It is useful for checking whether common objects retain their relationships when the document is edited, saved, and reopened.")
    add_bullet_list(doc, ["Text reflow around nearby objects", "Table width and cell padding", "Header and footer persistence", "Embedded graphic integrity"])
    heading(doc, "Status table")
    add_data_table(doc, many_rows=False, merged=False)
    heading(doc, "Reference image")
    add_image(doc, assets / "sample.png", "Mixed sample image", "3.4in", "1.89in")
    paragraph(doc, "Figure 1. A compact embedded raster image preceding a note.", "Caption")
    note_para = P(stylename="BodyText")
    note_para.addText("The following statement has a footnote")
    note = Note(noteclass="footnote", id="sample-footnote")
    note.addElement(NoteCitation(text="1"))
    note_body = NoteBody()
    note_body.addElement(P(stylename="BodyText", text="Footnote content should remain attached to its citation after editing."))
    note.addElement(note_body)
    note_para.addElement(note)
    note_para.addText(".")
    doc.text.addElement(note_para)
    doc.text.addElement(H(outlinelevel="1", stylename="PageBreakHeading", text="Continuation page"))
    paragraph(doc, "Page two confirms continued flow after a deliberate page break while retaining the same running header and page numbering.")
    add_image(doc, assets / "sample.svg", "Mixed sample vector chart", "4.5in", "2.25in")
    paragraph(doc, "Figure 2. Embedded vector graphic on the continuation page.", "Caption")
    for index in range(1, 8):
        paragraph(doc, f"Additional paragraph {index}: Repeated prose adds enough content to exercise normal page flow without relying on a single oversized object.")
    doc.save(str(output))


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="odt-test-assets-") as temp_dir:
        assets = Path(temp_dir)
        make_png(assets / "sample.png")
        make_svg(assets / "sample.svg")
        create_basic(OUTPUT / "01-text-and-formatting.odt")
        create_layout(OUTPUT / "02-page-layout.odt")
        create_tables(OUTPUT / "03-tables-and-pagination.odt")
        create_graphics(OUTPUT / "04-images-and-graphics.odt", assets)
        create_mixed(OUTPUT / "05-mixed-content-stress.odt", assets)
    print(f"Created 5 ODT samples in {OUTPUT}")


if __name__ == "__main__":
    main()