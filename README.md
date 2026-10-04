# ODT Compatibility Samples

Five editable OpenDocument Text files cover progressively richer word-processing features:

- `samples/01-text-and-formatting.odt`: character styles, headings, lists, a hyperlink, and Unicode text.
- `samples/02-page-layout.odt`: landscape page setup, repeated header/footer, page numbers, alignment, and an explicit page break.
- `samples/03-tables-and-pagination.odt`: merged cells, a repeating table heading, alternating fills, and a multipage table.
- `samples/04-images-and-graphics.odt`: embedded PNG and SVG figures with captions.
- `samples/05-mixed-content-stress.odt`: combined page furniture, lists, table, embedded images, footnote, and page break.

The PNG and SVG are generated temporarily and embedded in the documents. Regenerate the samples with:

```sh
python3 -m venv .venv
.venv/bin/pip install odfpy
.venv/bin/python generate_samples.py
```

All five files were opened and rendered to PDF by LibreOffice as a smoke check. The PDFs are not included; the ODT files are the test artifacts.