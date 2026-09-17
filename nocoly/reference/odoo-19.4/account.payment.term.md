# account.payment.term — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 17 Sep 2026: `fields_get` and `ir.model.fields` (module per field) of `account.payment.term` and
`account.payment.term.line`, `ir.model.constraint`, `ir.default`, `get_views` (form, list, search) and the raw
`ir.ui.view` arch of every view of both models, the window action and its menu, `decimal.precision`, every payment
term and every term line, every `ir.model.fields` row whose relation is either model, every view whose arch names a
payment term field, and the payment terms of every `account.move`, `res.partner` and `sale.order`. The data is saved
as `nocoly/data/casimir-payment-terms.json`. Behaviour the tenant cannot show is read from the Odoo 19.0 source in
this repo: `addons/account/models/account_payment_term.py`, `account_move.py`, `partner.py`, and
`odoo/addons/base/models/res_partner.py`. Nothing here differs between 19.0 and 19.4 that matters to the build.

Menu: **Invoicing ▸ Configuration ▸ Invoicing ▸ Payment Terms** (window action `account.action_payment_term_form`,
`list,kanban,form`, no domain, no context, sequence 10).

## Fields — `account.payment.term`

Every field is module `account`. S = stored.

| Field | Label | Type | Req. | Default | Notes |
|---|---|---|---|---|---|
| `name` | Payment Terms | char S | **yes** | — | translatable; placeholder "e.g. 30 days" |
| `active` | Active | boolean S | | true | help: "If the active field is set to False, it will allow you to hide the payment terms without removing it." |
| `note` | Description on the Invoice | html S | | — | translatable; placeholder "Description on invoice (e.g. Payment terms: 30 days after invoice date)"; printed on the invoice |
| `line_ids` | Terms | one2many → account.payment.term.line S | | **one line: Percent 100, 0 days** (`_default_line_ids`) | copied on duplicate |
| `company_id` | Company | many2one res.company S | | — | multi-company only; placeholder "Visible to all" |
| `sequence` | Sequence | integer S | **yes** | 10 | the list's drag handle; `_order = "sequence, id"` |
| `display_on_invoice` | Show installment dates | boolean S | | true | the invoice report prints the installments when set |
| `early_discount` | Early Discount | boolean S | | false | |
| `discount_percentage` | Discount % | float S | | 2.0 | help: "Early Payment Discount granted for this payment term" |
| `discount_days` | Discount Days | integer S | | 10 | help: "Number of days before the early payment proposition expires" |
| `early_pay_discount_computation` | Cash Discount Tax Reduction | selection S (computed, editable) | | from the company's country: BE → `mixed`, NL → `excluded`, else **`included`** | `included` On early payment · `excluded` Never · `mixed` Always (upon invoice). The form labels it "Reduced tax:" |
| `fiscal_country_codes`, `currency_id` | — | computed | | | invisible helpers |
| `example_amount` (1000), `example_date` (today), `example_invalid`, `example_preview`, `example_preview_discount` | — | not stored | | | the *Preview* group |

## Fields — `account.payment.term.line` (`_order = "id"`)

| Field | Label | Type | Req. | Default | Notes |
|---|---|---|---|---|---|
| `payment_id` | Payment Terms | many2one → account.payment.term S | **yes** | — | `ondelete='cascade'` |
| `value_amount` | Due | float S, digits **Payment Terms = 6** | | computed: a Percent line gets **100 − the other percent lines**; a Fixed line 0 | help: "For percent enter a ratio between 0-100." |
| `value` | Value | selection S | **yes** | `percent` | `percent` Percent · `fixed` Fixed. help: "Select here the kind of valuation related to this payment terms line." |
| `nb_days` | Days (list: **After**) | integer S | | computed: a new line after the first gets **the previous line's days + 30** | |
| `delay_type` | Delay Type | selection S | **yes** | `days_after` | `days_after` Days after invoice date · `days_after_end_of_month` Days after end of month · `days_after_end_of_next_month` Days after end of next month · `days_end_of_month_on_the` Days end of month on the |
| `days_next_month` | Days on the next month | char(2) S | | "10" | shown only for *Days end of month on the* (`display_days_next_month`) |

## Constraints (Python — `ir.model.constraint` holds only foreign keys)

| Model | Check | Message |
|---|---|---|
| term | sum of the **Percent** lines' Due, rounded to 6 digits, ≠ 100 (so no lines, or only Fixed lines, fail too) | "The Payment Term must have at least one percent line and the sum of the percent must be 100%." |
| term | Early Discount and more than one line | "The Early Payment Discount functionality can only be used with payment terms using a single 100% line. " |
| term | Early Discount and Discount % ≤ 0 | "The Early Payment Discount must be strictly positive." |
| term | Early Discount and Discount Days ≤ 0 | "The Early Payment Discount days must be strictly positive." |
| line | Value Percent and Due < 0 or > 100 | "Percentages on the Payment Terms lines must be between 0 and 100." |
| line | Days on the next month not a number | "The days added must be a number and has to be between 0 and 31." |
| line | Days on the next month a number outside 0–31 | "The days added must be between 0 and 31." |
| term, on delete | an `account.move` uses the term | "Uh-oh! Those payment terms are quite popular and can't be deleted since there are still some records referencing them. How about archiving them instead?" |

