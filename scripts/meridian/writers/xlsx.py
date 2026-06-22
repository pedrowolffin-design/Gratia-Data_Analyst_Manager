"""Minimal stdlib-only .xlsx writer plus the workbook layout.

Sheet contents are described declaratively in ``DATA_SHEETS`` (a column-key
list per tab) so adding/reordering columns is a one-line change rather than
editing parallel header and row-extraction blocks. The OOXML helpers below
hand-build the spreadsheet package — no third-party dependency.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

WARNING = "DRAFT / BLOCKED: do not submit until the 2026-04-28 stale cash row is refreshed."

# Style index (into styles.xml cellXfs) applied to LTV fraction cells.
PERCENT_STYLE = 1


class Percent(float):
    """A percentage value such as ``58.0`` (meaning 58%).

    Rendered to Excel as the fraction 0.58 with a ``0.00`` number format so it
    displays as ``0.58`` (plain decimal) rather than ``58.0%``.
    """


def _cell(column: str, value: Any) -> Any:
    """Wrap numeric ``*_Pct`` columns so they render as plain two-decimal fractions."""
    if column.endswith("_Pct") and isinstance(value, (int, float)) and not isinstance(value, bool):
        return Percent(value)
    return value

LIQUIDITY_COLUMNS = [
    "Fund_ID",
    "Fund_Name",
    "Corrected_Cash_USD",
    "Available_Credit_USD",
    "Total_Liquidity_USD",
    "Current_LTV_Pct",
    "Covenant_LTV_Max_Pct",
    "LTV_Headroom_Pct",
]

# (sheet title, column keys, model key). Column keys double as header labels and
# as the dict keys used to extract each row's cells.
DATA_SHEETS: list[tuple[str, list[str], str]] = [
    (
        "Cash by Currency",
        ["Fund_ID", "Fund_Name", "Currency", "Corrected_Balance_USD"],
        "currency",
    ),
    (
        "Cash by Account Type",
        ["Fund_ID", "Fund_Name", "Account_Type", "Corrected_Balance_USD"],
        "account_type",
    ),
    (
        "Cash Detail",
        [
            "Fund_ID",
            "Fund_Name",
            "Bank",
            "Account_Number",
            "Currency",
            "Balance_Local",
            "Reported_Balance_USD",
            "Corrected_Balance_USD",
            "USD_Variance",
            "As_Of_Date",
            "Account_Type",
            "FX_Rate_Used",
        ],
        "cash",
    ),
    (
        "Credit Facilities",
        [
            "Fund_ID",
            "Fund_Name",
            "Facility_Size_USD",
            "Drawn_Amount_USD",
            "Available_USD",
            "Maturity_Date",
            "Lender",
            "Covenant_LTV_Max_Pct",
            "Current_LTV_Pct",
            "LTV_Headroom_Pct",
            "Facility_Math_Variance_USD",
        ],
        "credit",
    ),
    (
        "Wire Review",
        [
            "Date",
            "Parsed_Fund_ID",
            "From_Account",
            "To_Account",
            "Amount_USD",
            "Currency",
            "Purpose",
            "Approved_By",
            "Approver_Count",
            "Status",
            "Reference",
        ],
        "wire",
    ),
    (
        "Issues",
        [
            "Severity",
            "Category",
            "Fund_ID",
            "Reference",
            "Title",
            "Description",
            "Why_It_Matters",
            "Recommendation",
        ],
        "issues",
    ),
]


def build_workbook_sheets(model: dict[str, Any]) -> dict[str, list[list[Any]]]:
    sheets: dict[str, list[list[Any]]] = {"Executive Summary": _executive_summary_sheet(model)}
    for title, columns, model_key in DATA_SHEETS:
        sheets[title] = _data_sheet(columns, model[model_key])
    return sheets


def _data_sheet(columns: list[str], rows: list[dict[str, Any]]) -> list[list[Any]]:
    sheet: list[list[Any]] = [[WARNING], [], list(columns)]
    for row in rows:
        sheet.append([_cell(key, row.get(key, "")) for key in columns])
    return sheet


def _executive_summary_sheet(model: dict[str, Any]) -> list[list[Any]]:
    totals = model["validation"]["totals"]
    sheet: list[list[Any]] = [
        ["Meridian Capital Partners - April 2026 Treasury Report"],
        [WARNING],
        [],
        ["Metric", "Amount USD"],
        ["Corrected Cash", totals["corrected_cash_usd"]],
        ["Available Credit", totals["available_credit_usd"]],
        ["Total Liquidity", totals["total_liquidity_usd"]],
        [],
        list(LIQUIDITY_COLUMNS),
    ]
    for row in model["liquidity"]:
        sheet.append([_cell(key, row.get(key, "")) for key in LIQUIDITY_COLUMNS])
    return sheet


def write_xlsx(path: Path, sheets: dict[str, list[list[Any]]]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types(len(sheets)))
        archive.writestr("_rels/.rels", _root_rels())
        archive.writestr("xl/workbook.xml", _workbook_xml(list(sheets)))
        archive.writestr("xl/_rels/workbook.xml.rels", _workbook_rels(len(sheets)))
        archive.writestr("xl/styles.xml", _styles())
        for index, rows in enumerate(sheets.values(), start=1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", _sheet_xml(rows))


def _content_types(sheet_count: int) -> str:
    sheet_overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        f"{sheet_overrides}</Types>"
    )


def _root_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>'
    )


def _workbook_xml(sheet_names: list[str]) -> str:
    sheets = "".join(
        f'<sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
        for index, name in enumerate(sheet_names, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{sheets}</sheets></workbook>"
    )


def _workbook_rels(sheet_count: int) -> str:
    rels = "".join(
        f'<Relationship Id="rId{i}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{i}.xml"/>'
        for i in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{rels}</Relationships>"
    )


def _styles() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<numFmts count="1"><numFmt numFmtId="164" formatCode="0.00"/></numFmts>'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
        '</cellXfs>'
        '</styleSheet>'
    )


def _sheet_xml(rows: list[list[Any]]) -> str:
    row_xml = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            cell_ref = f"{_column_letter(col_index)}{row_index}"
            if isinstance(value, Percent):
                cells.append(f'<c r="{cell_ref}" s="{PERCENT_STYLE}"><v>{float(value) / 100}</v></c>')
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                cells.append(f'<c r="{cell_ref}"><v>{value}</v></c>')
            else:
                cells.append(
                    f'<c r="{cell_ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
                )
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(row_xml)}</sheetData></worksheet>'
    )


def _column_letter(index: int) -> str:
    letters = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters
