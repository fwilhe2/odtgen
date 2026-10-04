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
    IllustrationIndex,
    IllustrationIndexEntryTemplate,
    IllustrationIndexSource,
    IndexBody,
    IndexEntryLinkEnd,
    IndexEntryLinkStart,
    IndexEntryPageNumber,
    IndexEntryTabStop,
    IndexEntryText,
    IndexTitle,
    IndexTitleTemplate,
    List,
    ListItem,
    ListLevelStyleBullet,
    ListStyle,
    LineBreak,
    Note,
    NoteBody,
    NoteCitation,
    P,
    PageNumber,
    Sequence,
    Span,
    TableOfContent,
    TableOfContentEntryTemplate,
    TableOfContentSource,
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


def new_document(title, *, landscape=False, running_header=False, a4=False, header_text=None, footer_label="Compatibility sample"):
    doc = OpenDocumentText()
    doc.meta.addElement(Title(text=title))
    doc.meta.addElement(Subject(text="Word processor compatibility test sample"))
    add_common_styles(doc)

    page_layout = PageLayout(name="TestPageLayout")
    page_layout.addElement(
        PageLayoutProperties(
            pagewidth="11in" if landscape else "8.27in" if a4 else "8.5in",
            pageheight="8.5in" if landscape else "11.69in" if a4 else "11in",
            printorientation="landscape" if landscape else "portrait",
            margin="0.7in",
        )
    )
    doc.automaticstyles.addElement(page_layout)
    master = MasterPage(name="Standard", pagelayoutname="TestPageLayout")
    if running_header:
        header = Header()
        header.addElement(P(stylename="HeaderText", text=header_text or title))
        master.addElement(header)
        footer = Footer()
        footer_line = P(stylename="HeaderText")
        footer_line.addText(f"{footer_label}  |  Page ")
        footer_line.addElement(PageNumber(selectpage="current"))
        footer.addElement(footer_line)
        master.addElement(footer)
    doc.masterstyles.addElement(master)
    return doc


def paragraph(doc, text, style="BodyText"):
    doc.text.addElement(P(stylename=style, text=text))


def line_block(doc, lines, style="BodyText"):
    block = P(stylename=style)
    for index, line in enumerate(lines):
        if index:
            block.addElement(LineBreak())
        block.addText(line)
    doc.text.addElement(block)


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


def add_index_templates(source, levels, template_type):
    for level in range(1, levels + 1):
        template = template_type(outlinelevel=str(level), stylename=f"IndexLevel{level}")
        template.addElement(IndexEntryLinkStart())
        template.addElement(IndexEntryText())
        template.addElement(IndexEntryTabStop(type="right", leaderchar="."))
        template.addElement(IndexEntryPageNumber())
        template.addElement(IndexEntryLinkEnd())
        source.addElement(template)


def add_table_of_contents(doc):
    index = TableOfContent(name="Contents", protected="false")
    source = TableOfContentSource(outlinelevel="3")
    source.addElement(IndexTitleTemplate(stylename="IndexTitle"))
    add_index_templates(source, 3, TableOfContentEntryTemplate)
    index.addElement(source)
    body = IndexBody()
    title = IndexTitle(name="Contents")
    title.addElement(P(stylename="IndexTitle", text="Contents"))
    body.addElement(title)
    entries = (
        ("Abstract", 1),
        ("Introduction", 4),
        ("Methods", 4),
        ("Results", 4),
        ("Discussion", 5),
        ("Conclusion", 5),
        ("References", 5),
    )
    for entry, page in entries:
        leaders = "." * max(4, 48 - len(entry))
        body.addElement(P(stylename="IndexLevel1", text=f"{entry} {leaders} {page}"))
    index.addElement(body)
    doc.text.addElement(index)


