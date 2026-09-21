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
**Cancelled** off the bar. A separate boolean **`locked`** freezes a confirmed order; in Odoo it is driven
by Lock / Unlock buttons, but **here it is an ordinary editable checkbox and those two buttons are not
built** (owner's decision, 21 Sep 2026).

## 2 · Fields

### Header

| # | Field | Odoo | Type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Number | `name` | Text · title · read-only | — | `New` | written on confirmation from the sequence, as Invoices' Number is |
| 2 | Status | `state` | Single Select, read-only | — | Quotation | **Quotation · Quotation Sent · Sales Order · Cancelled**; moved only by buttons |
| 3 | Customer | `partner_id` | Relation → Contacts | **yes** | — | |
| 4 | Invoice Address | `partner_invoice_id` | Relation → Contacts | — | the customer | |
| 5 | Delivery Address | `partner_shipping_id` | Relation → Contacts | — | the customer | |
| 6 | Expiration | `validity_date` | Date | — | **Quotation/Order Date + 30 days** | from a company setting — see below. Odoo's help: "Validity of the quotation. After this date, you will no longer be able to sign and pay it." |
| 7 | **Quotation/Order Date** | `date_order` | **Date & time** | — | **now** | Odoo puts the one field on the form twice under two labels — *Quotation Date* while draft or sent, *Order Date* once confirmed. HAP cannot rename a field from a rule, so it carries **both words**, exactly as Invoices' *Customer / Vendor* does |
| 8 | Payment Terms | `payment_term_id` | Relation → Payment Terms | — | the customer's | |
| 9 | Delivery Date | `commitment_date` | Date & time | — | — | |
| 10 | Tax mode | `document_tax_mode` | Single Select | **yes** | Tax Excluded | **the same field ERP Master already models on Invoices** |
| 11 | Pricelist | `pricelist_id` | Relation → Pricelists | — | the customer's | **blocked** — Pricelists is not built |
| 12 | Salesperson | `user_id` | Relation → users | — | the current user | Other Info › Sales |
| 13 | Sales Team | `team_id` | Relation → Sales Teams | — | — | Teh Li Wei built Sales Teams |
| 14 | Customer Reference | `client_order_ref` | Text | — | — | Other Info › Sales |
| 15 | Tags | `tag_ids` | Relation → CRM Tags, multiple | — | — | Teh Li Wei built CRM Tags |
| 16 | Source Document | `origin` | Text | — | — | Other Info › Tracking |
| 17 | Online signature | `require_signature` | Checkbox | — | **ticked** | from a company setting — see below. "Request a online signature from the customer to confirm the order." |
| 18 | Online payment | `require_payment` | Checkbox | — | **unticked** | from a company setting — see below |
| 19 | Prepayment % | `prepayment_percent` | Number | — | **100 %** | from a company setting — see below |
| 20 | Invoicing status | `invoice_status` | Single Select, read-only | — | computed | **Upselling Opportunity · Fully Invoiced · To Invoice · Nothing to Invoice** |
| 21 | Delivery status | `delivery_status` | Single Select, read-only | — | computed | **Not Delivered · Started · Partially Delivered · Fully Delivered** — needs Inventory; see §4 |
| 22 | Untaxed Amount · Tax · Total | `amount_untaxed`, `amount_tax`, `amount_total` | roll-ups over the lines | — | — | the pattern 06 uses: Σ Subtotal, and Σ Total − Σ Subtotal for the tax |
| 23 | **Locked** | `locked` | **Checkbox, editable** | — | unticked | **Owner's decision, 21 Sep 2026: a plain editable checkbox, and Odoo's Lock / Unlock buttons are not built.** Odoo's help: "Locked orders cannot be modified." It still drives a read-only rule — see below |

### Defaults that come from company settings

Four of the defaults above are not constants. Odoo computes each from `res.company`, and these are the
values **casimir holds today**:

| Field on the order | `res.company` field | Label in Sales › Configuration › Settings | casimir | What an order gets |
|---|---|---|---|---|
| Expiration `validity_date` | `quotation_validity_days` | **Default Quotation Validity** | **30** | Quotation/Order Date **+ 30 days** |
| Online signature `require_signature` | `portal_confirmation_sign` | **Online Signature** | **true** | **ticked** |
| Online payment `require_payment` | `portal_confirmation_pay` | **Online Payment** | **false** | **unticked** |
| Prepayment % `prepayment_percent` | `prepayment_percent` | **Prepayment percentage** | **1** | **100 %** — Odoo stores a **fraction**, not a percentage |

Proved on the tenant, not inferred: **S00021** is dated 2026-09-14 and expires **2026-10-14**; **S00022** is
dated 2026-09-21 and expires **2026-10-21**. Both are exactly thirty days.

**A decision to take.** HAP has no company-settings table, so either hard-code the four values as control
defaults and record that they came from a setting, or build a one-row Settings worksheet. Hard-coding is
cheaper and is what every other ERP Master worksheet has done with a company default; the cost is that
changing the validity from 30 days becomes a build change rather than a setting.

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

### Interaction rules — grouped by action

Everything the two tables above imply about *behaviour* is gathered here, so the tables stay a description
of the fields and this stays the description of the form.

**Hide**

| When | Hide | Odoo source |
|---|---|---|
| Status is **Sales Order** | **Expiration** | `invisible="state == 'sale'"` |
| **Online payment** is unticked | **Prepayment %** | `invisible="not require_payment"` |
| A line's Display Type is **Section, Subsection or Note** | that line's **Product · Quantity · Unit · Unit Price · Discount (%) · Taxes · Subtotal** | `sale_order_line_non_accountable_null_fields` — the same constraint 07 already implements as a rule |

**Make read-only**

| When | Make read-only | Odoo source |
|---|---|---|
| Status is **Sales Order or Cancelled** | **Customer · Expiration · Quotation/Order Date · Pricelist · Tax mode · Online signature · Online payment · Prepayment %** | `readonly="state in ['cancel','sale']"` |
| **Locked** is ticked, **or** Status is Cancelled | **Invoice Address · Delivery Address · Delivery Date** | `readonly="state == 'cancel' or locked"` |
| Status is **not Quotation** | **Tax mode** | `readonly="state != 'draft'"` — stricter than the first row, and the one to use for this field |

**Require** — nothing conditional. Customer is required in practice and Tax mode is required for every type;
both belong on the field, not on a rule.

**The asymmetry to keep.** **Payment Terms is never read-only on an order**, where 06 locks it on a posted
invoice. That is Odoo's own difference, not a slip — do not "fix" it into line with Invoices.

## 3 · Validation, buttons and views

### Validation

| Rule | Odoo source |
|---|---|
| A confirmed order must have a Quotation/Order Date | `sale_order_date_order_conditional_required` — `CHECK((state = 'sale' AND date_order IS NOT NULL) OR state != 'sale')`. Confirm sets it, so this is a guard rather than something a person trips |

### Buttons

| Button | Shown when | Does |
|---|---|---|
| **Send** | Quotation, or Quotation Sent / Sales Order | Status → Quotation Sent |
| **Confirm** | Quotation or Quotation Sent | Status → **Sales Order**; assigns the **Number**; fills Quotation/Order Date if empty |
| **Cancel** | Quotation, Quotation Sent or Sales Order, **and Locked is unticked** | Status → Cancelled |
| **Set to Quotation** | Cancelled | Status → Quotation |

Four buttons, the same shape as 06's Confirm / Cancel / Reset to Draft.

**Not built — owner's decision, 21 Sep 2026: Lock and Unlock.** Odoo gates a confirmed order behind those
two buttons; here **Locked is an ordinary editable checkbox** a person ticks. The read-only rule it drives
is unchanged, and Cancel still hides while it is ticked — so the behaviour survives, only the buttons go.

**Deferred, and why** — *Create Invoice* (§4), *Preview* and *Download* (no PDF), *Capture* and *Void
Transaction* (no payment providers).

### Views

| View | Filter | Columns |
|---|---|---|
| **Quotations** | Status is Quotation or Quotation Sent | Number · Customer · Quotation/Order Date · Salesperson · Total · Invoicing status |
| **Orders** | Status is Sales Order | the same |
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
| Online signature and payment (`require_signature`, `require_payment`, `prepayment_percent` as behaviour) | The checkboxes can be stored with their company-setting defaults; the customer portal cannot |
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
