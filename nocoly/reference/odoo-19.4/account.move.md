# account.move — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 15 Sep 2026: `fields_get`, `ir.model.fields.modules`, `get_views` (form, list, kanban, search), the
window actions, `default_get`, `_order`, SQL constraints and every record (8). Views are what the tenant's admin user is
served. Behaviour the tenant cannot show comes from the Odoo 19.0 source, `addons/account/models/account_move.py`.
Journal items are in `account.move.line.md`; journals in `account.journal.md`.

Installed apps that add fields here: `sale` (Sales Team, UTM, sale orders), `account_accountant` (deferred entries,
signature), `account_payment` (online transactions), `account_followup` (Last Reminder), `account_invoice_extract` (OCR),
`account_edi_ubl_cii` (UBL/CII file), `account_reports` (tax return), `l10n_my_edi` (MyInvois).

## Menus and actions

One model holds every accounting document; the menus differ by `move_type`:

| Action | Views | Context | Domain |
|---|---|---|---|
| **Invoices** (Invoicing › Customers) | list, kanban, form, pivot, graph, activity | `default_move_type: out_invoice`; menu variant also `search_default_out_invoice`, `search_default_out_receipt` | move_type in (out_invoice, out_refund, out_receipt) |
| **Credit Notes** (Customers) | same | `search_default_out_refund`, `default_move_type: out_refund` | move_type in (out_invoice, out_refund) |
| **Bills** (Invoicing › Vendors) | same | `default_move_type: in_invoice`; menu variant `search_default_in_invoice`, `search_default_in_receipt` | move_type in (in_invoice, in_refund, in_receipt) |
| **Refunds** (Vendors) | same | `search_default_in_refund`, `default_move_type: in_refund` | move_type in (in_invoice, in_refund) |
| Journal Entries / Entries (Accounting) | list, kanban, form, … | `default_move_type: entry`, `search_default_posted` | — |
| Invoices (from a Sales Team) | list, form, kanban | `default_team_id`, `journal_type: sale` | posted out_invoice / out_refund |
| Vendor Bills (from a contact) | list, form, graph | `default_partner_id` | in_invoice / in_refund |

## Order, defaults, constraints

- `_order`: **`date desc, name desc, invoice_date desc, id desc`**.
- `default_get`: state `draft` · move_type `entry` (each action sets `default_move_type`) · auto_post `no` ·
  review_state `no_review`. The Journal defaults to the first suitable journal for the type (Sales for customer
  documents, Purchases for vendor documents); Currency to the journal's or company's (MYR).
- SQL: `account_move_check_document_tax_mode_set` — an invoice, credit note or receipt needs a Document Tax Mode —
  "The document tax mode must be set."
- Numbering (19.0 source, `sequence.mixin`): a draft has no number and shows **Draft**; confirming assigns
  `<journal code>/<year>/<5 digits>` — INV/2026/00001 on Sales; credit notes use R + code when the journal has a
  Dedicated Credit Note Sequence (RINV/…), bills BILL/…; payments P + journal code (PBNK1/2026/00001).

## Fields that matter for Phase 1 (module `account` unless noted)

