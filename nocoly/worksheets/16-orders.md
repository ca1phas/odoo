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
