# 16 · Orders — requirements

| | |
|---|---|
| Odoo model | `sale.order` (+ `sale.order.line`) |
| Odoo menus | Sales › Orders › **Quotations** (action 497) and **Orders** (action 496) — two filtered views of one table |
| Reference | `nocoly/reference/odoo-19.4/sale.order.md` |
| Status | **§1 only — requirements.** The owner is building this worksheet by hand; nothing here has been built by a builder |
| Date | 21 Sep 2026, read from casimir before the trial expires |

---

## 1 · Shape

`sale.order` is **the same shape as `account.move`**, which ERP Master already models well: one table, two
menu entries that are filtered views of it, a status bar driven by buttons, a subtable of lines with
sections and notes, and a totals block. Most of the modelling decisions taken for 06 Invoices and 07 Invoice
Lines transfer directly, and should be, so the two read the same way.

**Status bar** `draft` **Quotation** → `sent` **Quotation Sent** → `sale` **Sales Order**, with `cancel`
**Cancelled** off the bar. A separate boolean **`locked`** freezes a confirmed order and gates Lock/Unlock.

## 2 · Fields

### Header

| # | Field | Odoo | Type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Number | `name` | Text · title · read-only | — | `New` | written on confirmation from the sequence, as Invoices' Number is |
| 2 | Status | `state` | Single Select, read-only | — | Quotation | **Quotation · Quotation Sent · Sales Order · Cancelled**; moved only by buttons |
| 3 | Customer | `partner_id` | Relation → Contacts | **yes** in practice | — | read-only once `state in ['cancel','sale']` |
| 4 | Invoice Address | `partner_invoice_id` | Relation → Contacts | — | the customer | read-only `state == 'cancel' or locked` |
| 5 | Delivery Address | `partner_shipping_id` | Relation → Contacts | — | the customer | read-only `state == 'cancel' or locked` |
| 6 | Expiration | `validity_date` | Date | — | computed from company settings | **hidden once `state == 'sale'`**; read-only for cancel/sale |
| 7 | Quotation Date / Order Date | `date_order` | **Date & time** | — | **now** | two instances in Odoo's form: labelled *Quotation Date* while draft/sent, *Order Date* once confirmed. Read-only for cancel/sale |
| 8 | Payment Terms | `payment_term_id` | Relation → Payment Terms | — | the customer's | **never read-only** — unlike the invoice, which locks it once posted |
| 9 | Delivery Date | `commitment_date` | Date & time | — | — | read-only `state == 'cancel' or locked` |
| 10 | Tax mode | `document_tax_mode` | Single Select | **yes** for non-entry | Tax Excluded | **the same field ERP Master already models on Invoices**; read-only `state != 'draft'` |
| 11 | Pricelist | `pricelist_id` | Relation → Pricelists | — | the customer's | **blocked** — Pricelists is not built |
| 12 | Salesperson | `user_id` | Relation → users | — | the current user | Other Info › Sales |
| 13 | Sales Team | `team_id` | Relation → Sales Teams | — | — | Teh Li Wei built Sales Teams |
| 14 | Customer Reference | `client_order_ref` | Text | — | — | Other Info › Sales |
| 15 | Tags | `tag_ids` | Relation → CRM Tags, multiple | — | — | Teh Li Wei built CRM Tags |
| 16 | Source Document | `origin` | Text | — | — | Other Info › Tracking |
| 17 | Online signature | `require_signature` | Checkbox | — | company setting | Other Info › Confirmation |
| 18 | Online payment | `require_payment` | Checkbox | — | company setting | Other Info › Confirmation |
| 19 | Prepayment % | `prepayment_percent` | Number | — | company setting | shown only when `require_payment` |
| 20 | Invoicing status | `invoice_status` | Single Select, read-only | — | computed | **Upselling Opportunity · Fully Invoiced · To Invoice · Nothing to Invoice** |
| 21 | Delivery status | `delivery_status` | Single Select, read-only | — | computed | **Not Delivered · Started · Partially Delivered · Fully Delivered** — needs Inventory; see §4 |
| 22 | Untaxed Amount · Tax · Total | `amount_untaxed`, `amount_tax`, `amount_total` | roll-ups over the lines | — | — | exactly the pattern 06 uses: Σ Subtotal, and Σ Total − Σ Subtotal for the tax |
| 23 | Locked | `locked` | Checkbox, hidden | — | unticked | set by Lock / Unlock |