| Field | Label on the form | Type | Req | Notes |
|---|---|---|---|---|
| `move_type` | Type | selection | yes | `entry` Journal Entry · `out_invoice` Customer Invoice · `out_refund` Customer Credit Note · `in_invoice` Vendor Bill · `in_refund` Vendor Credit Note · `out_receipt` Sales Receipt · `in_receipt` Purchase Receipt. Form: a receipt selector, hidden for entries; read-only once not draft |
| `name` | Number | char | | h1; "Draft" while empty; read-only unless draft |
| `state` | Status | selection | yes, RO | `draft` Draft · `posted` Posted · `cancel` Cancelled; the header status bar |
| `partner_id` | **Customer** (out_*) / **Vendor** (in_*) | many2one res.partner | | placeholder "Search a name or Tax ID..."; picker shows address and Tax ID; read-only unless draft |
| `commercial_partner_id` | Commercial Entity | many2one res.partner | RO | the partner's company |
| `partner_shipping_id` | Delivery Address | many2one res.partner | | customer documents only; "The delivery address will be used in the computation of the fiscal position." |
| `invoice_date` | **Invoice Date** (out_*) / **Bill Date** (in_*) | date | Bill Date required | Invoice Date placeholder "Today" (set on confirm when empty) |
| `date` | Accounting Date | date | yes | bills show it; customer invoices only in quick-edit or once posted with a different date |
| `invoice_date_due` | Due Date | date | | shown while there are no Payment Terms ("Due Date … or Payment Terms") |
| `invoice_payment_term_id` | Payment Terms | many2one account.payment.term | | Payment Terms bundle |
| `journal_id` | Journal | many2one account.journal | yes | shown only when several journals suit the type (`show_journal`); read-only once numbered |
| `currency_id` | Currency | many2one res.currency | yes | invisible on the form (single currency) |
| `document_tax_mode` | (selector) Tax Excl. / Tax Incl. | selection | yes for invoices | `tax_excluded` · `tax_included`; chooses whether line Amount is subtotal or total |
| `ref` | **Bill Reference** (in_*) / **Customer Reference** (out_*, tab Other Info) | char | | |
| `payment_reference` | Payment Reference | char | | bills: main group, placeholder "Use Bill Reference"; invoices: Other Info, placeholder "Standard communication"; "The payment reference to set on journal items." |
| `invoice_line_ids` | Invoice Lines (tab) | one2many account.move.line | | the product, section and note lines — see `account.move.line.md` |
| `line_ids` | Journal Items | one2many account.move.line | | every line, tax and receivable/payable lines included |
| `narration` | Terms and Conditions | html | | under the lines, placeholder "Terms and Conditions" |
| `amount_untaxed` | Untaxed Amount | monetary | RO | stored |
| `amount_tax` | Tax | monetary | RO | stored |
| `amount_total` | Total | monetary | RO | stored |
| `amount_residual` | Amount Due | monetary | RO | stored |
| `amount_untaxed_in_currency_signed`, `amount_tax_signed`, `amount_total_in_currency_signed`, `amount_residual_signed` | Tax Excluded · Tax · Total · Amount Due (list) | monetary | RO | signed: negative for credit notes |
| `tax_totals` | Invoice Totals | json | | the totals widget |
| `payment_state` | Payment Status | selection | RO | `not_paid` Not Paid · `in_payment` In Payment · `paid` Paid · `partial` Partially Paid · `reversed` Reversed · `blocked` Blocked · `invoicing_legacy` Invoicing App Legacy |
| `status_in_payment` | Status (list badge) | selection | RO | payment states plus draft · posted · sent · cancel |
| `invoice_user_id` | Salesperson | many2one res.users | | Other Info › Invoice |
| `team_id` | Sales Team | many2one crm.team | | `sale` |
| `invoice_origin` | Source Document | char | RO | e.g. S00011; hidden on the form, optional list column |
| `partner_bank_id` | Recipient Bank | many2one res.partner.bank | | bank accounts |
| `reversed_entry_id` / `reversal_move_ids` | Reversal of / Reversal Move | many2one / one2many account.move | | set by **Credit Note** (`action_reverse`) |
| `is_move_sent` / `move_sent_values` | Is Move Sent / Sent | boolean / selection | RO | set by Send or Print |
| `delivery_date` | Delivery Date | date | | Other Info |
| `auto_post`, `auto_post_until` | Auto-post, Auto-post until | selection, date | auto_post yes | `no` · `at_date` · `monthly` · `quarterly` · `yearly` |
| `company_id` | Company | many2one res.company | | |

