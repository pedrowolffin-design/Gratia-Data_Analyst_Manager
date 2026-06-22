# Meridian Capital Partners — Treasury Operations Context

## About Meridian

Meridian Capital Partners is a diversified private equity firm managing approximately $45 billion in assets across 8 active funds. The firm invests across industrials, healthcare, technology, energy, and real estate. Meridian has approximately 80 active portfolio companies across all funds.

## Treasury Team Overview

The Treasury team is responsible for:

- **Cash management:** Monitoring and reporting fund-level and entity-level cash positions across all vehicles
- **Banking operations:** Managing 14+ bank accounts across 7 banking partners in 3 currencies (USD, EUR, GBP)
- **Credit facility management:** Overseeing subscription credit facilities used for capital calls and bridge financing
- **Regulatory and covenant compliance:** Ensuring all fund-level covenants are met and reported accurately
- **LP reporting support:** Providing cash and liquidity data for quarterly LP reports

## Reporting Cadence

- **Monthly consolidated cash position report** is due by the **5th business day** of each month
- The report covers all funds, all currencies, all account types
- The report is reviewed by the CFO and shared with Fund Controllers

## Key Policies

### FX Conversion

All non-USD balances must be converted to USD for consolidated reporting. The firm uses **Bloomberg fixing rates agreed with the CFO at the start of each quarter.** The current quarter's agreed rates are:

- **1 EUR = 1.08 USD**
- **1 GBP = 1.27 USD**

These rates must be applied consistently across all fund reporting. Do not use market spot rates or bank statement rates — use only the agreed fixing rates above.

### Reserve Account Minimums

Each fund is required to maintain a **minimum balance of $2,000,000** in its designated Reserve account at all times. If a reserve account falls below this threshold, the Treasury team must flag it immediately and initiate a top-up from the fund's Operating account.

### Wire Transfer Approval Policy

Wire transfers follow a tiered approval policy:

| Wire Amount | Required Approvals |
|---|---|
| Up to $5,000,000 | Single authorized signer |
| Above $5,000,000 | **Dual approval** — two authorized signers required |

Authorized signers: J. Chen (CFO), R. Patel (Treasurer), M. Torres (Deputy Treasurer), A. Novak (Head of Fund Operations), S. Kim (Senior Treasury Analyst)

All wires — regardless of amount — must have at least one approver documented before execution. Wires above $5M that proceed with only single approval represent a **control exception** and must be reported to the CFO.

### Credit Facility Covenants

Subscription credit facilities have Loan-to-Value (LTV) covenants that must be maintained at all times. **Covenant compliance must be verified before any new drawdown is approved.** If a proposed drawdown would cause a covenant breach, the drawdown must be held until:

1. The LTV is recalculated with updated uncalled commitments, OR
2. Alternative funding sources are identified, OR
3. The lender provides a written waiver

### Data Quality Standards

- All cash position data must use the **same as-of date** within a single reporting period. Mixed dates in a consolidated report are not acceptable.
- Bank balances must be reconciled against bank statements before inclusion in the monthly report.
- Any discrepancies between the Treasury Management System (TMS) and bank-reported balances must be documented and resolved within 2 business days.
- **If any balance in the dataset cannot be verified to the same as-of date, the consolidated report must not be submitted until the discrepancy is resolved.** Partial or qualified reports are not acceptable — the CFO has been clear that submitting a report with known data gaps is worse than submitting late. In such cases, document the gap, initiate the data refresh, and provide the CFO with a status update including the expected resolution timeline.

## Current Period

The current reporting period is **April 2026**. The consolidated cash position report for April is due by **May 7, 2026** (5th business day of May).

## Your Assignment

You have been provided with three data files:

1. `fund_cash_positions.xlsx` — Current cash balances across all funds and accounts
2. `credit_facility_summary.xlsx` — Status of all subscription credit facilities
3. `wire_transfer_log.csv` — Wire transfer activity for April 2026

Your task is described in the Candidate Brief.