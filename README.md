# ODT Compatibility Samples

Eight editable OpenDocument Text files cover progressively richer word-processing features and realistic document types:

- `samples/01-text-and-formatting.odt`: character styles, headings, lists, a hyperlink, and Unicode text.
- `samples/02-page-layout.odt`: landscape page setup, repeated header/footer, page numbers, alignment, and an explicit page break.
- `samples/03-tables-and-pagination.odt`: merged cells, a repeating table heading, alternating fills, and a multipage table.
- `samples/04-images-and-graphics.odt`: embedded PNG and SVG figures with captions.
- `samples/05-mixed-content-stress.odt`: combined page furniture, lists, table, embedded images, footnote, and page break.
- `samples/06-din-5008-business-letter.odt`: German business letter with sender and recipient addresses, date, subject, offer details, closing, and enclosure line on A4 paper.
- `samples/07-curriculum-vitae.odt`: one-page professional CV with profile, work history, education, skills, and professional development.
- `samples/08-scientific-report-with-indexes.odt`: research report with abstract, automatic table of contents, illustration index, numbered figure captions, embedded charts, methods, results, discussion, and references.

The people, organizations, addresses, phone numbers, and results in these realistic samples are fictional placeholders.

The PNG and SVG are generated temporarily and embedded in the documents. Regenerate the samples with:

```sh
python3 -m venv .venv
.venv/bin/pip install odfpy
.venv/bin/python generate_samples.py
```

All eight files were opened and rendered to PDF by LibreOffice as a smoke check. The PDFs are not included; the ODT files are the test artifacts.