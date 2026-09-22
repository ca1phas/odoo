# 16 · Orders — requirements

| | |
|---|---|
| Odoo model | `sale.order` (+ `sale.order.line`) |
| Odoo menus | Sales › Orders › **Quotations** (action 497) and **Orders** (action 496) — two filtered views of one table |
| Reference | `nocoly/reference/odoo-19.4/sale.order.md` |
| Status | **Requirements, plus §6 — the three interaction rules are built.** The owner is building the rest of this worksheet by hand; `build/orders.py` owns the rules and nothing else. Since then §8–§11 (22 Sep 2026) and **§12 Incoterm** (22 Sep 2026) |
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
| Terms and conditions `note` | `invoice_terms` / `invoice_terms_html`, behind `account.use_invoice_terms` | **Default Terms & Conditions** (Invoicing settings) | **unknown** — never extracted | **empty** — no company settings here; see §9 |

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
| 1 | **Send** | mail composer; sending marks the order Quotation Sent | **button + workflow** — the owner's *Send Quotation*, rewired: refuses without a customer email, attaches the order's PDF from *Quotation / Order*, sends Odoo's quotation or confirmation email, Quotation → Quotation Sent. **Built 22 Sep 2026, §10 — published, not yet pressed** |
| 2 | **Download** | `sale.action_report_saleorder`, the quotation PDF | **System Print** with a print template — native, no workflow. **Built 22 Sep 2026, §9** |
| 3 | **Confirm** | guards, then Status → Sales Order and **Quotation/Order Date → now** | **button + workflow** (the guard is a branch) |
| 4 | **Preview** | `act_url` to `get_portal_url()` — the customer-facing page | **Public Sharing** — native, effectively already there |
| 5 | **Cancel** | refuses a locked order; Status → Cancelled | **button**, disabled while Locked is ticked |
| 6 | **Create Invoice** | action 495 → a wizard that writes `account.move` | **workflow** — **blocked**, no order → invoice link (§4) |
| 7 | **Set to Quotation** | from Cancelled **or Quotation Sent** → Quotation; clears the signature fields | **button** — one field to write |
| 8 | **Sign & Accept** | on the **portal**: the customer signs, writing `signature` · `signed_by` · `signed_on`, and confirms | **button + two workflows** — *Share for Signature* makes a single-use, no-login fill-in link (the workflow Get Link node) into **Signing Link**; the customer signs on it; *Signed: confirm the order* stamps Signed On, runs Confirm's product check and confirms unless Online Payment is ticked. **Built 22 Sep 2026, §11 — the link's own submission awaits the browser test** |
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
| Online payment (`require_payment`, `prepayment_percent` as behaviour) | The checkboxes are stored; there is no payment. **Online signature is built since 22 Sep 2026** (§11, a no-login fill-in link), and Online Payment only keeps a signed order a quotation |
| Preview · Send as behaviour | No mail. **Download is built** as System Print, §9 |
| `fiscal_position_id`, ~~`incoterm`~~, `project_id`, `preferred_payment_method_line_id` | Each needs a table that is not built. **Incoterm was built on 22 Sep 2026** once Incoterms existed (§12) |
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
| 5 | Pricelist · Fiscal Position · Incoterm | Still absent, all correctly deferred to their bundles. **Incoterm Location is present without Incoterm** — half a pair. **Incoterm built 22 Sep 2026 (§12)** |
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


## 9 · Download — built 22 Sep 2026 (`orders.py` §15)

Odoo's *Download* (the tenant's label; the 19.0 source calls the same header button *Print*) is
`sale.action_report_saleorder`, the quotation / order PDF. Both hide the header button on a Sales Order, but Odoo's
Print menu still offers the report in every state, headed *Quotation* or *Order* by state. Here it is **System
Print with a Word template** — native, so no button and no workflow.

**Piece 1 · Terms and conditions** (`terms`). Odoo's `sale.order.note`, `fields.Html(string="Terms and
conditions", compute='_compute_note', store=True, readonly=False)` (19.0 source, `addons/sale/models/sale_order.py`
149–152). The form (`sale_order_views.xml` 845) puts it on the Order Lines page in `note_group`, below the lines,
placeholder *Terms and conditions...*, with **no readonly and no invisible condition** — in the 19.0 source and in
the tenant extract alike — so **no rule was touched**.

