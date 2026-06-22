"""Minimal stdlib-only .docx writer (OOXML zip, no third-party deps).

Renders a small subset of Markdown into real Word formatting via direct run
properties (no styles part needed):

* ``#`` / ``##`` / ``###`` headings -> bold, sized, with spacing above
* ``- `` lines -> indented bullet paragraphs
* ``**bold**`` inline spans -> bold runs

Blank lines are dropped; spacing is carried by paragraph properties instead.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    "</Types>"
)

ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/></Relationships>'
)

# Heading prefix -> (font size in half-points, spacing-before in twentieths of a point).
HEADINGS = {
    "### ": (26, 180),
    "## ": (28, 240),
    "# ": (36, 280),
}
BODY_SIZE = 22  # 11pt


def write_docx(path: Path, markdown_text: str) -> None:
    body = "".join(_block(line) for line in markdown_text.splitlines() if line.strip())
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}"
        '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" '
        'w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body></w:document>'
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("_rels/.rels", ROOT_RELS)
        archive.writestr("word/document.xml", document_xml)


def _block(line: str) -> str:
    for prefix, (size, space_before) in HEADINGS.items():
        if line.startswith(prefix):
            return _paragraph(line[len(prefix):], size=size, bold=True, space_before=space_before)
    if line.startswith("- "):
        return _paragraph("•\t" + line[2:], size=BODY_SIZE, space_before=40, hanging=True)
    return _paragraph(line, size=BODY_SIZE, space_before=80)


def _paragraph(
    text: str, *, size: int, bold: bool = False, space_before: int = 0, hanging: bool = False
) -> str:
    props = []
    if space_before:
        props.append(f'<w:spacing w:before="{space_before}"/>')
    if hanging:
        props.append('<w:ind w:left="360" w:hanging="220"/>')
    ppr = f"<w:pPr>{''.join(props)}</w:pPr>" if props else ""
    return f"<w:p>{ppr}{_runs(text, size=size, base_bold=bold)}</w:p>"


def _runs(text: str, *, size: int, base_bold: bool) -> str:
    runs = []
    for index, segment in enumerate(text.split("**")):
        if not segment:
            continue
        bold = base_bold or index % 2 == 1  # odd segments sit between ** markers
        bold_tag = "<w:b/>" if bold else ""
        runs.append(
            f"<w:r><w:rPr>{bold_tag}<w:sz w:val=\"{size}\"/><w:szCs w:val=\"{size}\"/></w:rPr>"
            f'<w:t xml:space="preserve">{escape(segment)}</w:t></w:r>'
        )
    return "".join(runs)
