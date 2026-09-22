# 16 · Orders — requirements

| | |
|---|---|
| Odoo model | `sale.order` (+ `sale.order.line`) |
| Odoo menus | Sales › Orders › **Quotations** (action 497) and **Orders** (action 496) — two filtered views of one table |
| Reference | `nocoly/reference/odoo-19.4/sale.order.md` |
| Status | **Requirements, plus §6 — the three interaction rules are built.** The owner is building the rest of this worksheet by hand; `build/orders.py` owns the rules and nothing else |
| Date | 21 Sep 2026, read from casimir before the trial expires; rules built 21 Sep 2026 |

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
| 6 | Expiration | `validity_date` | Date | **no** | **Quotation/Order Date + 30 days** | from a company setting — see below. Odoo's help: "Validity of the quotation. After this date, you will no longer be able to sign and pay it." **Required must be off**: the hide rule above would otherwise make a confirmed order unsaveable — §6. As built by hand it is *required*, with the function default `DATEADD(DATENOW(),"+1M",1)` — one month, not the thirty days casimir's setting gives |
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
| 21 | Delivery status | `delivery_status` | **Single Select, editable** | — | empty | **Owner's decision, 21 Sep 2026: a flag a person sets, not a computed figure** — Odoo computes it from stock pickings, which do not exist here. See *How Odoo computes it* below |
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

### Delivery status — why it is a flag here

Odoo's `delivery_status` is **not a `sale` field at all**. It lives in **`sale_stock`**
(`addons/sale_stock/models/sale_order.py`), is `store=True` and computed from
`picking_ids.state`:

| Odoo's test | Value |
|---|---|
| no pickings, or every picking cancelled | **`False` — empty** |
| every picking done or cancelled | `full` **Fully Delivered** |
| any picking done **and** some line carries a delivered quantity | `partial` **Partially Delivered** |
| any picking done, but no line carries a delivered quantity | `started` **Started** |
| pickings exist, none done | `pending` **Not Delivered** |

Every branch reads a stock picking. **There are no pickings in ERP Master and there will not be until
Inventory is built** (Phase 5), so nothing here could compute this field honestly. The owner's call is
therefore to carry it as an **editable Single Select a person sets by hand** — the same shape as *Locked*,
where Odoo's mechanism was replaced by a control someone drives.

**Two things to know about the option set as built:**

- It carries **Nothing to Deliver**, which Odoo does not have as an option — Odoo uses the **empty** value for
  "no pickings". Naming the null is the same modelling choice Invoice Lines made when it gave Display Type an
  explicit *Product* option, so it is consistent with the house pattern and worth keeping.
- It **omits `started` — Started**. In Odoo that is a real state, and a distinct one: a picking has been
  completed but no line yet shows a delivered quantity. Add it if the four are meant to mirror Odoo; leave it
  out deliberately if a hand-set flag does not need the distinction. **Not decided.**