def add_illustration_index(doc):
    index = IllustrationIndex(name="List of Figures", protected="false")
    source = IllustrationIndexSource(captionsequencename="Illustration")
    source.addElement(IndexTitleTemplate(stylename="IndexTitle"))
    template = IllustrationIndexEntryTemplate(stylename="IndexLevel1")
    template.addElement(IndexEntryText())
    template.addElement(IndexEntryTabStop(type="right", leaderchar="."))
    template.addElement(IndexEntryPageNumber())
    source.addElement(template)
    index.addElement(source)
    body = IndexBody()
    title = IndexTitle(name="List of Figures")
    title.addElement(P(stylename="IndexTitle", text="List of Figures"))
    body.addElement(title)
    body.addElement(P(stylename="IndexLevel1", text="Figure 1. Mean weekday demand by building category .......... 4"))
    body.addElement(P(stylename="IndexLevel1", text="Figure 2. Mean absolute error by forecast horizon ........... 5"))
    index.addElement(body)
    doc.text.addElement(index)


def add_figure_caption(doc, number, caption):
    caption_line = P(stylename="Caption")
    caption_line.addText("Figure ")
    caption_line.addElement(
        Sequence(name="Illustration", refname=f"figure{number}", formula="ooow:Figure", text=str(number))
    )
    caption_line.addText(f". {caption}")
    doc.text.addElement(caption_line)


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


def make_report_charts(directory):
    demand = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="240" viewBox="0 0 480 240">'
        '<rect width="480" height="240" fill="#ffffff"/>'
        '<path d="M55 25V190H455M55 150H455M55 110H455M55 70H455" stroke="#cbd5d1" fill="none"/>'
        '<text x="18" y="75" font-size="11">120</text><text x="24" y="115" font-size="11">80</text>'
        '<text x="24" y="155" font-size="11">40</text>'
        '<rect x="95" y="125" width="54" height="65" fill="#287271"/>'
        '<rect x="190" y="100" width="54" height="90" fill="#287271"/>'
        '<rect x="285" y="80" width="54" height="110" fill="#287271"/>'
        '<rect x="380" y="68" width="54" height="122" fill="#287271"/>'
        '<text x="93" y="210" font-size="11">Library</text><text x="186" y="210" font-size="11">Lab</text>'
        '<text x="276" y="210" font-size="11">Office</text><text x="375" y="210" font-size="11">Housing</text>'
        '<text x="120" y="231" font-size="12">Mean weekday demand (kWh)</text></svg>'
    )
    error = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="240" viewBox="0 0 480 240">'
        '<rect width="480" height="240" fill="#ffffff"/>'
        '<path d="M55 25V190H455M55 150H455M55 110H455M55 70H455" stroke="#cbd5d1" fill="none"/>'
        '<text x="20" y="75" font-size="11">16</text><text x="20" y="115" font-size="11">10</text>'
        '<text x="26" y="155" font-size="11">4</text>'
        '<path d="M85 149L170 130L255 110L340 95L425 78" fill="none" stroke="#ad4c41" stroke-width="4"/>'
        '<circle cx="85" cy="149" r="5" fill="#ad4c41"/><circle cx="170" cy="130" r="5" fill="#ad4c41"/>'
        '<circle cx="255" cy="110" r="5" fill="#ad4c41"/><circle cx="340" cy="95" r="5" fill="#ad4c41"/>'
        '<circle cx="425" cy="78" r="5" fill="#ad4c41"/>'
        '<text x="74" y="210" font-size="11">1 day</text><text x="158" y="210" font-size="11">2 days</text>'
        '<text x="243" y="210" font-size="11">3 days</text><text x="328" y="210" font-size="11">4 days</text>'
        '<text x="411" y="210" font-size="11">5 days</text>'
        '<text x="135" y="231" font-size="12">Forecast horizon (mean absolute error, %)</text></svg>'
    )
    (directory / "demand.svg").write_text(demand, encoding="utf-8")
    (directory / "forecast-error.svg").write_text(error, encoding="utf-8")


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


