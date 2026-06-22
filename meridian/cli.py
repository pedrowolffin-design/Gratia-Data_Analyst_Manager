"""Command-line entry point: build the model and emit all deliverables."""

from __future__ import annotations

from .formatting import money
from .loaders import load_inputs, project_root
from .model import build_model
from .writers import write_outputs


def main() -> int:
    root = project_root()
    model = build_model(load_inputs(root))
    output_dir = root / "outputs"
    write_outputs(model, output_dir)

    totals = model["validation"]["totals"]
    print(f"Generated Meridian {model['period']['label']} treasury deliverables")
    print(f"Output directory: {output_dir}")
    print(f"Reported cash: {money(totals['reported_cash_usd'])}")
    print(f"Corrected cash: {money(totals['corrected_cash_usd'])}")
    print(f"Available credit: {money(totals['available_credit_usd'])}")
    print(f"Total liquidity: {money(totals['total_liquidity_usd'])}")
    print(f"Submission status: {model['validation']['submission_status']}")
    return 0