### Lines — `sale.order.line`

The three-way split is **the same as Invoice Lines**: `display_type` is **`line_section` Section ·
`line_subsection` Subsection · `line_note` Note**, and a product line carries `display_type` **NULL**.

> ERP Master's Invoice Lines gave Display Type an explicit fourth option, *Product*, because a HAP Single
> Select has no null. Do the same here so the two worksheets read alike — and record it in §3 as the same
> difference 07 already records.

| # | Field | Odoo | Type | Notes |
|---|---|---|---|---|
| 1 | Order | `order_id` | Relation → Orders | the parent; the subtable fills it |
| 2 | Sequence | `sequence` | Number | Odoo uses a drag handle; HAP needs the column |
| 3 | Display Type | `display_type` | Single Select | Section · Subsection · Note (+ Product, ours) |
| 4 | Product | `product_id` | Relation → Product Variants | |
| 5 | Description | `name` | Text | Odoo fills it from the product; we do not — the same gap 07 records |
| 6 | Quantity | `product_uom_qty` | Number, 2 dp | |
| 7 | Delivered | `qty_delivered` | Number, read-only | needs Inventory; see §4 |
| 8 | Invoiced | `qty_invoiced` | Number, read-only | computable once an order → invoice link exists |
| 9 | Unit | `product_uom_id` | Relation → Units & Packagings | |
| 10 | Unit Price | `price_unit` | Currency | |
| 11 | Taxes | `tax_ids` | Relation → Taxes, multiple | the Taxes bundle is built; automation B's pattern fills it from the product |
| 12 | Discount (%) | `discount` | Number | |
| 13 | Lead Time | `customer_lead` | Number, integer | "Number of days between the order confirmation and the shipping of the products" |
| 14 | Optional Line | `is_optional` | Checkbox | |
| 15 | Subtotal | `price_subtotal` | **Formula**, read-only | `Quantity × Unit Price × (1 − Discount ÷ 100)` — 07's formula exactly |
| 16 | Total | `price_total` | Formula, read-only | subtotal plus its taxes, as 07's Total is |

## 3 · Rules, buttons, views

### Rules to build

| Rule | When | Effect | Odoo source |
|---|---|---|---|
| A section or a note carries no figures | Display Type is Section, Subsection or Note | hide Product, Quantity, Unit, Unit Price, Discount, Taxes, Subtotal | `sale_order_line_non_accountable_null_fields` — the same constraint 07 already implements |
| Expiration is for an unconfirmed quotation | Status is Sales Order | hide **Expiration** | `invisible="state == 'sale'"` |
| Prepayment follows Online payment | Online payment unticked | hide **Prepayment %** | `invisible="not require_payment"` |
| A confirmed or cancelled order is closed for editing | Status is Sales Order or Cancelled | make Customer · Expiration · Quotation Date · Pricelist · Tax mode · Online signature · Online payment · Prepayment % read-only | the `readonly` conditions in the reference |
| A locked order is closed for editing | Locked is ticked | make Invoice Address · Delivery Address · Delivery Date read-only | `readonly="state == 'cancel' or locked"` |

**Validation.** `sale_order_date_order_conditional_required` — a confirmed order must have a
`date_order`. Since Confirm will set it, this is a guard rather than a form rule.

Note the deliberate asymmetry to carry over: **Payment Terms is never read-only on an order**, where 06
locks it on a posted invoice. That is Odoo's own difference, not a slip.

### Buttons