Outside Phase 1 (listed so nothing is mistaken for missing): `fiscal_position_id` Fiscal Position (Fiscal Positions);
`invoice_incoterm_id`, `incoterm_location` (Incoterms); `invoice_cash_rounding_id` (Cash Rounding);
`preferred_payment_method_line_id` Payment Method, `payment_ids`, `matched_payment_ids`, `reconciled_payment_ids`,
`origin_payment_id`, `transaction_ids` (Payments); `qr_code_method`; `invoice_vendor_bill_id` Auto-Complete;
`quick_edit_mode` / `quick_edit_total_amount`; `review_state` To Review; `restrict_mode_hash_table`, `inalterable_hash`,
`secure_sequence_number` (hash lock); `statement_line_id` (bank statements); `tax_cash_basis_*`, `always_tax_exigible`
(cash-basis taxes); `adjusting_entr*`, `deferred_*` (`account_accountant`); `taxable_supply_date`; `last_reminder`
(`account_followup`); `l10n_my_edi_*` MyInvois state, Tax Exemption Reason, Customs Form Reference (`l10n_my_edi`);
`campaign_id`, `medium_id`, `source_id`, `utm_reference` (`sale`, Marketing group); `extract_*` (OCR);
`ubl_cii_xml_*`; `sending_data`, `invoice_pdf_report_*`; duplicate and warning helpers (`duplicated_ref_ids`,
`abnormal_*_warning`, `alerts`, `partner_credit_warning`); mail and activity fields.

## Form

```
header: Confirm (drafts; Post for entries) · Send · Print (posted) · Pay (posted, not paid) · Preview (customer, posted)
        · Credit Note (posted invoice or bill) · Cancel (drafts) · Reset to Draft · Lock (hash) · Send To MyInvois
        · Request Cancel · Reload Data · Digitize document          status bar: Draft → Posted (Cancelled)
alerts: sale warning · duplicates ("This document might be a duplicate of") · outstanding credits/debits · inactive currency
smart buttons: Payments · Journal Items · Reversals · Sale Orders · MyInvois documents · …
ribbons: Paid · In Payment · Partially Paid · Reversed · Blocked · Sent · MyInvois In Progress / Rejected
[Type selector — invoice / receipt, drafts only]
h1: Number (or "Draft")
left:  Customer | Vendor (placeholder "Search a name or Tax ID...")
       Delivery Address (customer documents)
       Bill Reference (vendor documents) · Auto-Complete (bills)
right: Invoice Date (customer, placeholder "Today") | Bill Date (vendor, required)
       Accounting Date (vendor; customer only when it differs once posted)
       Payment Reference (vendor) · Recipient Bank (vendor)
       Due Date "or" Payment Terms
       Journal (only when several suit the type)
       Tax Excl. / Tax Incl.
notebook:
  Invoice Lines — lines list (see account.move.line.md) · Add a line / Add a section / Add a note / Catalog
                · Terms and Conditions · totals (Untaxed Amount, taxes, Total) · payments · Amount Due · outstanding
  Other Info — Invoice (customer): Customer Reference, Salesperson, Sales Team, Recipient Bank, Payment Reference,
                 Payment QR-code, Delivery Date
             — Accounting: Incoterm, Incoterm Location, Fiscal Position, Payment Method, Source Email (bills),
                 Auto-post, Auto-post until
             — Extraction Information (OCR) · Marketing (UTM)
  MyInvois — Malaysian companies, invoices and bills: MyInvois State, Tax Exemption Reason, Customs Form Reference
chatter
```

## List (Invoices / Bills)

**Number** · **Customer** (customer actions) / **Vendor** (vendor actions) · Journal (optional, hidden) · **Invoice Date**
/ **Bill Date** · Accounting Date (hidden) · **Due Date** (relative, hidden once paid or cancelled) · **Last Reminder** ·
Source Document (hidden) · Payment Reference (bills, hidden) · Reference (hidden) · Salesperson (hidden) · Sales Team
(hidden) · Activities (hidden) · **Tax Excluded** · Tax (hidden) · **Total** · **Amount Due** · Currency (hidden) ·
MyInvois state (hidden) · **Status** (badge) · Sent (hidden). Header buttons: Pay, Download.

