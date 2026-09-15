# account.move.line — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 15 Sep 2026: `fields_get`, `ir.model.fields.modules`, `get_views`, window actions, `default_get`,
`_order`, SQL constraints, every line (33) and the taxes they use. Behaviour the tenant cannot show comes from the Odoo
19.0 source, `addons/account/models/account_move_line.py`. The document is in `account.move.md`.

A journal item is one line of an `account.move`. On an invoice, the lines a user edits are the **product, section
and note lines** (`invoice_line_ids`); Odoo then maintains the **tax** lines and one **payment term** (receivable or
payable) line itself.

## Invoice lines as the invoice form shows them (`invoice_line_ids`, tab Invoice Lines)

Controls: **Add a line** · **Add a section** (`display_type line_section`) · **Add a note** (`line_note`) · **Catalog**.

| Column | Field | Notes |
|---|---|---|
| (drag handle) | `sequence` | |
| **Product** | `product_id` → **product.product** (the variant) | domain `sale_ok` on customer documents, `purchase_ok` on vendor documents; optional "conditional"; read-only on down-payment lines |
| **Label** | `name` | the product's display name and sales description on selection; for sections and notes, the text |
| Malaysian classification code | `l10n_my_edi_classification_code` | optional, hidden; `l10n_my_edi` |
| Deferred Date | `deferred_start_date` / `deferred_end_date` | optional, hidden; `account_accountant` |
| **Quantity** | `quantity` | "The optional quantity expressed by this line, eg: number of product sold." |
| **Unit** | `product_uom_id` → uom.uom | among `allowed_uom_ids` (the product's unit and packagings) |
| **Price** | `price_unit` | Unit Price |
| Disc.% | `discount` | optional, hidden; default 0 |
| **Taxes** | `tax_ids` → account.tax | domain by the document's tax use and country; Taxes bundle |
| Professional | `deductible_percentage` | vendor documents only, optional, hidden |
| **Amount** | `price_subtotal` (Tax Excl.) or `price_total` (Tax Incl.) | by the document's Document Tax Mode |

The line's own form (from the list): Product, Description / Section / Subsection / Note, Quantity, Unit, Price, Disc.%,
Account, Taxes, Amount. Kanban (mobile): product, price, quantity, unit, label.

## Fields that matter for Phase 1 (module `account` unless noted)

| Field | Label | Type | Req | Notes |
|---|---|---|---|---|
| `move_id` | Journal Entry | many2one account.move | yes | |
| `sequence` | Sequence | integer | | product lines 0, 1, 2…; tax lines 10000; payment term line 12000 |
| `display_type` | Display Type | selection | yes | `product` Product · `line_section` Section · `line_subsection` Subsection · `line_note` Note · `tax` Tax · `payment_term` Payment Term · `rounding` · `discount` · `epd` Early Payment Discount · `cogs` · `non_deductible_*` |
| `product_id` | Product | many2one **product.product** | | |
| `name` | Label | char | | |
| `quantity` | Quantity | float | | |
| `product_uom_id` | Unit | many2one uom.uom | | |
| `price_unit` | Unit Price | float | | |
| `discount` | Discount (%) | float | | default 0 |
| `price_subtotal` | Subtotal | monetary | RO | quantity × price × (1 − discount), before tax |
| `price_total` | Total | monetary | RO | with taxes |
| `tax_ids` | Taxes | many2many account.tax | | |
| `currency_id` | Currency | many2one res.currency | yes | the document's |
| `partner_id` | Partner | many2one res.partner | | the document's commercial partner |
| `date`, `invoice_date`, `move_name`, `parent_state`, `journal_id`, `ref`, `move_type`, `company_id` | Date, Invoice/Bill Date, Number, Status, Journal, Reference, Type, Company | related to the document | RO | stored except `move_type` |
| `collapse_composition`, `collapse_prices` | Hide Composition, Hide Prices | boolean | | on section lines: hide the lines or prices below in reports |
| `parent_id` | Parent Section Line | many2one account.move.line | RO | |
| `is_downpayment`, `sale_line_ids` | Is Downpayment, Sales Order Lines | boolean, many2many | | `sale` |

Accounting side, outside Phase 1 (Chart of Accounts, Taxes, Payments, Analytic bundles): `account_id` Account and its
helpers; `debit`, `credit`, `balance`, `amount_currency`, `amount_residual(_currency)`; `date_maturity` Due Date (on the
payment term line); `tax_line_id`, `group_tax_id`, `tax_group_id`, `tax_base_amount`, `tax_repartition_line_id`,
`tax_tag_ids`, `extra_tax_data`; reconciliation (`reconciled`, `full_reconcile_id`, `matched_debit_ids`,
`matched_credit_ids`, `matching_number`, …); `analytic_distribution`, `analytic_line_ids`; early-payment discount
fields; `payment_id`, `statement_line_id`, `statement_id`; `deferred_*`; follow-up; consolidation; storno.

## Standalone views (Accounting menus, not used by an invoice user)

- List "Journal Items": Invoice Date (hidden), Date, Journal (hidden), Journal Entry, Partner, Reference (hidden),
  Product (hidden), Label, Deferred Date (hidden), Taxes (hidden), Debit, Credit, Tax Grids, Discount Date / Amount,
  Originator Tax, Due Date, Balance (hidden), Matching, Residual (hidden).
- Form: Label, Partner; Information (Amount: Account, Debit, Credit, Balance, Quantity; Dates: Due Date; Taxes;
  Matching; Product); Accounting documents (Journal Entry, Statement Line).
- Search: Journal Item, dates, Amount, Account, Partner, Journal, Ledger, Journal Entry, Taxes; filters Unposted ·
  Posted | To Review | Unreconciled · With residual | Sales · Purchases · Bank · Cash · Credit · Miscellaneous |
  Payable · Receivable · P&L Accounts | Date · Invoice Date; group by Journal Entry, Account, Partner, Journal, Date,
  Invoice Date, Taxes, Tax Grid, Matching.
- Actions: Journal Items (several), Sales / Purchases / Bank and Cash / Miscellaneous (by journal type), Partner Ledger,
  Amounts to Settle, Journal Items to reconcile — all excluding section and note lines.

## Order, defaults, constraints

- `_order`: `date desc, move_name desc, id`.
- `default_get`: discount 0 · deductible_percentage 1 · analytic_precision 2.
- SQL constraints:
  - `check_credit_debit` — "Wrong credit or debit value in accounting entry!" (a line cannot be both debit and credit)
  - `check_amount_currency_balance_sign` — the amount in currency has the balance's sign
  - `check_accountable_required_fields` — "Missing required account on accountable line." (every line but sections and notes)
  - `check_non_accountable_fields_null` — "Forbidden balance or account on non-accountable line" (sections and notes carry no amount or account)

## Records (33) — product, section and note lines

Every line of the 8 documents; tax and payment-term lines summarised after. Taxes on the tenant: **10% G** (id 7) and
**8% S** (id 5), both sale taxes, percent, price-excluded (Malaysian SST: goods 10%, services 8%).

| Document | Seq | Type | Product (variant) | Label | Qty | Unit | Price | Disc % | Taxes | Subtotal | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Draft (SCG-PO-88213) | 0 | product | [FURN-0002] Height-Adjustable Desk 140cm | [FURN-0002] Height-Adjustable Desk 140cm | 40 | Units | 1,650 | 8 | 10% G | 60,720.00 | 66,792.00 |
| Draft (SCG-PO-88213) | 1 | product | [FURN-0001] Ergonomic Office Chair | [FURN-0001] Ergonomic Office Chair | 40 | Units | 899 | 8 | 10% G | 33,083.20 | 36,391.52 |
| Draft (SCG-PO-88213) | 2 | product | [FURN-0003] Steel Filing Cabinet 4-Drawer | [FURN-0003] Steel Filing Cabinet 4-Drawer | 15 | Units | 720 | 0 | 10% G | 10,800.00 | 11,880.00 |
| INV/2026/00001 | 0 | product | [FURN-0001] Ergonomic Office Chair | [FURN-0001] Ergonomic Office Chair | 8 | Units | 899 | 0 | 10% G | 7,192.00 | 7,911.20 |
| INV/2026/00001 | 1 | product | [FURN-0003] Steel Filing Cabinet 4-Drawer | [FURN-0003] Steel Filing Cabinet 4-Drawer | 4 | Units | 720 | 0 | 10% G | 2,880.00 | 3,168.00 |
| INV/2026/00001 | 2 | product | [CONS-0001] A4 Copy Paper (Box of 5 reams) | [CONS-0001] A4 Copy Paper (Box of 5 reams) | 20 | Units | 68 | 0 | 10% G | 1,360.00 | 1,496.00 |
| Draft (STL-2026-0042) | 0 | product | [SRV-0003] Annual Support Retainer | [SRV-0003] Annual Support Retainer | 1 | Units | 18,000 | 0 | 8% S | 18,000.00 | 19,440.00 |
| Draft (STL-2026-0042) | 1 | product | [SW-0002] Nocoly HAP Licence — Pro | [SW-0002] Nocoly HAP Licence — Pro | 25 | Units | 7,200 | 10 | 8% S | 162,000.00 | 174,960.00 |
| INV/2026/00002 | 0 | product | Ergonomic Office Chair (Blue) | Ergonomic Office Chair (Blue) + sales description | 2 | Units | 959 | 0 | 10% G | 1,918.00 | 2,109.80 |
| INV/2026/00002 | 1 | product | [SRV-0001] Implementation Consulting | [SRV-0001] Implementation Consulting + sales description | 1 | Hours | 850 | 0 | 8% S | 850.00 | 918.00 |
| INV/2026/00003 | 13 | product | — (down payment) | Down payment of 30.00% | 1 | — | 575.40 | 0 | 10% G | 575.40 | 632.94 |
| INV/2026/00003 | 14 | product | — (down payment) | Down payment of 30.00% | 1 | — | 255.00 | 0 | 8% S | 255.00 | 275.40 |
| Cancelled (S00021) | 0 | product | Ergonomic Office Chair (Blue) | Ergonomic Office Chair (Blue) + sales description | 2 | Units | 959 | 0 | 10% G | 1,918.00 | 2,109.80 |
| Cancelled (S00021) | 1 | **line_section** | — | Down Payments | — | — | — | — | — | — | — |
| Cancelled (S00021) | 2 | product | — (down payment deduction) | Down Payment (ref: INV/2026/00003 on 09/14/2026) | −1 | — | 575.40 | 0 | 10% G | −575.40 | −632.94 |
| Cancelled (S00021) | 3 | product | — (down payment deduction) | Down Payment (ref: INV/2026/00003 on 09/14/2026) | −1 | — | 255.00 | 0 | 8% S | −255.00 | −275.40 |

The label is the product's display name followed, on a new line, by its sales description (shown truncated above).
The empty draft (8) has no lines.

Tax lines (`display_type tax`, sequence 10000, account SST Control Account): one per tax per document, e.g.
INV/2026/00001 "10% G" 1,143.20. Payment term lines (`payment_term`, sequence 12000, account Account Receivable):
one per document, the total, with the due date. The payment entry PBNK1/2026/00001 has two lines, "Manual Payment:
INV/2026/00002" on Outstanding Receipts (debit 3,027.80) and Account Receivable (credit 3,027.80).

**For worksheets 04 and 07.** The lines point at variants that Phase 1's one-variant-per-product model does not hold:
**[FURN-0001] Ergonomic Office Chair** and **[FURN-0002] Height-Adjustable Desk 140cm** are the archived original
variants, and **Ergonomic Office Chair (Blue)** an attribute variant (see `product.product.md`). Seeding Invoice Lines
will have to map them to the chair's and desk's single variant, or bring those variants in with the Product Variants
bundle.
