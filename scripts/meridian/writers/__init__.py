"""Output writers and the orchestrator that emits all deliverables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .docx import write_docx
from .html import write_html
from .memo import build_memo_markdown
from .xlsx import build_workbook_sheets, write_xlsx

__all__ = [
    "write_outputs",
    "build_memo_markdown",
    "write_docx",
    "write_html",
    "write_xlsx",
    "build_workbook_sheets",
]


def write_outputs(model: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    # The memo markdown is still rendered as the source for the .docx, but is no
    # longer written out as a standalone .md file.
    memo_markdown = build_memo_markdown(model)
    write_docx(output_dir / "meridian_april_2026_findings_memo.docx", memo_markdown)
    write_html(output_dir / "meridian_april_2026_interactive.html", model)
    write_xlsx(output_dir / "meridian_april_2026_treasury_report.xlsx", build_workbook_sheets(model))