Duplicating a term names the copy "%s (copy)".

## Form (`account.view_payment_term_form`)

```
[ribbon "Archived" when not active]
label "Payment Terms"   h1: name  (placeholder "e.g. 30 days")
group:  company_id (multi-company)
        Early Discount [x]  <Discount %> "% if paid within" <Discount Days> "days"      ← the last three only when early_discount
                            "Reduced tax:" <early_pay_discount_computation>          ← only when early_discount
group "Due Terms"                         | group "Preview"
  line_ids, editable list, no label:      |   [x] Show installment dates
    Due · Value · After · Delay Type ·    |   Example: <example_amount> on <example_date>
    Days on the next month (only for      |   note  (placeholder "Description on invoice (e.g. …)")
    "Days end of month on the")           |   example_preview_discount (early discount and display_on_invoice)
                                          |   example_preview  "#1 Installment of RM 1,000.00 due on …" (display_on_invoice)
```

## List, kanban, search

- **List** (`view_payment_term_tree`): `sequence` (handle) · `name` · `company_id` (multi-company).
- **Kanban**: name (bold) and note.
- **Search**: Payment Terms (name) · Active · filter **Archived** (`active = False`).

## Access (`addons/account/security/ir.model.access.csv`)

| Model | Group | Read | Write | Create | Delete |
|---|---|---|---|---|---|
| term, line | `base.group_user` (every internal user) | ✓ | | | |
| term | `base.group_portal` | ✓ | | | |
| term, line | `account.group_account_manager` | ✓ | ✓ | ✓ | ✓ |

## The records — 10 terms, 11 lines, 17 Sep 2026

All active, sequence **10**, no company, Show installment dates ✓, Discount % **2**, Cash Discount Tax Reduction
**On early payment**, created 2026-09-07 by the chart template. The list's order is therefore the id order below.

| id | Payment Terms | Lines (Due · Value · After · Delay Type · Days on the next month) | Early Discount | Description on the Invoice |
|---|---|---|---|---|
| 1 | Immediate Payment | 100 Percent · 0 · Days after invoice date | — (days 10) | Payment terms: Immediate Payment |
| 2 | 15 Days | 100 Percent · 15 · Days after invoice date | — (10) | Payment terms: 15 Days |
| 3 | 21 Days | 100 Percent · 21 · Days after invoice date | — (10) | Payment terms: 21 Days |
| 4 | 30 Days | 100 Percent · 30 · Days after invoice date | — (10) | Payment terms: 30 Days |
| 5 | 45 Days | 100 Percent · 45 · Days after invoice date | — (10) | Payment terms: 45 Days |
| 6 | End of Following Month | 100 Percent · 0 · Days after end of next month | — (10) | Payment terms: End of Following Month |
| 7 | 10 Days after End of Next Month | 100 Percent · 10 · Days after end of next month | — (10) | Payment terms: 10 Days after End of Next Month |
| 8 | 30% Now, Balance 60 Days | 30 Percent · 0 · Days after invoice date; 70 Percent · 60 · Days after invoice date | — (10) | Payment terms: 30% Now, Balance 60 Days |
| 9 | 2/7 Net 30 | 100 Percent · 30 · Days after invoice date | **✓ 2 % within 7 days** | Payment terms: 30 Days, 2% Early Payment Discount under 7 days |
| 10 | 90 days, on the 10th | 100 Percent · 90 · Days end of month on the · **10** | — (10) | Payment terms: 90 days, on the 10th |

Every line carries Days on the next month "10", shown only on term 10. Each description is stored as `<p>…</p>`.

## How a term dates an invoice (19.0 source)

`account.move._compute_invoice_date_due` takes the **latest** `date_maturity` of `needed_terms`; `needed_terms` is
built from the term's lines by `_compute_terms` **only when the invoice has lines** (`invoice_line_ids`), with
`date_ref = invoice_date or date or today`. Without a term, or without lines, the due date stays as entered, or today.
Each line's date (`account.payment.term.line._get_due_date`):

| Delay Type | Due date |
|---|---|
| Days after invoice date | ref + After days |
| Days after end of month | last day of ref's month + After days |
| Days after end of next month | last day of the month after ref's + After days |
| Days end of month on the | Days on the next month ≤ 0: last day of the month of (ref + After days). Otherwise (ref + After days), one month on, on that day — clamped to the month's last day (`relativedelta(months=1, day=n)`); a value that is not a number counts as 1 |