def create_din_letter(output):
    doc = new_document("06 - DIN 5008 business letter", a4=True)
    add_style(doc, "SenderLine", "paragraph", paragraph={"marginbottom": "0.05in"}, text={"fontfamily": "Liberation Sans", "fontsize": "9pt", "color": "#555555"})
    add_style(doc, "Address", "paragraph", paragraph={"marginbottom": "0in"}, text={"fontfamily": "Liberation Sans", "fontsize": "11pt"})
    add_style(doc, "DateLine", "paragraph", paragraph={"textalign": "end", "marginbottom": "0.28in"}, text={"fontfamily": "Liberation Sans", "fontsize": "10pt"})
    add_style(doc, "Subject", "paragraph", paragraph={"margintop": "0.24in", "marginbottom": "0.18in", "keepwithnext": "always"}, text={"fontfamily": "Liberation Sans", "fontsize": "12pt", "fontweight": "bold", "color": "#174a5b"})
    paragraph(doc, "Muster Umwelttechnik GmbH  |  Beispielstra\u00dfe 1  |  00000 Musterstadt", "SenderLine")
    line_block(doc, ["Erika Musterfrau", "Beispielstra\u00dfe 1", "00000 Musterstadt", "Telefon: +49 000 0000000  |  erika.musterfrau@example.invalid"], "Address")
    paragraph(doc, "", "BodyText")
    line_block(doc, ["Beispiel Geb\u00e4udemanagement GmbH", "Einkauf", "Musterweg 2", "00000 Musterstadt"], "Address")
    paragraph(doc, "Musterstadt, 4. Oktober 2026", "DateLine")
    paragraph(doc, "Angebot zur energetischen Bestandsaufnahme am Standort Musterweg", "Subject")
    paragraph(doc, "Sehr geehrte Damen und Herren,")
    paragraph(doc, "vielen Dank f\u00fcr Ihre Anfrage vom 28. September. Gern bieten wir Ihnen die energetische Bestandsaufnahme Ihres Verwaltungsgeb\u00e4udes mit rund 6.200 m\u00b2 Nutzfl\u00e4che an.")
    paragraph(doc, "Unser Leistungsumfang umfasst die Sichtung der Verbrauchsdaten der letzten drei Jahre, eine Begehung der technischen Anlagen sowie einen priorisierten Ma\u00dfnahmenplan. Die Ergebnisse stellen wir in einem Bericht mit Kostenrahmen und erwarteter CO2-Einsparung zusammen.")
    paragraph(doc, "Das Pauschalhonorar betr\u00e4gt 8.400,00 EUR netto zuz\u00fcglich der gesetzlichen Umsatzsteuer. Die Bearbeitungszeit betr\u00e4gt vier Wochen ab Beauftragung und Eingang der vollst\u00e4ndigen Unterlagen. Dieses Angebot ist bis zum 30. November 2026 g\u00fcltig.")
    paragraph(doc, "F\u00fcr ein kurzes Abstimmungsgespr\u00e4ch stehen wir Ihnen gern zur Verf\u00fcgung. Wir freuen uns auf die Zusammenarbeit.")
    paragraph(doc, "Mit freundlichen Gr\u00fc\u00dfen")
    line_block(doc, ["Erika Musterfrau", "Gesch\u00e4ftsf\u00fchrerin"])
    paragraph(doc, "Anlage: Leistungsbeschreibung und Zeitplan", "SenderLine")
    doc.save(str(output))