| Button | Shown when | Does |
|---|---|---|
| **Send** | Quotation, or Quotation Sent / Sales Order | Status → Quotation Sent |
| **Confirm** | Quotation or Quotation Sent | Status → **Sales Order**; assigns the **Number**; fills Order Date if empty |
| **Cancel** | Quotation, Quotation Sent or Sales Order, and not locked | Status → Cancelled |
| **Set to Quotation** | Cancelled | Status → Quotation |
| **Lock** | Sales Order and not locked | Locked → ticked |
| **Unlock** | Locked | Locked → unticked |
| **Create Invoice** | `invoice_status` is *To Invoice* | **defer** — see §4 |
| Preview · Download | — | PDF; **defer** |
| Capture / Void Transaction | there is an authorised transaction | **defer** — payment providers |

The first six are the buildable set, and they are the same shape as 06's Confirm / Cancel / Reset to Draft.

### Views

| View | Filter | Columns |
|---|---|---|
| **Quotations** | Status is Quotation or Quotation Sent | Number · Customer · Quotation Date · Salesperson · Total · Invoicing status |
| **Orders** | Status is Sales Order | the same, plus Order Date |
| **Cancelled** (ours) | Status is Cancelled | — Odoo reaches these through a filter, not a menu |

Odoo's own visible list columns are `name · date_order · partner_id · user_id · activity_ids ·
amount_total · invoice_status · expected_date`, with a dozen more available and hidden.

## 4 · Not built now

| What | Why |
|---|---|
| **Create Invoice** and the order → invoice link (`invoice_lines`, `invoice_count`, `invoice_status` as a live figure) | This is the one piece worth arguing about. Invoices and Invoice Lines are built, so the link is reachable — but it needs a button that creates a document and its lines from another document's lines, which nothing in Phase 1 does. Treat it as its own bundle |
| **Delivery** — `qty_delivered`, `delivery_status`, `commitment_date` honouring stock | Inventory is not in scope at all |
| **Pricelists** (`pricelist_id`) and the price-recompute it drives | A worksheet of its own, not built |
| **Quotation Templates** (`sale_order_template_id`) | Not built; zero records on the tenant |
| **Quote Builder** tab (`quotation_document_ids`, `customizable_pdf_form_fields`) | See worksheet 17 — it configures a PDF assembler HAP does not have |
| Down payments (`is_downpayment`), optional lines' ordering, combos (`combo_item_id`, `linked_line_id`), product custom attributes | Each is its own machinery; the fields are on the line but nothing in Phase 1 drives them |
| Online signature and payment (`require_signature`, `require_payment`, `prepayment_percent` as behaviour) | The checkboxes can be stored; the customer portal cannot |
| Preview · Download · Send as behaviour | No PDF, no mail |
| `fiscal_position_id`, `incoterm`, `project_id`, `preferred_payment_method_line_id` | Each needs a table that is not built |
| Smart buttons (Invoices, Projects, Tasks, Transactions) | Counts over tables that do not exist yet |

## 5 · Dependencies, and the one that will bite

| Needs | State |
|---|---|
| Contacts | built — **but see below** |
| Products / Product Variants | built |
| Units & Packagings | built |
| Taxes | built (bundle 6) |
| Payment Terms | built (bundle 3) |
| Sales Teams · CRM Tags | built by Teh Li Wei |
| Invoices / Invoice Lines | built — the link is not |
| Pricelists · Quotation Templates · Fiscal Positions · Inventory · Projects · Payment providers | **not built** |

**The seed problem.** The tenant holds **12 orders and 29 lines**, and five of their customers are not in
ERP Master's Contacts: **Petronas Digital Sdn Bhd · Universiti Teknologi Malaysia · TechBridge
Distributors · Bumi Retail Ventures · Nasi Kandar Pelita Holdings**. Seeding Orders faithfully means
seeding those five contacts first — and Contacts is a built worksheet, so that is a change to someone
else's table. Decide it before seeding: either add the five, or seed only the seven orders whose customers
already exist and say which were left out.

Four of the tenant's orders — **S00011, S00014, S00016, S00021** — are already the Source Documents on ERP
Master's seeded invoices, so those four are the natural first seeds.

**The trial.** casimir's banner read *free trial expires in 1 day* on 21 Sep 2026. Everything above was read
off the tenant on that day; `reference/odoo-19.4/sale.order.md` and this file are what survives it.