Kanban card: partner, journal, total, number, date, activities, status.

## Search

- Fields: Invoice (number), Reference, Payment Reference, Total, Journal, Ledger, Partner, Salesperson, Sales Team,
  Period (date), Next Payment Date, Invoice Line, activities.
- Filters: My Invoices | Draft · Posted · Cancelled | Not Sent | Invoices · Receipts · Credit Notes | To Review |
  To pay · In payment · Overdue | Invoice Date · Accounting Date · Due Date.
- Group by: Salesperson, Partner, Status, Sales Team, Payment Method, Journal | Invoice Date, Due Date, Accounting Date.

## Records (8)

| id | Number | Type | Status | Payment | Customer | Invoice Date | Due | Accounting Date | Journal | Reference | Payment Terms | Salesperson | Team | Source | Untaxed | Tax | Total | Due amount | Fiscal Position |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | (Draft) | Customer Invoice | draft | not paid | Sunway Construction Group | — | 2026-10-09 | 2026-09-09 | Sales | SCG-PO-88213 | 30 Days | Casimir | Enterprise | S00011 | 104,603.20 | 10,460.32 | 115,063.52 | 115,063.52 | MY Domestic |
| 2 | INV/2026/00001 | Customer Invoice | posted | not paid | Klinik Kesihatan Damansara | 2026-09-11 | 2026-10-02 | 2026-09-11 | Sales | KKD-2026-009 | 21 Days | Casimir | SMB | S00014 | 11,432.00 | 1,143.20 | 12,575.20 | 12,575.20 | Exempted person under Schedule A |
| 3 | (Draft) | Customer Invoice | draft | not paid | Sarawak Timber Logistics | — | 2026-10-29 | 2026-09-14 | Sales | STL-2026-0042 | 45 Days | Casimir | Enterprise | S00016 | 180,000.00 | 14,400.00 | 194,400.00 | 194,400.00 | MY Domestic |
| 4 | INV/2026/00002 | Customer Invoice | posted | **paid** | Casimir | 2026-09-14 | 2026-09-14 | 2026-09-14 | Sales | TEST demo run - delete me | — | Casimir | Sales | S00020 | 2,768.00 | 259.80 | 3,027.80 | 0.00 | — |
| 5 | PBNK1/2026/00001 | Journal Entry (payment of INV/2026/00002) | posted | — | Casimir | — | 2026-09-14 | 2026-09-14 | Bank | INV/2026/00002 | — | — | — | — | — | — | 3,027.80 | 0.00 | — |
| 6 | INV/2026/00003 | Customer Invoice (30% down payment) | posted | not paid | Casimir | 2026-09-14 | 2026-09-14 | 2026-09-14 | Sales | S00021 | — | Casimir | Sales | S00021 | 830.40 | 77.94 | 908.34 | 908.34 | — |
| 7 | (Draft) | Customer Invoice | **cancel** | not paid | Casimir | — | 2026-09-14 | 2026-09-14 | Sales | S00021 | — | Casimir | Sales | S00021 | 1,087.60 | 113.86 | 1,201.46 | 1,201.46 | — |
| 8 | (Draft) | Customer Invoice | draft | not paid | — | — | 2026-09-14 | 2026-09-14 | Sales | — | — | — | Sales | — | 0 | 0 | 0 | 0 | — |

All MYR, Tax Excl., auto-post no, not sent, no MyInvois state. Payment reference = the number on posted invoices.
Records 4–8 are demo/test traffic on the tenant (4 says "TEST demo run - delete me"; 8 is an empty draft); there are
no vendor bills or credit notes. Sales orders S00011–S00021 are the Sales app's (not in Phase 1).