The tenant bears it out: INV/2026/00001 dated 2026-09-11 on *21 Days* → 2026-10-02; the Sunway draft (no invoice
date, accounting date 2026-09-09) on *30 Days* → 2026-10-09; the Sarawak draft (2026-09-14) on *45 Days* → 2026-10-29.
Posting fills an empty invoice date with today, and the due date recomputes from it.

The amounts per installment (the last line always takes the balance; Fixed lines are amounts; percentages of the
total) become the **payment-term journal items** on the receivable/payable account — double entry, not built.

## Where other models point here

| Model | Field | Label | Notes |
|---|---|---|---|
| `account.move` | `invoice_payment_term_id` | Payment Terms | stored, computed from the partner, editable (below) |
| `account.bank.statement.line` | `invoice_payment_term_id` | Payment Terms | related, not stored |
| `res.partner` | `property_payment_term_id` | **Customer Payment Terms** | company-dependent; `ondelete='restrict'`; a **commercial field** |
| `res.partner` | `property_supplier_payment_term_id` | **Vendor Payment Terms** | company-dependent; a **commercial field** |
| `res.users` | the same two | | related through the user's partner |
| `sale.order` | `payment_term_id` | Payment Terms | Sales — not this app |

### `account.move` — the invoice form

```xml
<div class="o_td_label" invisible="move_type not in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')">
    <label for="invoice_date_due" string="Due Date" invisible="invoice_payment_term_id"/>
    <label for="invoice_payment_term_id" string="Payment terms" invisible="not invoice_payment_term_id"/>
</div>
<div class="d-flex" invisible="move_type not in (…the same six…)" name="due_date">
    <field name="invoice_date_due" force_save="1" placeholder="Date" invisible="invoice_payment_term_id" …/>
    <span … invisible="state != 'draft' or invoice_payment_term_id">or</span>
    <field name="invoice_payment_term_id" placeholder="Payment Terms" options="{'no_quick_create':True}" readonly="state in ['cancel', 'posted']"/>
</div>
```

So: **Due Date or Payment Terms**, never both; neither on a journal entry; the term read-only once posted or
cancelled. `_compute_invoice_payment_term_id` (depends on `partner_id`): a sale document (invoice, credit note,
receipt) takes the partner's **Customer Payment Terms**, a purchase document its **Vendor Payment Terms** — *or keeps
the one it has* when the partner has none; any other move gets none. No view other than the form names the field.

| Invoice | Partner | Term | Due |
|---|---|---|---|
| INV/2026/00001 (posted, 2026-09-11) | Klinik Kesihatan Damansara | 21 Days | 2026-10-02 |
| draft SCG-PO-88213 (2026-09-09) | Sunway Construction Group | 30 Days | 2026-10-09 |
| draft STL-2026-0042 (2026-09-14) | Sarawak Timber Logistics | 45 Days | 2026-10-29 |
| INV/2026/00002, INV/2026/00003, two others | Casimir / none | — | the invoice date |

### `res.partner` — tab *Sales & Purchase*

The base view has three groups on the tab — **Sales** (`user_id` Salesperson), **Purchase** (empty) and **Misc**
(Company ID for companies, **Reference**, Industry). `account.view_partner_property_form` adds:

```xml
<group name="sale" position="inside">
    <field string="Payment Terms" name="property_payment_term_id" options="{'no_open': True, 'no_create': True}" groups="account.group_account_invoice,account.group_account_readonly"/>
    <field string="Payment Method" name="property_inbound_payment_method_line_id" … />
</group>
<group name="purchase" position="inside">
    <field string="Payment Terms" name="property_supplier_payment_term_id" options="{'no_open': True, 'no_create': True}" groups="account.group_account_invoice,account.group_account_readonly"/>
    <field string="Payment Method" name="property_outbound_payment_method_line_id" … />
</group>
```

`sale.res_partner_view_form_property_inherit` re-sets both fields' groups to
`account.group_account_invoice,sales_team.group_sale_salesman`. Either way every accounting group sees them: Billing and Read-only are named, and
Accountant and Adviser imply Billing. Neither field is hidden for a contact under a company.

**Commercial fields.** Both are in `res.partner._commercial_fields()`. A contact given a company takes the company's
*set* values (`_commercial_sync_from_company`, `_get_commercial_values`); a company whose value changes writes it —
**empty included** — to its non-company contacts (`_commercial_sync_to_descendants`). A contact's own edit is not
pushed up (only `vat` is a synced commercial field).

| Partner | Customer Payment Terms |
|---|---|
| Bumi Retail Ventures | 2/7 Net 30 |
| Klinik Kesihatan Damansara | 21 Days |
| Nasi Kandar Pelita Holdings | 15 Days |
| Petronas Digital Sdn Bhd | 45 Days |
| Sarawak Timber Logistics | 45 Days |
| Sunway Construction Group | 30 Days |
| TechBridge Distributors | 30 Days |
| Universiti Teknologi Malaysia | 30 Days |

No partner has **Vendor Payment Terms**. No `ir.default` exists for either field or for the invoice's.