| | |
|---|---|
| Control | **Terms and conditions** `6ab2587bbd43f5576223fb06`, rich text (41), alias `note` — modelled on Invoices' Terms and Conditions (`narration`) |
| Permission | `111`, as Invoices' |
| Hint | Odoo's placeholder *Terms and conditions...* (HAP never draws a rich text's hint) |
| Description | *The terms printed at the foot of the quotation or order.* |
| Default | **none** — see the divergence below |
| Rules | none name it |
| Where it is | appended with `C.append_controls` into the **Order Lines tab** (the payload carried the tab's `sectionId`), **parked at row 9999** — the foot of that tab, below the totals |

**Placement is the owner's.** Intent (`TERMS_PLACE`): the Order Lines tab, a full-width row of its own directly
below the lines and above Untaxed Amount · Tax · Total — where Invoices keeps its Terms and Conditions. Odoo sets it
*beside* the totals (4 of 6 columns against 2); a HAP row has no row-span and the three totals already fill row 12,
so beside is not available without restacking them.

**Divergence — no default.** Odoo's `_compute_note` fills the field from the company's default terms when
`account.use_invoice_terms` is on: the plain `invoice_terms` in the customer's language, or, when `terms_type` is
*html*, a line linking to the company's terms page — recomputed when the customer changes. This app has no company
settings, so the field starts **empty** and is typed per order. What casimir held is **unknown**: the tenant's
`note` was never extracted and the tenant is gone. The one indirect sign is that its three seeded invoices, whose
`narration` Odoo fills from the same setting, carry an empty value (`data/casimir-invoice-seed.json`).

**Piece 2 · the three templates** (`templates`). The Word templates in `nocoly/print-templates/` had been
re-pointed from the Sales app to ERP Master on 21 Sep 2026, all but the Terms placeholder, which still named the
Sales app's own rich text `6a9e38cd4a22ad87b727b5d9` (read to identify it, never written). The placeholder syntax is
`#{<control id>}`, `#{<relation>.<control>}` into a related record or a line, and a trailing `[S]` on some.

| File | Heads the page | Placeholders | On Orders |
|---|---|---|---|
| `quotation_order_template.docx` | **`<Status> # <Number>`** — *Sales Order # S00017* — so **the general one**, for every state | 28 | **uploaded** as System Print *Quotation / Order* |
| `quotation_template_quotation.docx` | *Quotation # `<Number>`* | 27 | not uploaded |
| `quotation_template_order.docx` | *Order # `<Number>`* | 27 | not uploaded |

In all three `#{6a9e38cd4a22ad87b727b5d9}` became `#{6ab2587bbd43f5576223fb06}` and nothing else changed: the
read-back compares every part of each .docx and only `word/document.xml` differs, by that id. All three pass
`unzip -t` and parse as XML, and every placeholder names a live control on Orders or on the worksheet its relation
or the lines lead to. The originals are in `build/backups/print-templates_*_pre_terms_20260922-183005.docx` (not
committed).

**Piece 3 · System Print** (`print`). The main-site API has no single upload call, but pd-openweb — the platform's
open-source front end — shows the three calls the designer makes (`src/pages/FormSet/components/EditPrint.jsx`):
`Qiniu/GetUploadToken {files: [{bucket: 3, ext: '.docx'}], type: 33}` and the bytes to the file store (hap-cli's own
`upload._post_to_store`); `AppManagement/GetToken {worksheetId, tokenType: 5}`; and POST
`<downLoadUrl>/PrintTemplate/EditPrint` with the file key, type 2 (Word) and the name. `Worksheet/GetPrintList`
reads it back. Only the general template went up:

| | |
|---|---|
| Template | **Quotation / Order** `6ab258cd7903a53029f5ade7` — `ids.json` › prints › `Orders: Quotation / Order` |
| File | `quotation_order_template.docx` · type 2 (Word) |
| Settings | range 1 (every view) · no filter · download permission 0 · no edit after print · no advance settings — the same as the Sales app's three Word templates |
| Roles | every role has record printing on for Orders — HAP's default for a worksheet `roles.py` does not own |

**Proved** (`selfprint`, 22 Sep 2026) by filling the template through the same call the print page makes
(`<downLoadUrl>/ExportWord/GetWordPath`) and reading the .docx in memory: for **S00017** (a Sales Order) the page is
headed *Sales Order # S00017*, the lines, totals and payment terms fill, and no placeholder is left. With a TEST
value in its Terms and conditions the value printed under *Terms & Conditions*; the value was then cleared and reads
back empty. A formatted value, `<p>TEST terms <strong>bold</strong> line one</p><p>TEST line two</p>`, printed as two
paragraphs with no tag showing (checked once by hand the same way, and cleared). (`record get` returns nothing for this control on orders that existed before it — the known gap in
CLAUDE.md — so the listing is the path that shows the value.) **Not UI-tested**: nothing here opened a browser.

**Left for the browser.** Place Terms and conditions (intent above). Open an order, print it with *Quotation /
Order* from the record's print menu and look at the page itself — the fill is proved, the layout is not. Upload the
Quotation-only and Order-only templates as well if you want them (the worksheet's form settings, print templates,
new Word template), and if the general one should not be offered in some state, give it a filter there.


## 10 · Send — built 22 Sep 2026 (`orders.py` §16)

Odoo's *Send* is `action_quotation_send` (19.0 source, `addons/sale/models/sale_order.py:1069`): it opens the mail
composer on the order, addressed to the customer, loaded with the template `_find_mail_template` (:1125) picks —
*Sales: Send Quotation* (`email_template_edi_sale`) unless the order is a sale, *Sales: Order Confirmation*
(`mail_template_sale_confirmation`) once it is — and both templates attach the quotation / order report
(`report_template_ids`, `sale.action_report_saleorder`, file name `Quotation - S00017` / `Order - S00017` by its
`print_report_name`). Posting with `mark_so_as_sent` (`message_post`, :1716) moves **only a Quotation** to Quotation
Sent. The form shows Send while `state == 'draft'` and again while `state in ('sent', 'sale')`
(`sale_order_views.xml`, `quotation_send_primary` and `quotation_send`) — every state but Cancelled. *Send an email*
(server action 505) is the batch form.

**The owner's button, rewired rather than replaced.** *Send Quotation* `6ab0aac1e54d2a34fa4e7c1b` and its workflow
`6ab0aac1789584ded3230fe1` were built by hand on 21 Sep 2026 (one run, on S00004, to a TEST contact). Its email had
placeholder text (*[Total Amount: TO BE ADD]*), no attachment and no guard. Kept as the owner left it: id, name,
description, the confirmation dialog, the condition (Status is Quotation, Quotation Sent or Sales Order — already
Odoo's), and **every node of theirs** — nothing was deleted. Changed: **batch on**, and the workflow below.

| | |
|---|---|
| Button | *Send Quotation* `6ab0aac1e54d2a34fa4e7c1b` — `ids.json` › buttons › `Orders: Send Quotation` |
| Workflow | `6ab0aac1789584ded3230fe1` — `ids.json` › workflows › `Orders: Send Quotation` (new key) |
| Offered | Status is Quotation, Quotation Sent or Sales Order — the server's own evaluation (`GetWorksheetBtns` per order) offers it on all ten such orders and on neither Cancelled one |
| Batch | **on** — one run per selected order |
| Confirmation | the owner's: *Email this quotation (or, for a confirmed order, the order confirmation) to the customer, with the PDF attached?* — buttons *Send* / *Discord* (sic, see below) |

```
Trigger by button (once per selected order)
  → Get Customer                         the owner's: the record the Customer relation points at
  → (found / not found)                  the owner's result branch
      not found → Missing customer                    notification to whoever pressed — the run ends
      found     → Amount and signature                code block: Total as "RM 1,234.50"; "--" and the Salesperson
                → Quotation or order?                 the owner's branch (was "Branch"), three paths
                    Quotation         Status Quotation or Quotation Sent, and the customer has an email
                        → Quotation file              print file: "Quotation / Order", PDF, "Quotation - S00017"
                        → Email quotation             the owner's step, rewritten
                        → Set Status: Quotation Sent  the owner's step
                    Order             Status Sales Order, and the customer has an email
                        → Order file                  "Order - S00017"
                        → Email order confirmation
                    No email address  the customer's Email is empty
                        → Missing email address       notification to whoever pressed — the run ends
```

**The emails.** To the customer's Email (through Get Customer), no cc or bcc, plain text, sender name *casimir*
(the company name the print template heads its page with), no reply address, the PDF attached. `<Number>` is the
order's, `<amount>` its Total formatted by the code block, `<signature>` "--" and the Salesperson's name (empty with
no salesperson).

| | Subject | Body |
|---|---|---|
| Quotation, Quotation Sent | `casimir Quotation (Ref <Number>)` | Hello,<br><br>Your quotation `<Number>` amounting in `<amount>` is ready for review.<br><br>Do not hesitate to contact us if you have any questions.<br>`<signature>` |
| Sales Order | `casimir Order (Ref <Number>)` | Hello,<br><br>Your order `<Number>` amounting in `<amount>` has been confirmed.<br>Thank you for your trust!<br><br>Do not hesitate to contact us if you have any questions.<br>`<signature>` |

**The refusals.** A notification reads 【heading】message: **【Missing customer】** *S00013 was not sent: it has no
customer. Choose the customer, then send it again.* · **【Missing email address】** *S000xx was not sent: the customer
has no email address. Add one to the customer's contact, then send it again.* Nothing is written to the order.
*Missing email address* is Odoo's own label for a mail that could not go out.

**Proved without sending anything** (`send`, then `check`, 22 Sep 2026): every node read back — the two print-file
steps on the trigger order with template `6ab258cd7903a53029f5ade7`, PDF on, their file names; both emails' recipient,
subject, body, sender name and attachment (each its own file step's **pdf** output); the three path conditions; both
notices' text and recipient (the person who pressed); Get Customer and the status write as the owner built them; no
abort node; every path's chain exact. The code block's formatting is proved by `codeTest`, which runs only the code:
`1,234` / no salesperson → *RM 1,234.00* and no signature; `74.8` / a plain name → *RM 74.80*; `271743.5` / a member
as JSON → *RM 271,743.50*. The workflow published with no warnings; a second `send` saved and published nothing; the
workflow's run list still holds only the owner's run of 21 Sep. The other six buttons, the whole control set and
*Sign & Accept* read back byte for byte unchanged. **Not UI-tested, and never pressed.**

**Whose inbox a press reaches** (`sendreach`, read-only). All eight contacts carry an email. Orders on which the button
is offered and would email someone: S00007 → *Sunway Construction Group*; S00010 and S00017 → *Klinik Kesihatan
Damansara*; S00012 → *Sarawak Timber Logistics*; S00014 and S00016 → *Casimir*. Those three company addresses are on
real-looking domains. S00006, S00008, S00009 and S00013 have no customer (their seed contacts are not in the app) and
are refused. S00011 and S00015 are Cancelled and not offered.

**Divergences** (DECISIONS.md, *Orders · Send*): no editable composer — the text is fixed and goes on the click; the
batch press sends each order its own templated email and marks each Quotation sent (Odoo's *Send an email* opens one
mass-mail composer with no template and marks nothing); nothing is logged on the order the way Odoo posts the mail
in its chatter; Odoo's *(with reference: …)* line and product-document list are not carried; sent from the
platform's mailer with the name *casimir*, not from the salesperson's address; on a Quotation Sent the status write
re-writes the same value. The refusal still draws the green *Operation completed* toast (15 §6.7, as Confirm).

**For the owner.** The dialog's cancel label reads **Discord** — presumably *Discard*; it is the owner's text and
was left as is. Each send makes a **PDF, which the platform charges to the organisation's credits** — set
`SEND_PDF = False` in `orders.py` and re-run `send` to attach the Word file instead. No reply address is set, so a
customer's reply goes to the platform's sender, not to the salesperson.

**Left for the browser — the live test** (only with the owner's approval; every press sends real email):

1. **Quotation path** on **S00014** (Quotation, customer *Casimir*): the dialog shows the owner's text; after *Send*,
   the mail arrives with subject *casimir Quotation (Ref S00014)*, the amount as *RM 1,120.90* and "--" /
   *Casimir Chiong Ming Yuan* under the text, and **one** attachment, *Quotation - S00014.pdf*, headed *Quotation #
   S00014* — open it; Status then reads **Quotation Sent**. Look at the sender's name and address, and where *Reply*
   goes.
2. **Again on S00016** (already Quotation Sent): the same email; Status stays Quotation Sent.
3. **Order path**: no Sales Order has a safe customer — confirm a TEST order for *Casimir* (or point one at a TEST
   contact) and send it: *casimir Order (Ref …)*, *…has been confirmed. Thank you for your trust!*, *Order - ….pdf*
   headed *Sales Order # …*; Status unchanged.
4. **Guards**: S00013 (no customer) → no mail, 【Missing customer】 in the notification centre, Status unchanged.
   *Missing email address* needs a customer with no email — every contact has one; a TEST contact without one would.
5. **Offered**: absent or greyed on S00011 / S00015 (Cancelled); present on the other ten.
6. **Batch**: select S00014 and S00013 in the list and press it once — one mail, one notification.
7. The run history (`hap approval history --process-id 6ab0aac1789584ded3230fe1`) shows the path each run took;
   the code block's `seen` output holds what Total and Salesperson actually arrived as, which `codeTest` could not
   show. Check the organisation's credit balance for the PDF charge.

Keep clear of S00007, S00010, S00012 and S00017 — they email the three company addresses above.

## 11 · Sign & Accept — built 22 Sep 2026 (`orders.py` §17)

Odoo's *Accept & Sign* is on the customer portal, not the back end. `portal_quote_accept`
(`addons/sale/controllers/portal.py:318`, 19.0 source) refuses unless `_has_to_be_signed()` (`sale_order.py:1896`):
Status is Quotation or Quotation Sent, the quotation hasn't expired (`validity_date < today`, so the Expiration day
itself can still be signed), Online Signature is ticked, and it isn't signed yet. It then writes `signed_by`,
`signed_on = now` and `signature`. Unless `_has_to_be_paid()`, it confirms through `_validate_order` →
`action_confirm`, which runs the same missing-product check as Confirm and then sets Status to Sales Order and the
date to now. It also posts the signed PDF on the chatter and emails the confirmation.

**The owner chose the platform's no-login form for this: the workflow Get Link node (获取链接), fill-in type
(填写链接).** The node's shape comes from pd-openweb `WorkflowSettings/Detail/Link/index.jsx`, and every setting
below was read back.

| | |
|---|---|
| Control | **Signing Link** `6ab27eaae54d2a34faaa9765` — Text, alias `access_url` (Odoo has no field for the link; `portal.mixin`'s `access_url` is the nearest), permission `100`, draws the URL as a link (`analysislink`). Description: *Copy this link and send it to the customer so they can sign and accept the quotation online.* **Parked at row 9999 for the owner to place**; intended (7, 0, 12), its own row under Signature, Signed By and Signed On |
| Button | **Share for Signature** `6ab27f107d58b0f4498fcb8e` — not batch, no confirmation. Offered while **Status is Quotation or Quotation Sent, Online Signature is ticked, Signature is empty, and Expiration is empty or today or later** — all of `_has_to_be_signed`, expiry included since 22 Sep 2026 (below). Description: *Create the link the customer opens to sign and accept this quotation online, and put it in Signing Link. The link works once, and not after the Expiration date.* |
| Its workflow | `6ab27f10789584ded342675d` (ids.json › `Orders: Share for Signature`) |
| Second workflow | **Signed: confirm the order** `6ab28144e606b26d2601895f` (ids.json › `Orders: Signed: confirm the order`) |

```
Share for Signature   offered while (Status is Quotation or Quotation Sent AND Online Signature is ticked AND
                      Signature is empty) AND (Expiration is empty OR Expiration is on or after today)
  Trigger by button
    → Does the quotation expire?
        Expiration is set   (Expiration is not empty)
            → Signing link until the expiration date      Get Link: fill-in, ends at 23:59 on Expiration
            → Save the link (until the expiration date)   Signing Link ← the link
        No expiration date  (else)
            → Signing link with no end date               Get Link: fill-in, no end
            → Save the link (no end date)                 Signing Link ← the link

Signed: confirm the order
  The customer signed   Orders updated, Signature among the fields written; runs only while Signature is filled,
                        Status is Quotation or Quotation Sent and Online Signature is ticked
    → Set Signed On                           Signed On ← now
    → Product lines with no product           Confirm's own count over Order Lines
    → Is a product line missing its product?
        Yes → Quotation signed, not confirmed        notice to the Salesperson; the order stays a quotation
        No  → Is online payment required?
                Online payment    → Quotation signed, payment due    notice; stays a quotation, as in Odoo
                No online payment → Confirm the order                Status ← Sales Order, Quotation/Order Date ← now
                                  → Quotation signed                 notice: "S000xx was signed by <Signed By>."
```

**What the customer sees on the link:** Number, Status, Customer, Invoice Address, Delivery Address, Expiration,
Quotation/Order Date, Delivery Date and Payment Terms; the Order Lines tab with the lines (Product, Description,
Quantity, Unit, Unit Price, Discount, Taxes, Tax Amount, Subtotal, Total — no adding, editing, deleting or
exporting); Untaxed Amount, Tax, Total and Terms and conditions. All of these are view only. **Signature and
Signed By** are editable and required. Everything else is hidden: Signing Link, Locked, Is Template, Template Name,
Discount Type and Value, Invoicing Closed, the two statuses, Signed On, Tax Mode, and the whole Other Info tab. A
control added later is hidden by default. The submit button reads **Accept & Sign**. After submitting, the link
can be neither viewed nor changed, so it works once. No password.

**Confirm's writes, not new ones.** *Confirm the order* carries exactly the two writes of Confirm's own step.
*Product lines with no product* is Confirm's own count (Orders is this order, Display Type is Product, Product is
empty). The three notices go to the order's **Salesperson** in the app. *Set to Quotation* clears Signature, which
fails the trigger's condition, so no run starts at all.

**Proved without a browser** (`sign`, `signtest`, `selfsign`, `check`, 22 Sep 2026):

- Every node read back as built. For both links that means the record, fill-in, "Accept & Sign", no revisiting, no
  password, new controls hidden, the property of every control, the subtable's column switches and columns, and
  the dated link's end (Expiration, 23:59). Both write steps store `$<link step>-link$` into Signing Link. The
  path and trigger conditions and the three notices' text and recipient read back too. Both workflows published
  with no warnings, and a second `sign` saved and published nothing.
- **Signature takes "edit and required" on the link although it is read-only on the form.** The node saved and
  read back property 3 for it. Whether the public page honours that is the browser test's first check.
- **The expiry works, and it is not the start of the day.** `Worksheet/GetLinkDetail`, the public page's first
  call, answers **17, "link expired"**, for S00022, whose Expiration was yesterday. It answers "open" for S00021,
  whose Expiration is **today**, at 21:45 on that day. That rules out the start of the day and the editor's 08:00
  default. That S00021 dies at 23:59 is for tomorrow.
- **The server offers the button exactly where it should** (`GetWorksheetBtns` per order): on the Quotations and
  Quotation Sents with Online Signature ticked, no signature and no Expiration in the past, and on nothing else.

**Not offered once the quotation has expired (added 22 Sep 2026, 22:13).** Odoo's `_has_to_be_signed` includes
`not is_expired`, and `is_expired` is `validity_date < today` (19.0 source), so the Expiration day itself still
counts. The button used to be offered on an expired quotation and make a link that was already dead. Its condition
is now two groups joined by AND:

| Group | Joined by | Conditions |
|---|---|---|
| 1 | AND | Status is any of Quotation, Quotation Sent · Online Signature is ticked · Signature is empty |
| 2 | OR | Expiration is empty · Expiration is **on or after today** |

- **The date shape comes from pd-openweb**, not a guess. `WorkSheetFilter/enum.js` gives *on or after* (晚于等于) as
  `FILTER_CONDITION_TYPE.DATE_GTE` **34** and *today* (今天) as `DATE_OPTIONS` value **1**, stored as the condition's
  `dateRange`. `components/contents/Date.jsx` clears `dateRangeType` when *today* is picked. The server stored
  exactly `filterType 34, dateRange 1, dateRangeType 0`, as the editor would. hap-cli's `ge` operator lowers to the
  number comparison 14, and its translator carries no `dateRange`, so `sign_filters` writes the second group by hand.
- **Groups, because a mix of AND and OR has no other shape.** The button's filter dialog (`ShowBtnFilterDialog`)
  opens `FilterConfig` with `supportGroup`. It reads a list whose first entry `isGroup` as groups throughout, with
  one relation between the groups and one inside each (`model.formatForSave`). The first group is hap-cli's own
  lowering of the three old conditions, unchanged.
- **Written in place**, as `send` turned Send Quotation's batch flag on: `Worksheet/SaveWorksheetBtn` with the
  button's `btnId` and everything the button editor sends, as read, with only `filters` replaced. Every other key
  of the button read back unchanged, and so did the other seven buttons and the whole control set. Backup:
  `backups/orders_buttons_pre_sign_expiry_20260922-221345.json`. A second `sign` saved nothing.
- **Greyed out or hidden is the page's choice, not a setting.** The button has no hide-or-grey option: its editor
  offers only *always* or *when the filter matches* (`showType`). pd-openweb's `CustomButtons` hides a disabled
  button where the record is opened without a view (`hideDisabled = type === 'iconText' || !viewId`) and greys it
  everywhere else, so it greys out in the pop-up record like the other Orders buttons. That matches BUILDING.md's
  note under *Buttons*.
- **Proved by the server**, `GetWorksheetBtns` with each order's rowId, at 22:13 on 22 Sep 2026:

  | Order | Status | Expiration | Before | After |
  |---|---|---|---|---|
  | S00021 | Quotation, unsigned | 22 Sep (today) | offered | **offered** |
  | S00022 | Quotation, unsigned | 21 Sep (yesterday) | offered | **disabled** |
  | S00023 | Quotation, unsigned | none | offered | **offered** |
  | S00008 | Quotation Sent, unsigned | 20 Sep | offered | **disabled**, expired too (a seeded order) |
  | S00009 · S00013 · S00014 · S00016 | Quotation / Quotation Sent, unsigned | 27 Sep – 14 Oct | offered | offered |
  | the other ten | signed, confirmed, cancelled, or Online Signature off | — | disabled | disabled |

  `check` asserts this per order through both read paths. It compares against this machine's date (+08:00). The
  server's "today" is the app's, the same date while both are in +08:00. From 23 Sep, S00021 is disabled too.
- **Downstream of the link, all of it runs** (`selfsign`, on S00020, its own TEST order). An API write of Signature
  and Signed By is the worksheet event the link is expected to cause:

  | Case | Run | Order afterwards | Notice (as sent, to Casimir Chiong Ming Yuan) |
  |---|---|---|---|
  | lines complete, no online payment | Set Signed On → count → No → No online payment → Confirm the order → Quotation signed | **Sales Order**; Quotation/Order Date and Signed On = the signing minute | *S00020 was signed by TEST signer.* |
  | Set to Quotation on it | **no run** | Quotation; Signature, Signed By, Signed On empty | — |
  | a product line with no product | … → Yes → Quotation signed, not confirmed | still **Quotation**; signature kept; Signed On set | *S00020 was signed by TEST signer, but it was not confirmed: some order lines are missing a product. Correct them, then confirm it.* |
  | Signature cleared by the API | **no run** | — | — |
  | Online Payment ticked | … → Online payment → Quotation signed, payment due | still **Quotation**; Signed On set | *S00020 was signed by TEST signer. It stays a quotation because it asks for online payment.* |

**Not proved: whether the link's submission starts *Signed: confirm the order*.** The public page saves through the
ordinary record editor (pd-openweb `WorksheetRowEdit`), so it should count as an update. That is the browser test's
second check. If no run appears, the trigger becomes a **scheduled workflow**: every few minutes it looks for
orders with Online Signature ticked, a Signature, no Signed On and Status Quotation or Quotation Sent, and runs the
same steps on each. Signed On empty is the "not handled yet" mark.

**TEST orders**, all for *TEST QA Trading Sdn Bhd, TEST Person One*, Salesperson Casimir, Online Signature ticked,
one line copied from S00006 (*Business Laptop 14" i7*, 1 × 5,400.00 at its taxes). Each is found by its Customer
Reference and recorded in `ids.json` › records. None has been sent anywhere.

| Order | Customer Reference | Online Payment | Expiration | Signing Link |
|---|---|---|---|---|
| **S00018** | TEST Sign & Accept | no | 29 Sep | https://www.nocoly.com/public/workflow/6ab2829a480ec07369259f1e |
| **S00019** | TEST Sign & Accept, online payment | yes | 29 Sep | https://www.nocoly.com/public/workflow/6ab2829edd767e035b70194a |
| S00021 | TEST Sign & Accept, expires today | no | 22 Sep | https://www.nocoly.com/public/workflow/6ab28657863f2dc2a7a7e397 |
| S00022 | TEST Sign & Accept, expired yesterday | no | 21 Sep | https://www.nocoly.com/public/workflow/6ab28662480ec07369259f21 — answers "link expired" |
| S00023 | TEST Sign & Accept, no expiration | no | — | https://www.nocoly.com/public/workflow/6ab2866d863f2dc2a7a7e398 |
| S00020 | TEST Sign & Accept, CLI run | yes (left so) | 29 Sep | none — `selfsign`'s; left signed, a Quotation |

**Left for the browser — the live test.** Open each link in a private window, not signed in.

1. **S00018's link.** The page should show only the fields listed above: the ten line columns, and no Signing
   Link, Locked, discount fields or Other Info. Signature and Signed By should be marked required, and the button
   should read *Accept & Sign*. Pressing it empty must be refused.
2. **Sign and press *Accept & Sign*.** The page should report that it was submitted.
3. **In the app, S00018** should have Signature and Signed By filled (this proves the link can write a field that
   is read-only on the form), Signed On at the signing time, **Status Sales Order**, and Quotation/Order Date moved
   to now. 【Quotation signed】 *S00018 was signed by <name>.* should be in your notifications, and *Share for
   Signature* should be gone from the order. If Status is still Quotation, run
   `hap approval history --process-id 6ab28144e606b26d2601895f`. A run for S00018 means a step is wrong; tell me.
   **No run means the link's submission starts no workflow**, and the trigger becomes the scheduled scan above.
4. **Reopen S00018's link.** It should show only "submitted", with no form (single use).
5. **S00019's link:** the same, but the order **stays a Quotation**, with 【Quotation signed, payment due】.
6. **S00023's link** (no Expiration) opens like the others. You may leave it unsigned.
7. **S00022's link** should say the link has expired. **S00021's link** should open today and say "expired" after
   midnight. That is where the cutoff is. On S00022 (and, from 23 Sep, S00021), **Share for Signature** should be
   greyed out in the pop-up record and absent from the full-page record. On S00023 (no Expiration) it should be
   offered.
8. Optional: on a signed test order, *Set to Quotation* should clear the three signature fields and start no run
   of *Signed: confirm the order*.

**Credits — not built, and nothing here spends any** (prices from help.nocoly.com/purchase/billing-items, where
$1 = 1 credit):

| Option | What it adds | Per use | How it fits |
|---|---|---|---|
| (a) The quotation email carries the link | Odoo's *View Quotation* button | nothing on top of Send's own 0.002 per recipient (and 0.03 per PDF) | In Send's *Quotation* path, put the link into *Email quotation*'s body. Either read Signing Link (`$trigger-Signing Link$`, blank until Share for Signature has been pressed), or copy the dated/open Get Link pair and its write in front of *Quotation file*, so every send makes a fresh link. The node's link name (e.g. *View Quotation*) makes it a hyperlink in the email |
| (b) Confirmation email after signing | Odoo's `_validate_order` mail | 0.002 per recipient; +0.03 with the PDF | On *No online payment*, after *Confirm the order*: Get Customer → Order file (PDF) → *Email order confirmation*, the three steps Send's *Order* path already has |
| (c) The signed PDF kept on the order | Odoo's chatter post of the signed quotation | 0.03 per signing (a Word file is free) | Add Signature, Signed By and Signed On to the Word template. Add an Attachment control (e.g. *Signed Quotation*). In *Signed: confirm the order*, after *Set Signed On*: a print file step (PDF) → write it to that control |
| (d) A customer portal with verification codes | Odoo's `/my/orders` | each login code by SMS 0.34 as the page states (international), or by email 0.002 | The platform's external portal. Customers are portal users tied to their contact and see their own orders, and sign in a view instead of a link. A larger build that would replace the link, not add to it |


## 12 · Incoterm — built 22 Sep 2026 (`orders.py` §18)

Odoo's `sale_stock` adds `incoterm` (Many2one `account.incoterms`, `options="{'no_open': True, 'no_create': True}"`)
and `incoterm_location` (Char) to the order and shows them together under *Other Info › Shipping*
(sale_stock/views/sale_order_views.xml:27-28, 19.0 source; the tenant extract lists the same pair under Shipping).
The owner had built **Incoterm Location** by hand on 21 Sep 2026; this completes the pair once the Incoterms worksheet
existed (19-incoterms.md).

| Control | Id | Type | Alias | Permission | Notes |
|---|---|---|---|---|---|
| **Incoterm** | `6ab29e24e43d174ab3cd7675` | Relation → Incoterms, single, **one-way**, dropdown | `incoterm` | `111` | **appended**; picker filter *Active is ticked*; shows the Display Name "[FOB] FREE ON BOARD"; description Odoo's help. Stored in the **Other Info** tab at **row 9999** — the owner places it |
| Incoterm Location | `6ab0c528e54d2a34fa4e8124` | Text | `incoterm_location` | `""`, as the owner left it | **the owner's control**; only its alias was written, in one version-pinned save whose signature diff named that control alone (of 45) |

`INCOTERM_PLACE` is the intent: **a full-width row of its own directly under the *Shipping* divider** (row 22), so the
tab reads Shipping › Incoterm › Incoterm Location, Odoo's order; Incoterm Location and everything under it move down
one row.

**No read-only rule.** Odoo leaves both editable in every state: the view gives neither a `readonly`, and
`sale.order.write` refuses only a pricelist change on a confirmed order. So *A confirmed or cancelled order is closed
for editing* and *A locked or cancelled order is closed for editing* were **not** extended. Odoo's `no_create` on the
picker is the Roles' job — every business role only views Incoterms.

**Views.** The owner's **All** view has no custom columns, so it shows every field and Incoterm joined it as a column;
Quotations, Orders and Templates use custom columns and did not change. Odoo's list has no Incoterm column.

**Self-check** (`selfincoterm`): on *TEST Sign & Accept, CLI run* (`8aa92a30-1a0c-4ee5-973d-1a141d81d849`), Incoterm set
to FOB and Incoterm Location to "TEST Port Klang" through `record update`; `record get` and the listing both read back
`[FOB] FREE ON BOARD` with its rowid and the text; both put back empty and read back empty both ways. No Orders
workflow fires on them (*Signed: confirm the order* is narrowed to Signature).

`check` now reads both back — exactly one control of each name, the owner's id for Incoterm Location, type, alias,
permission, one-way, the picker filter, ids.json, and Incoterms' title — and notes while Incoterm is still parked.

**Not built**: the order's Incoterm and location carried onto its invoice (`_prepare_invoice` writes
`invoice_incoterm_id`; `account.move._compute_incoterm_location` joins the orders' locations) — it waits for the
order → invoice link (§4).

## Descriptions rewritten for the app's users (22 Sep 2026)

The owner's rule of 22 Sep 2026: a description in the app says only what the field or button does, for the people using it — no Odoo, no field or model names, no divergences, no build notes. The texts below were rewritten or emptied on the live app and in the builder's constants. The old text is kept here, word for word, because it carried the Odoo references and build reasoning that are no longer in the app.

**Orders**

| Control | Key | Before | After |
|---|---|---|---|
| Is Template | desc | A template is a quotation kept to be recreated from, not sent to a customer. Use the record menu's Recreate to start a real quotation from it — Recreate copies the order lines, Copy does not. Not an Odoo field: `sale.order` has no `is_template`. | Tick to keep this quotation as a template instead of sending it. Recreate from the record menu to start a quotation from this template: Recreate copies the order lines, Copy does not. |
| Template Name | desc | What this template is called in the Templates view. Not an Odoo field: `sale.order` has no `template_name`. | The name shown for this template in the Templates view. |
| Signature | desc | The signature the customer drew when they accepted this quotation on a shared page. Written by Sign & Accept and cleared by Set to Quotation — never typed, which is why it is read-only and hidden on create. The Online Signature checkbox is only a request for a signature and stores nothing; this is where the signature itself lands. | The signature the customer drew when accepting the quotation online. Filled in automatically and cleared by Set to Quotation. |
| Signed By | desc | The name the customer gave when they accepted this quotation on a shared page. Written by Sign & Accept and cleared by Set to Quotation — never typed, which is why it is read-only and hidden on create. Online Signature is only the request; this is who signed. | The name the customer gave when accepting the quotation online. Filled in automatically. |
| Signed On | desc | When the customer accepted this quotation on a shared page. Written by Sign & Accept and cleared by Set to Quotation — never typed, which is why it is read-only and hidden on create. Online Signature is only the request; this is when the signature arrived. | When the customer accepted the quotation online. Filled in automatically. |
| Discount Type | desc | Stands in for Odoo's discount wizard (sale.order.discount), which is a dialog and not part of the order. Global Discount: Discount Value is a percentage of each tax group's subtotal. Fixed Amount: Discount Value in RM, shared over the tax groups in proportion to their subtotals. Press Apply Discount to write the discount lines. Odoo's third mode, On All Order Lines, is the lines' own Discount % — use the subtable's Batch Operation. | Global Discount takes Discount Value as a percentage off the order. Fixed Amount takes it as an amount in RM off the order total, tax included. Press Apply Discount to add the discount lines. To discount single lines, use the lines' Discount instead. |
| button Confirm | desc | Confirm this quotation as a sales order, and stamp Quotation/Order Date with the confirmation time. Refused, with a notification, while any product line has no Product. | Confirm this quotation as a sales order and set the Quotation/Order Date to now. Not possible while a product line has no product. |
| button Cancel | desc | Cancel this order. Not offered on a locked order — untick Locked first, as Odoo asks you to unlock it. | Cancel this order. Not available on a locked order: untick Locked first. |
| button Deliver | desc | Set every product line's Quantity Delivered to its own Quantity — for an order that is not delivered through Inventory. Offered on a Sales Order only (our judgment: Odoo's own guard for this action is not in the Community source). | Set every product line's Quantity Delivered to its Quantity. Available on a sales order only. |
| button Apply Discount | desc | Odoo's Discount button (the sale.order.discount wizard), named Apply Discount here so it is not confused with the lines' Discount % column. Writes the discount set in Discount Type and Discount Value as Discount lines, one per tax combination, as Odoo does — replacing any this order already has, so it can be pressed again. With Discount Value empty or 0 it removes them. Not offered on a locked or cancelled order. | Add discount lines for the Discount Type and Discount Value, replacing any discount lines already on the order. With Discount Value empty or 0, removes them. Not available on a locked or cancelled order. |

**Order Lines**

| Control | Key | Before | After |
|---|---|---|---|
| Tax rate | desc | The sum of the Amounts of this line's Taxes, counting only the ones whose Tax Computation is Percentage — so a Fixed or Custom Formula tax cannot add its amount as if it were a rate. A roll-up (汇总) over the Taxes relation; hidden and read-only, and Total is computed from it. | The combined percentage of this line's taxes. |

### Form text corrected (22 Sep 2026)

| Control | Type | Key | Before | After |
|---|---|---|---|---|
| The owner's search button, `6ab0f80f7d58b0f449317238` | 49 | controlName | Sign & Acccept | Sign & Accept |

A typo, three c's, fixed at the owner's request in one version-pinned save of that one attribute; its button text
(`hint` "Query") and everything else are as the owner left them. `orders.py` OWNERS_CONTROL follows, so `buttons`
and `check` recognise it. No custom button carries the name, and no `ids.json` key records this control.

**The owner deleted this placeholder later on 22 Sep 2026**, once Sign & Accept was to be built as a Get Link workflow
(§11). `orders.py` no longer expects it — `buttons`, `send` and `check` used to compare it byte for byte and stop
without it — and `check` only notes it should that id come back. No `ids.json` key ever carried it, so none was
removed.