def create_cv(output):
    doc = new_document("07 - Curriculum vitae", a4=True, running_header=True, header_text="Max Mustermann", footer_label="Curriculum vitae")
    add_style(doc, "ContactLine", "paragraph", paragraph={"marginbottom": "0.16in"}, text={"fontfamily": "Liberation Sans", "fontsize": "10pt", "color": "#555555"})
    add_style(doc, "Role", "paragraph", paragraph={"margintop": "0.08in", "marginbottom": "0.02in", "keepwithnext": "always"}, text={"fontfamily": "Liberation Sans", "fontsize": "11pt", "fontweight": "bold"})
    add_style(doc, "CVDate", "paragraph", paragraph={"marginbottom": "0.06in"}, text={"fontfamily": "Liberation Sans", "fontsize": "9pt", "fontstyle": "italic", "color": "#555555"})
    paragraph(doc, "Max Mustermann", "DocumentTitle")
    paragraph(doc, "Data scientist  |  Musterstadt, Germany  |  max.mustermann@example.invalid  |  +49 000 0000000", "ContactLine")
    heading(doc, "Profile")
    paragraph(doc, "Applied data scientist with seven years of experience building forecasting and decision-support systems for energy and infrastructure teams. Combines statistical modelling with practical delivery, clear documentation, and close collaboration with domain experts.")
    heading(doc, "Professional experience")
    paragraph(doc, "Senior Data Scientist | Muster Energieanalyse, Musterstadt", "Role")
    paragraph(doc, "2022-present", "CVDate")
    add_bullet_list(doc, [
        "Led development of day-ahead demand forecasts for 38 commercial buildings, reducing portfolio-level mean absolute error by 17%.",
        "Built reproducible Python pipelines for meter-data quality checks, feature generation, model evaluation, and monthly reporting.",
        "Worked with energy managers to translate model outputs into an operational dashboard and a documented review process.",
    ])
    paragraph(doc, "Data Scientist | Beispiel Mobilit\u00e4tsforschung, Musterstadt", "Role")
    paragraph(doc, "2019-2022", "CVDate")
    add_bullet_list(doc, [
        "Analysed public-transport demand and service reliability using time-series and geospatial methods.",
        "Designed an experiment to evaluate timetable changes across 12 routes; presented findings to city and operator stakeholders.",
    ])
    heading(doc, "Education")
    paragraph(doc, "M.Sc. Statistics | Example University | 2017-2019", "Role")
    paragraph(doc, "Thesis: Probabilistic forecasting for sparse, weather-sensitive demand series.")
    paragraph(doc, "B.Sc. Mathematics | Example University | 2014-2017", "Role")
    heading(doc, "Skills")
    paragraph(doc, "Methods: time-series forecasting, regression, experimental design, uncertainty estimation, model monitoring")
    paragraph(doc, "Tools: Python, SQL, pandas, scikit-learn, statsmodels, Git, PostgreSQL, Power BI")
    paragraph(doc, "Languages: German (native), English (C1), Danish (B1)")
    heading(doc, "Selected professional development")
    paragraph(doc, "Energy Data Management Certificate | Example Academy | 2023")
    paragraph(doc, "Responsible AI in Practice | Example Data School | 2021")
    doc.save(str(output))