Because the value is now typed rather than derived, **it can disagree with reality** — nothing keeps it in
step, and nothing will until Inventory lands and the field can go back to being computed. The rule that hides
it unless Status is *Sales Order* (see below) carries more weight for that reason: it keeps a meaningless
flag off an unconfirmed quotation.

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
| 6 | Quantity | `product_uom_qty` | Number, 2 dp | default **1** (Odoo's), as 07 does |
| 7 | Delivered | `qty_delivered` | Number, read-only | needs Inventory; see §4 |
| 8 | Invoiced | `qty_invoiced` | Number, read-only | computable once an order → invoice link exists |
| 9 | Unit | `product_uom_id` | Relation → Units & Packagings | |
| 10 | Unit Price | `price_unit` | Currency | |
| 11 | Taxes | `tax_ids` | Relation → Taxes, multiple | the Taxes bundle is built; automation B's pattern fills it from the product |
| 12 | Discount (%) | `discount` | Number | default **0** (Odoo's), as 07 does |
| 13 | Lead Time | `customer_lead` | Number, integer | "Number of days between the order confirmation and the shipping of the products" |
| 14 | Optional Line | `is_optional` | Checkbox | |
| 15 | Subtotal | `price_subtotal` | **Formula**, read-only | `Quantity × Unit Price × (1 − Discount ÷ 100)` — 07's formula exactly |
| 16 | Total | `price_total` | Formula, read-only | subtotal plus its taxes, as 07's Total is |

**A blank operand counts as 0** in Subtotal, Tax Amount and Total (`advancedSetting.nullzero "1"`, `orderlines.py
defaults`, 22 Sep 2026). With 07's `"0"` a type 31 Formula computes **nothing** when any operand is blank: probed
through the API on S00017's line, Discount written blank stored Subtotal, Tax Amount and Total empty (both read
paths), and the order's totals with them. With `"1"` the same write stored 68.00 / 6.80 / 74.80, and Quantity 2 with
Discount blank stored 136.00 / 13.60 / 149.60. The static defaults only fill a new line in the form; `nullzero`
covers a cleared Discount and an API write. A blank Quantity or Unit Price now stores Subtotal 0.00 rather than
nothing, which is Odoo's figure. **Invoice Lines still carries `"0"`** and has the same defect.

### Interaction rules — grouped by action

Everything the two tables above imply about *behaviour* is gathered here, so the tables stay a description
of the fields and this stays the description of the form.

**Hide**

| When | Hide | Odoo source | Built |
|---|---|---|---|
| Status is **Sales Order** | **Expiration** | `invisible="state == 'sale'"` | **yes** — *Expiration is for an unconfirmed quotation*, §6 |
| **Online payment** is unticked | **Prepayment %** | `invisible="not require_payment"` | no — neither control exists |
| A line's Display Type is **Section, Subsection or Note** | that line's **Product · Quantity · Unit · Unit Price · Discount (%) · Taxes · Subtotal** | `sale_order_line_non_accountable_null_fields` — the same constraint 07 already implements as a rule | no — the child table cannot be reached, §6 |

**Make read-only**

| When | Make read-only | Odoo source | Built |
|---|---|---|---|
| Status is **Sales Order or Cancelled** | **Customer · Expiration · Quotation/Order Date · Pricelist · Tax mode · Online signature · Online payment · Prepayment %** | `readonly="state in ['cancel','sale']"` | **partly** — *A confirmed or cancelled order is closed for editing*, §6, with the first three; the other five controls do not exist |
| **Locked** is ticked, **or** Status is Cancelled | **Invoice Address · Delivery Address · Delivery Date** | `readonly="state == 'cancel' or locked"` | **yes**, the OR and all three — *A locked or cancelled order is closed for editing*, §6 |
| Status is **not Quotation** | **Tax mode** | `readonly="state != 'draft'"` — stricter than the first row, and the one to use for this field | no — the control does not exist |

**Require** — nothing conditional. Customer is required in practice and Tax mode is required for every type;
both belong on the field, not on a rule.

**The asymmetry to keep.** **Payment Terms is never read-only on an order**, where 06 locks it on a posted
invoice. That is Odoo's own difference, not a slip — do not "fix" it into line with Invoices.

## 3 · Validation, buttons and views

### Validation

| Rule | Odoo source |
|---|---|
| A confirmed order must have a Quotation/Order Date | `sale_order_date_order_conditional_required` — `CHECK((state = 'sale' AND date_order IS NOT NULL) OR state != 'sale')`. Confirm sets it, so this is a guard rather than something a person trips |

### Buttons — all twenty, and where each one lives

**An earlier draft of this section listed four.** It was built from a "header buttons" extract that was
itself truncated, and it was never re-read against the arch. The twenty exist in **four different places**,
which is why one table missed most of them:

| Where | Which |
|---|---|
| **`<header>`** | Send · Confirm · Download · Preview · Cancel · Set to Quotation · Lock · Unlock · Create Invoice · Reopen Invoicing · Capture / Void Transaction |
| **`<control>` inside the lines list** | Add Line · Add Section · Add Note · Catalog |
| **below the lines** | Discount |
| **cog "Actions" — `ir.actions.server` bound to `sale.order`** | Mark as Sent (501) · Confirm Orders (502, batch) · Share (503) · Deliver (504) · Send an email (505, batch) · Close Invoicing (506) · Save as template (531) · Create Project (541) |
| **the portal, not the back end** | Sign & Accept |

Nothing named *Add Subsection* is in the arch — the lines list offers **three** controls, Add Line, Add
Section and Add Note. `line_subsection` is a `display_type` value the UI reaches another way.

#### What each does, and what it becomes here

The rule for the last column: **prefer a Nocoly native feature over a built workflow.**

| # | Button | Odoo behaviour | Here |
|---|---|---|---|
| 1 | **Send** | mail composer; sending marks the order Quotation Sent | **workflow** — send-email node, then set Status. Not yet working |
| 2 | **Download** | `sale.action_report_saleorder`, the quotation PDF | **System Print** with a print template — native, no workflow |
| 3 | **Confirm** | guards, then Status → Sales Order and **Quotation/Order Date → now** | **button + workflow** (the guard is a branch) |
| 4 | **Preview** | `act_url` to `get_portal_url()` — the customer-facing page | **Public Sharing** — native, effectively already there |
| 5 | **Cancel** | refuses a locked order; Status → Cancelled | **button**, disabled while Locked is ticked |
| 6 | **Create Invoice** | action 495 → a wizard that writes `account.move` | **workflow** — **blocked**, no order → invoice link (§4) |
| 7 | **Set to Quotation** | from Cancelled **or Quotation Sent** → Quotation; clears the signature fields | **button** — one field to write |
| 8 | **Sign & Accept** | on the **portal**: the customer signs, writing `signature` · `signed_by` · `signed_on`, and confirms | **Public Sharing + a shared form.** A share link is read-only by default, so accepting a signature needs a form that writes back. **Three controls missing** |
| 9 | **Discount** | wizard applying a percentage across every line | **button + workflow** over the subtable |
| 10 | **Mark as Sent** | refuses unless Quotation; Status → Quotation Sent | **button** |
| 11 | **Deliver** | `deliver_sold_quantity` — sets each line's **Delivered = Quantity** (`qty_delivered` is writable) | **button + workflow** over the subtable |
| 12 | **Reopen Invoicing** | clears `invoicing_closed` | **button** + the missing control below |
| 13 | **Save as template** | creates a `sale.order.template` from this order | **already solved** — Recreate plus Is Template, §1.1 of 17 |
| 14 | **Create Project** | creates a project | **not built** — Services phase |
| 15 | **Add Section** | a line with `display_type = line_section` | **built** — the subtable's Add a row plus Display Type |
| 16 | **Add Note** | `display_type = line_note` | **built**, same |
| 17 | **Duplicate** | Odoo's generic copy | **Recreate** — and it must be Recreate, not Copy: Copy leaves the order lines behind, proved 21 Sep |
| 18 | **Add Subsection** | not a control in the arch | Display Type already carries **Subsection** |
| 19 | **Catalog** | a product-picker grid | **not built** — needs a catalogue UI |
| 20 | **Close Invoicing** | sets `invoicing_closed` | **button** + the missing control below |

#### What these buttons need that does not exist yet

| Control | Odoo | Needed by |
|---|---|---|
| **Invoicing Closed** | `invoicing_closed`, *Manually Closed For Invoicing*, boolean, stored | 12 and 20 — neither works without it |
| **Signature · Signed By · Signed On** | `signature` binary · `signed_by` char · `signed_on` datetime, all stored | 8, and 7 clears them |

#### Also in Odoo, and not on the list of twenty

**Lock / Unlock** — owner's decision, 21 Sep 2026: **not built.** Locked is an ordinary editable checkbox;
the read-only rule it drives is unchanged and Cancel still hides while it is ticked, so the behaviour
survives and only the buttons go. **Update Prices** needs Pricelists. **Capture / Void Transaction** needs
payment providers. **Share** (503) is Public Sharing again. **Confirm Orders** (502) and **Send an email**
(505) are the batch forms of 3 and 1, and HAP custom actions already run over a selection.

#### Two corrections to the earlier draft

- Confirm does **not** "fill Quotation/Order Date if empty". `_prepare_confirmation_values` returns
  `{'state': 'sale', 'date_order': now}` — it **overwrites unconditionally**. That is the mechanism behind
  the field carrying two labels: on a confirmed order the value is the confirmation date.
- Confirm does **not** assign the Number. In this app Number is an **auto-number control**, which the reseed
  proved — the twelve seeded orders took S00006–S00017 the moment they were written.

#### The guards, which are validations rather than decoration

- **Confirm** — *"Some order lines are missing a product, you need to correct them before going further."*
  when any line that is not a section, subsection or note, and not a down payment, has no Product. Order
  Lines carries Display Type, so the condition is expressible; down payments are not modelled.
- **Cancel** — *"You cannot cancel a locked order. Please unlock it first."*
- **Mark as Sent** — *"Only draft orders can be marked as sent directly."*

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
| **Delivery** — `qty_delivered` and `commitment_date` honouring stock, and `delivery_status` as a **computed** figure | Inventory is not in scope at all. Delivery status is built as an editable flag instead (§2); the computation waits for Phase 5 |
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

## 6 · Build — the three interaction rules, 21 Sep 2026

`build/orders.py` owns the **rules of this worksheet and nothing else**. It has no `fields`, `layout`, `views`,
`buttons`, `seed` or `records` step and must not gain one: HAP has no per-field endpoint, so a layout step is a
full `SaveWorksheetControls` that replaces the whole control set, and it would revert whatever the owner had
typed in the browser since the read. `products.py` carries the same trap and the same warning.

| Step | What it does | State |
|---|---|---|
| `rules` | the three interaction rules, upserted by name | **run** — all three built and read back |
| `retire` | disables the five hand-built rules those three supersede | **written, not run** — the sandbox refused the write |
| `expiry` | clears `required` on Expiration in one version-pinned save | **written, not run** — the sandbox refused the write |
| `check` | reads the rules and Expiration back and reports drift | run |
| `show` | the live controls, the live rules and the Order Lines child table | — |

### The three rules, as HAP stored them

| Rule | ruleId | Condition | Action and targets |
|---|---|---|---|
| **Expiration is for an unconfirmed quotation** | `6ab0ba6d805aef703286d6fb` | Status `filterType` 2 = [Sales Order] | **hide** (item type 2) Expiration |
| **A confirmed or cancelled order is closed for editing** | `6ab0ba6e805aef703286d6fd` | Status `filterType` 2 = [Sales Order, Cancelled] | **read-only** (item type 4) Customer · Expiration · Quotation/Order Date |
| **A locked or cancelled order is closed for editing** | `6ab0ba6ee54d2a34fa4e7fe2` | one group, both conditions `spliceType` **2**: Locked `filterType` 2 `value` "1" `values` ["1"] **or** Status `filterType` 2 = [Cancelled] | **read-only** (item type 4) Invoice Address · Delivery Address · Delivery Date |

All three are `type` 0 (interaction), `checkType` 0, `hintType` 0, enabled, and each is written
**`<action> · equals`** rather than `<opposite> · not equals`. A rule applies its action while its condition
holds and the opposite when it fails, so on a **new order** — Status empty, Locked unticked — no condition
holds and every field is visible and editable, which is what Odoo's `invisible` and `readonly` do.

Rule 2 carries **three** of Odoo's eight targets. Pricelist, Tax mode, Online signature, Online payment and
Prepayment % are not on the worksheet; add them to `CONFIRMED_FIELDS` in `orders.py` the day they are, and
nothing else about the rule changes.

### Found while building

**1 · HAP expresses an OR across two different controls, and the app now has three examples.** A rule's
`filters` is a list of groups; `spliceType` **1** is AND and **2** is OR, and HAP's own rule editor stamps the
group's operator onto *every* condition in it — which is why a lone condition reads 1. Rule 3 is one group
holding a Locked condition and a Status condition, both `spliceType` 2, and the server stored it exactly as
sent. The shape was not guessed: the owner's hand-built *Read-only when status is Cancelled or Locked* already
carried it. `common.any_of` OR-s whole *groups* the same way, so either shape is available; `orders.either`
uses the editor's.

**2 · Expiration is required, and rule 1 hides it — the form will refuse to save a confirmed order.** A field a
rule hides can never be filled, so a hidden field must not be required on the control itself; Journals'
Communication Type and Communication Standard had their Required taken off for exactly this reason on 16 Sep
and required by a second rule instead (05 §3). Invoices' Auto-post is the one field in this app that is both
required and hidden by a rule, and only because it carries the default **No**, so it is always filled by the
time the rule hides it. Expiration's default is a *function* — `DATEADD(DATENOW(),"+1M",1)` — and **the API
applies no defaults at all**, so an order created through the API carries no Expiration and can then never be
saved from the form once it is confirmed. **Odoo does not require `validity_date`.** The owner approved clearing
the flag on 21 Sep 2026 and `orders.py expiry` is written to do it — a version-pinned full control save that
flips the one boolean and asserts every other control is byte-identical — but it has not been run. Until it is,
rule 1 is a trap.

Two smaller Expiration notes while it is open: the default is **one month**, where casimir's *Default Quotation
Validity* is **30 days** (§2), and a month is not thirty days; and Odoo's help text on the control reads
"Validity of this quotation…" where Odoo's own is "Validity of the quotation…".

**3 · The rule the brief called inert is not inert.** `6ab0aa0fe43d174ab3753143` *Hide Delivery Status when
Quotation is not Sales Order* was read as targeting nothing and testing nothing because its `controlIds` is
empty and its filter's `controlId` is an empty string. **Both are normal.** Every rule in this app stores
`controlIds: []` — the ten rules on Invoices, proved in the UI, included — because the targets live in
`ruleItems[].controls`, not there; and the filter entry with the empty `controlId` is the **group wrapper**
(`isGroup: true`), whose real condition sits in its `groupFilters`. That condition is Status `filterType` **6**
(not equals) = [Sales Order], and the rule hides Delivery Status. It is a working rule, it matches Odoo — a
delivery status means nothing on an unconfirmed quotation — and **no rule built here touches Delivery Status**,
so it was left enabled. It is the owner's to keep or drop.

**4 · The owner hand-built the same three rules while this was being specified.** Six rules were created in the
browser between 11:52 and 12:23 on 21 Sep 2026. Five of them are the three above, written by hand, and
`orders.py retire` disables them — **disables, not deletes**: `disabled` is a flag on the rule, `save-rule
--enabled` puts any of them straight back, and the CLI cannot delete a rule at all. Each is re-sent in full with
only that flag flipped.

| ruleId | Name | What it does | Superseded by |
|---|---|---|---|
| `6ab0ad7ce43d174ab37532c2` | Read-only when status is Sales Order or Cancelled | Status is Sales Order or Cancelled → read-only Customer, Expiration, Quotation/Order Date | rule 2 — same condition, same three targets |
| `6ab0aff8e54d2a34fa4e7dbb` | Hide when status is Sales Order | Status is Sales Order → hide Expiration | rule 1 — the same rule, `filterType` 51 |
| `6ab0b117e54d2a34fa4e7f0e` | Read-only when Locked | Locked → read-only Invoice Address, Delivery Address, Delivery Date | rule 3 — which adds Odoo's `state == 'cancel'` |
| `6ab0b0f3e43d174ab37533d2` | Read-only when status is Cancelled or Locked | Cancelled or Locked → read-only Delivery Date | rule 3 — a subset of it |
| `6ab0afcebd43f55762c78212` | Read-only when status is Sales Order | Sales Order **or Locked** → read-only Invoice Address, Delivery Address | rule 3 — **and it is wrong** |

That last one is not merely superseded. Odoo's `readonly` on `partner_invoice_id` and `partner_shipping_id` is
`state == 'cancel' or locked` and says nothing about `sale`, so the rule froze both addresses on every plain
confirmed order — and because a rule reverses its action when its condition fails, it **contradicted** the
owner's own *Read-only when Locked* on exactly those records: one made the addresses read-only while the other
made them editable. Which wins is undefined. Until `retire` runs, that contradiction is live.

**5 · A single select's "is" is stored two ways on this worksheet, and only one of them is proved.** A business
rule's *is any of* is `filterType` **2** — what every rule this repo has built and tested in the UI carries,
including Invoices' eight — while a view's or a button's condition on the same control is 51. HAP's own rule
editor wrote **51** for a single-option *equals* on three of the owner's rules and **2** on another, so both
shapes are on Orders. The three built here use 2. Whether 51 behaves identically in a rule is unproved and is
worth one glance in the UI pass, since the owner will reach for the editor again.

The same ambiguity exists for the checkbox. HAP's editor wrote Locked's "is ticked" as `filterType` 2 with
`value` "1" and `values` `[]`; `taxes.py`'s picker work found `values` `["1"]`; Products' live *Sales tab only
for products that can be sold* carries both keys. Rule 3 sends both, which is a superset of every shape seen —
but which one the browser reads is for the UI pass.

### The three rules that were not built, and why

| Rule | Why not |
|---|---|
| **Prepayment %** hidden when **Online payment** is unticked | Neither control exists on the worksheet |
| **Tax mode** read-only when Status is not Quotation | The control does not exist |
| A line's **Section, Subsection or Note** hides its figures | The Order Lines child table cannot be reached — below |

**Why the line-level rule cannot be built.** Its targets live on the Order Lines subtable's child worksheet
`6ab0a592e43d174ab3752fe7`, and `hap worksheet fields` on it answers **Insufficient permissions**. That is
structural, not a permission this profile is missing:

- the child worksheet's id was minted **by the subtable control itself** — `…fe5` the control, `…fe6` the
  back-relation, `…fe7` the worksheet, all in one second — which is HAP's `child_fields` kind of 子表, a
  **hidden child table**. It has no entry in the app's sections, and HAP resolves a worksheet's permissions
  through the app's worksheet list;
- the main site's own `GetWorksheetControls` — the call the form designer uses, reached through the CLI's
  session — refuses it the same way, while the identical call reads **Invoice Lines**, a *mounted* worksheet,
  without complaint. So it is not a V3-open-API quirk;
- no role is being debugged (`app role list` answers normally), which is the other thing that turns the CLI's
  answers into *Insufficient permissions*;
- `hap worksheet rules` on it answers `[]` rather than refusing, so an empty rule list there is not evidence of
  anything.

The only readable view of the child is the parent control's `relationControls` snapshot, and it shows the table
currently holds **two** columns — Description and Product Variants. So even with access the rule would have
nothing to act on: none of Display Type, Product, Quantity, Unit, Unit Price, Discount (%), Taxes or Subtotal
exists yet. **This is the bigger finding: Order Lines is not shaped like Invoice Lines.** 07's lines are a real
worksheet with its own sidebar entry, views, rules and records, mounted with `mount-subtable`; Orders' are a
hidden child table that no CLI call can read or write. If the line-level rule, the Subtotal and Total formulas
and the order roll-ups are to be built the way 06 and 07 were, Order Lines has to be a worksheet of its own —
which is a decision for the owner, and a rebuild of the subtable, not a rule.

---

## 7 · What is left — read off the app, 21 Sep 2026 (evening)

The owner rebuilt both worksheets by hand after §6. **Order Lines went from two controls to sixteen and is now
a real mounted worksheet** (`6ab0c740e43d174ab37535b2`), not the hidden child table §6 could not read — so the
structural blocker recorded there is **cleared**. Orders grew from twelve controls to thirty-five.

What stands: Order Lines has Orders · Sequence · Display Type (**all four options including Product**, as 07
does) · Product → Product Variants · Description · Quantity · Quantity Invoiced · Quantity Delivered · Unit →
Units · Unit Price · Discount · Taxes → Taxes · Product Unit (Lookup off Product) · Tax Amount · Subtotal ·
Total. Orders gained the Order Lines subtable mounted at `6ab0c740e43d174ab37535b0`, Tax Mode, Salesperson,
Tags, Sales Teams, an Other Info section with the Sales / Confirmation / Tracking / Invoicing / Shipping
dividers, Customer Reference, Source Document, Online Signature, Online Payment, Prepayment Percentage,
Template, Journal, Incoterm Location, Invoicing Status and three roll-up controls.

> **Both worksheets hold zero records.** Nothing built on top of them can lose data, which settles by
> itself every question below that turned on what a change would discard.

### 7.1 Orders

| # | What | Detail |
|---|---|---|
| 1 | **The three roll-ups aggregate nothing** | Untaxed Amount `…35b8`, Tax `…35b9`, Total `…35ba` are 汇总 (type 37) but carry `dataSource=''`, `sourceControlId=''` and `enumDefault=6` — which is **count**, not sum. Wire them over the subtable `$6ab0c740e43d174ab37535b0$` onto the child's **Subtotal** `6ab0ca80805aef703286d82a`, **Tax Amount** `6ab0cad0805aef703286d83d` and **Total** `6ab0cad0805aef703286d83e` with `enumDefault=5`, and **filter to Display Type = Product** — a section keeps whatever figures were typed into it before its Display Type was changed. The working shape to copy is Invoice Lines' *Tax rate*; note that a 汇总's own `advancedSetting.filters` writes a single select's "is" as `filterType` **51**, where a business rule writes **2** |
| 2 | **The subtable shows one column** | `6ab0c740e43d174ab37535b0` carries `showControls` — and `advancedSetting.controlssorts` — of `["6ab0c740e43d174ab37535b6", "<Sequence>"]`, and **`…35b6` is a dead id**: no such control is on Order Lines any more. So the grid on the Orders form offers *Sequence* and nothing else — no Product, no Quantity, no price. Mounting minted the list from the controls that existed that minute and never grew with the worksheet. Invoices' *Lines* `6aaa2baae43d174ab3749de9` is the reference: it names all twelve of its child's columns |
| 3 | **Widen the closed-for-editing rule** | `A confirmed or cancelled order is closed for editing` (`6ab0ba6e805aef703286d6fd`) names three controls. **Online Signature, Online Payment and Prepayment Percentage** now exist and belong in it. **Tax Mode does not** — item 4 puts it under a stricter condition, and two rules disagreeing about one control is a fight with no defined winner |
| 4 | **Tax Mode read-only when Status is not Quotation** | Was blocked in §6; buildable now. `readonly="state != 'draft'"` — stricter than the rule above and the one to use for this field |
| 5 | Pricelist · Fiscal Position · Incoterm | Still absent, all correctly deferred to their bundles. **Incoterm Location is present without Incoterm** — half a pair |
| 6 | Invoicing Status | The control and its four options exist, but nothing can compute it until the order → invoice link does. See §4. Correctly left hidden and read-only (`001`) until then |

### 7.2 Order Lines

| # | What | Detail |
|---|---|---|
| 1 | **Nothing computes Tax Amount** | Subtotal and Total already compute — see the correction below — but Tax Amount is a number a person types, and because Total is `Subtotal + Tax Amount`, **an empty Tax Amount leaves Total empty too**. The fix is 07's: a hidden, read-only **Tax rate** 汇总 over the Taxes relation summing the Amounts of the taxes whose Tax Computation is Percentage, and Tax Amount computed as `Subtotal × Tax rate ÷ 100` |
| 2 | **Lead Time missing** | `customer_lead`, integer: "Number of days between the order confirmation and the shipping of the products" |
| 3 | **Optional Line missing** | `is_optional`, checkbox |
| 4 | **The Orders relation is not required** | Invoice Lines makes Invoice required, which is what 07's test 8 showed stops an orphan line being created from the standalone worksheet |
| 5 | Description is not required | Odoo's `sale.order.line.name` is `required=True`. Safe to require here: the owner gave Description a default that copies the Product's, so it fills itself |
| 6 | **No rules at all** | The line-level rule — *a section or a note carries no figures* — is unbuilt. Blocked in §6, buildable now |
| 7 | **No aliases anywhere** | Every control on both worksheets carries `alias=''`. BUILDING.md's convention is that an alias is the Odoo field name, and every other worksheet in the app follows it; the browser's own field editor does not set one, so a hand-built worksheet has none |
| 8 | No `invoice_lines` link | So Quantity Invoiced has no source and stays manual until the order → invoice bundle |

### 7.3 Three things this section got wrong, and what they actually are

Written after reading the app a second time and testing the form. Recorded rather than quietly edited,
because each was a claim about a mechanism, not a typo.

**Subtotal is not broken. Total was, and §7.3 could not see why.** §7 first reported both as Currency
controls where 07 uses Formula, and asked the owner to accept losing typed values to convert them. Both carry
a **function default** — `advancedSetting.defaulttype = "1"` with a `defaultfunc` of
`{"type":"mdfunction","expression":…,"status":1}` — and **Subtotal's works**: typing quantity 3, unit price 100
and discount 10 produced RM 270.00 on the spot, because every operand is a plain number on the same row. It is
also better than 07 in one respect, since a Formula control cannot carry a currency and this one shows RM.
**Keep Subtotal exactly as it is.**

Total was a different case, and the first pass got it wrong by generalising from Subtotal. Its expression
reads `Subtotal + Tax Amount`, and **Tax Amount had to read the Tax rate 汇总** — which is computed
server-side and therefore has no value while the form is open. A function default is evaluated in the browser
as you type, so the expression yielded nothing, Tax Amount saved blank, and Total with it. A saved line proved
it: Subtotal 270.00, Tax Amount empty, Total empty, and the order reading Untaxed 270 / Tax 0 / Total 0.

**The rule that came out of it:** a control that reads a roll-up must be a **Formula (type 31)**; a function
default can only read plain values on its own row. Invoice Lines is the proof either way — its Total is a
Formula reading the same kind of roll-up, and its stored rows are right (1798.00 → 1977.80 at 10%, 850.00 →
918.00 at 8%). Tax Amount and Total were converted to Formulas on 21 Sep 2026; Subtotal was not.

**The Prepayment Percentage rule is not a divergence.** §7 read the rule *Only require Prepayment Percentage
if Online Payment is needed* as making the field **required** where Odoo **hides** it. Its rule item is type
**1**, and 1 is **SHOW**, not require — the constants are `SHOW, HIDE, READONLY, REQUIRE, ERROR = 1, 2, 4, 5,
6`. The control is hidden at the field (`fieldPermission` `011`) and the rule reveals it when Online Payment
is ticked, which is `invisible="not require_payment"` exactly. Confirmed in the form: the field is absent
from Other Info until Online Payment is ticked, and appears the moment it is. Only the **name** is wrong.
Renaming it would strand the rule — `upsert_rules` matches by name and would build a second one — so it
keeps its name and this paragraph explains it.

**Tax Mode's stray "Option 3" is already gone.** It is still in the options array but carries
`isDeleted: true`, and the form offers only Tax Excluded and Tax Included.

*What this leaves.* Of the twelve items §7 first raised, three were not defects. One new one — the subtable's
dead column list, 7.1 item 2 — is the most visible of the lot, because it is what makes the Orders form
unusable for entering a line.

### 7.4 The order to do it in

The roll-ups read the child's figures, so they follow Tax Amount; the subtable's column list names controls
that do not exist yet, so it follows Order Lines' new fields. So: **Order Lines' three new controls** (Tax
rate, Lead Time, Optional Line) → **Tax Amount's function** → the two `required` flags → **Orders' three
roll-ups and the subtable's columns** in one save → **the rules**, Order Lines' section rule and Orders'
7.1 items 3 and 4 as one pass → **the aliases** last, as a pass of their own over both worksheets.

## 8 · Discount — built 22 Sep 2026 (`orders.py` §14)

Odoo's discount wizard (`sale.order.discount`) writes the discount **as order lines** on a Discount product. The
owner chose the same. Odoo's third mode, *On All Order Lines*, is not built: it is the subtable's Batch Operation on
each line's Discount %.

**Piece 1 · the Discount product** (`discountproduct`): *Discount*, Service, Sales Price 0, Cost 0, no Sales or
Purchase Taxes, category Services, unit Units; created as a **record** in Products (no control saved). Its variant
came from Product Variants' own *create a new product's variant* automation. Ids in `ids.json` › records
(`Products: Discount` 4464529e…, `Product Variants: Discount` dd0780ce…). Not carried: `invoice_policy 'order'`
(Products has no Invoicing Policy control); Odoo's default purchase tax (unknowable with the tenant gone).
`discountline` proved a line on it is an ordinary product line: on S00006, Qty 1 × −100 at 10% G stored Subtotal
−100.00, Tax Amount −10.00, Total −110.00, and Untaxed / Tax / Total went 247,225.00 / 24,518.50 / 271,743.50 →
247,125.00 / 24,508.50 / 271,633.50, then back once the test line was deleted.

**Piece 2 · Apply Discount**: two controls, **Discount Type** (Global Discount · Fixed Amount, `discount_type`)
and **Discount Value** (2 decimals, `discount_value`), stand in for the wizard. **They are parked at row 9999 for
the owner to place** (intent: side by side above the totals). The button is offered unless Locked is ticked or
Status is Cancelled (Odoo's `invisible="locked or state == 'cancel'"`). It removes the order's lines on the
Discount product, stops if Value is empty or 0, then writes **one line per tax combination** — grouped, not the
one-per-product-line fallback. Line names follow `_prepare_global_discount_so_lines`: one combination →
**"Discount 10.00%"** / **"Discount"**; several → `"Discount 10.00%- On products with the following taxes 10% G"`.
The percentage prints with two decimals because Odoo formats it with `float_repr(…, Discount precision = 2)`.

Divergences from Odoo (also in `orders.py` §14c and the button's description): named *Apply Discount*, not
*Discount*; **replaces** instead of stacking; no cent adjustment on a Fixed split; no >100% refusal; the wizard is
two fields on the order.

**Fixed Amount matches Odoo since 22 Sep 2026.** Odoo 19's `_reduce_base_lines_to_target_amount` takes
`percentage = amount ÷ Σ(total_excluded + tax_amount)` — the product lines' **tax-included** total — and gives
each tax group's discount line an untaxed amount of the group's Subtotal × percentage, so **the order's Total drops
by exactly the amount**. The workflow's denominator step, now *Their total, tax included*, sums the product lines'
**Total** (it summed Subtotal before, which took about RM 1,099 off the Total for RM 1,000 promised). The only
remaining difference is **Odoo's cent correction**: it nudges the lines so the Total reconciles to the cent, and
this does not — `selfdiscount` reports the residual exactly.

**Proved** (`selfdiscount`, both read paths, 22 Sep 2026) on S00006 — lines 128,250 + 89,775 + 19,000 at 10% G
and 10,200 at 8% S, untaxed 247,225.00:

| Press | Discount lines | Untaxed / Tax / Total |
|---|---|---|
| Global 10% | 10% G −23,702.50 (tax −2,370.25) · 8% S −1,020.00 (tax −81.60) | 222,502.50 / 22,066.65 / 244,569.15 — untaxed −24,722.50 exactly |
| Global 10% again | the same two, new ids — still one set | the same |
| Fixed 1,000 (22 Sep, Odoo's way) | 10% G −872.24 (tax −87.22, total −959.46) · 8% S −37.54 (tax −3.00, total −40.54) | 246,315.22 / 24,428.28 / **270,743.50 — Total −1,000.00, residual 0.00** |
| Value 0 | none | 247,225.00 / 24,518.50 / 271,743.50 |

S00006 ended with no Discount line and Discount Type / Value empty. The one-combination name was proved on S00007
(one line "Discount 10.00%", −10,460.32 on 104,603.20), then removed and the fields cleared. **Not UI-tested**:
nothing here opened a browser.
