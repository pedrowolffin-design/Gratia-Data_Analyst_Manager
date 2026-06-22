import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import meridian as report


class MeridianTreasuryReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = report.load_inputs(ROOT)
        cls.model = report.build_model(cls.inputs)

    def test_cash_as_of_date_check_fails_current_dataset(self):
        self.assertEqual(
            self.model["validation"]["as_of_dates_found"],
            ["2026-04-28", "2026-04-30"],
        )
        blocking_titles = {
            issue["Title"]
            for issue in self.model["issues"]
            if issue["Severity"] == "Blocking"
        }
        self.assertIn("Mixed cash as-of dates", blocking_titles)

    def test_fx_conversion_uses_readme_rates_and_catches_mf004_mismatches(self):
        mismatches = [row for row in self.model["cash"] if abs(row["USD_Variance"]) > 0.01]
        self.assertEqual(len(mismatches), 2)
        self.assertEqual({row["Fund_ID"] for row in mismatches}, {"MF-004"})
        self.assertEqual(sum(row["USD_Variance"] for row in mismatches), 252000.0)
        eur_rows = [row for row in self.model["cash"] if row["Currency"] == "EUR"]
        self.assertTrue(all(row["FX_Rate_Used"] == 1.08 for row in eur_rows))

    def test_reserve_balances_below_minimum_are_flagged(self):
        reserve_issues = [
            issue for issue in self.model["issues"] if issue["Category"] == "Reserve Minimum"
        ]
        self.assertEqual(len(reserve_issues), 8)
        self.assertTrue(all(issue["Severity"] == "High" for issue in reserve_issues))

    def test_wires_over_5m_require_dual_approval(self):
        approval_issues = [
            issue
            for issue in self.model["issues"]
            if issue["Title"] == "Wire above $5M completed with single approval"
        ]
        self.assertEqual(len(approval_issues), 1)
        self.assertEqual(approval_issues[0]["Reference"], "WR-2026-0424")
        self.assertEqual(approval_issues[0]["Fund_ID"], "MF-005")

    def test_wire_fund_ids_parse_from_from_account(self):
        self.assertTrue(all(row["Parsed_Fund_ID"] for row in self.model["wire"]))
        self.assertEqual(
            report.parse_wire_fund_id("MF-003 Citibank Facility"),
            "MF-003",
        )

    def test_credit_facility_math_reconciles(self):
        variances = [row["Facility_Math_Variance_USD"] for row in self.model["credit"]]
        self.assertTrue(all(variance == 0 for variance in variances))

    def test_total_liquidity_equals_corrected_cash_plus_available_credit(self):
        totals = self.model["validation"]["totals"]
        self.assertEqual(totals["corrected_cash_usd"], 439554000.0)
        self.assertEqual(totals["available_credit_usd"], 323000000.0)
        self.assertEqual(totals["total_liquidity_usd"], 762554000.0)
        self.assertEqual(
            totals["corrected_cash_usd"] + totals["available_credit_usd"],
            totals["total_liquidity_usd"],
        )


if __name__ == "__main__":
    unittest.main()