def create_scientific_report(output, assets):
    doc = new_document("08 - Scientific report with indexes", a4=True, running_header=True, header_text="Campus energy demand forecasting", footer_label="Research report")
    add_style(doc, "ReportSubtitle", "paragraph", paragraph={"marginbottom": "0.16in"}, text={"fontfamily": "Liberation Sans", "fontsize": "13pt", "color": "#287271"})
    add_style(doc, "IndexTitle", "paragraph", paragraph={"margintop": "0.12in", "marginbottom": "0.08in", "keepwithnext": "always"}, text={"fontfamily": "Liberation Sans", "fontsize": "14pt", "fontweight": "bold", "color": "#174a5b"})
    for level in range(1, 4):
        add_style(doc, f"IndexLevel{level}", "paragraph", paragraph={"marginleft": f"{(level - 1) * 0.18}in", "marginbottom": "0.04in"}, text={"fontfamily": "Liberation Serif", "fontsize": "10pt"})
    add_style(doc, "FrontMatterBreak", "paragraph", paragraph={"breakbefore": "page", "marginbottom": "0in"})
    paragraph(doc, "Day-ahead electricity demand forecasting for a university campus", "DocumentTitle")
    paragraph(doc, "A retrospective evaluation across four building categories", "ReportSubtitle")
    line_block(doc, ["Max Mustermann, Ph.D.", "Example Research Lab", "4 October 2026"])
    heading(doc, "Abstract")
    paragraph(doc, "Accurate short-term demand forecasts can help campus energy teams schedule flexible loads and investigate unusual consumption. This study evaluates a gradient-boosted forecasting model using hourly meter readings from 24 buildings over 18 months. A rolling-origin evaluation shows that error increases with forecast horizon, while building-level demand profiles remain materially different. The results support horizon-aware operational thresholds and routine review of meter quality.")
    paragraph(doc, "Keywords: electricity demand; load forecasting; campus energy; rolling-origin evaluation", "SenderLine")
    paragraph(doc, "", "FrontMatterBreak")
    add_table_of_contents(doc)
    paragraph(doc, "", "FrontMatterBreak")
    add_illustration_index(doc)
    paragraph(doc, "", "FrontMatterBreak")
    heading(doc, "Introduction")
    paragraph(doc, "Building operations account for a substantial share of campus energy use, but daily demand is shaped by occupancy, weather, and schedules that vary across facilities. Forecasts can support procurement and the timing of flexible loads, provided their uncertainty is understood by the people using them.")
    paragraph(doc, "We assess whether a single forecasting workflow can provide useful day-ahead estimates across a mixed building portfolio. The analysis focuses on out-of-sample error by building category and forecast horizon, rather than on a single portfolio-wide score.")
    heading(doc, "Methods")
    paragraph(doc, "The dataset contains hourly electricity readings from 24 campus buildings between January 2024 and June 2025. Records with missing intervals were excluded from model fitting; calendar features and observed outdoor temperature were used as predictors. Buildings were grouped into library, laboratory, office, and housing categories for descriptive comparison.")
    paragraph(doc, "We used a gradient-boosted regression model and evaluated it with a rolling-origin procedure. At each origin, the model was trained on all prior observations and forecast one to five days ahead. Performance was summarized using mean absolute error (MAE), reported as a percentage of mean observed demand. This retrospective design avoids using future observations in model fitting.")
    heading(doc, "Results")
    paragraph(doc, "Mean weekday demand differed across building categories, with housing and laboratory facilities contributing the highest average loads in the evaluation period (Figure 1). Forecast error increased from 7.1% at a one-day horizon to 14.8% at five days (Figure 2). The direction of this increase was consistent across the rolling evaluation windows.")
    add_image(doc, assets / "demand.svg", "Mean weekday electricity demand by building category", "5.7in", "2.85in")
    add_figure_caption(doc, 1, "Mean weekday electricity demand by building category. Values are illustrative normalized means from the evaluation cohort.")
    add_image(doc, assets / "forecast-error.svg", "Forecast error by horizon", "5.7in", "2.85in")
    add_figure_caption(doc, 2, "Mean absolute error as a percentage of observed demand by forecast horizon.")
    heading(doc, "Discussion")
    paragraph(doc, "The results indicate that a campus-wide forecast should be accompanied by horizon-specific error expectations. Category-level differences also argue against interpreting a single aggregate score as representative of every facility. Operational use should retain building-level checks and flag abrupt changes in meter coverage or occupancy schedules.")
    paragraph(doc, "This study has limitations. The evaluation covers one campus and one model family, and the available weather inputs do not capture every local condition. Future work should compare probabilistic forecasts and assess whether forecast-guided interventions reduce peak demand without shifting consumption to less favorable periods.")
    heading(doc, "Conclusion")
    paragraph(doc, "Rolling-origin evaluation provides a practical view of how forecast quality changes with lead time. For the evaluated campus portfolio, day-ahead estimates were more reliable than longer-range estimates, and building category remained important to interpreting demand. These findings favor transparent, horizon-aware deployment over a single undifferentiated accuracy target.")
    heading(doc, "References")
    paragraph(doc, "Hyndman, R. J., & Athanasopoulos, G. (2021). Forecasting: Principles and Practice (3rd ed.). OTexts.")
    paragraph(doc, "Hong, T., Pinson, P., & Fan, S. (2014). Global energy forecasting competition 2012. International Journal of Forecasting, 30(2), 357-363.")
    doc.save(str(output))


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="odt-test-assets-") as temp_dir:
        assets = Path(temp_dir)
        make_png(assets / "sample.png")
        make_svg(assets / "sample.svg")
        make_report_charts(assets)
        create_basic(OUTPUT / "01-text-and-formatting.odt")
        create_layout(OUTPUT / "02-page-layout.odt")
        create_tables(OUTPUT / "03-tables-and-pagination.odt")
        create_graphics(OUTPUT / "04-images-and-graphics.odt", assets)
        create_mixed(OUTPUT / "05-mixed-content-stress.odt", assets)
        create_din_letter(OUTPUT / "06-din-5008-business-letter.odt")
        create_cv(OUTPUT / "07-curriculum-vitae.odt")
        create_scientific_report(OUTPUT / "08-scientific-report-with-indexes.odt", assets)
    print(f"Created 8 ODT samples in {OUTPUT}")


if __name__ == "__main__":
    main()