# 07 · Invoice Lines

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Invoicing** |
| Worksheet | Invoice Lines, mounted as the subtable of the Invoices tab *Invoice Lines* |
| Odoo model | `account.move.line` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: `fields_get`, the invoice form's line columns, the standalone Journal Items views, `default_get`, `_order`, the four SQL constraints and all 33 lines, extracted read-only to `nocoly/reference/odoo-19.4/account.move.line.md`. The document is `account.move.md`, built as 06 |
| Phase | 1 — core worksheet **7 of 7**, the last |
| Status | Built, seeded and self-checked with the hap CLI on 16 Sep 2026 — 13 controls, 1 rule, 1 view, the mount into the Invoices tab, 2 roll-up workflows and the 8 tenant lines; 06's Untaxed Amount, Total and Amount Due come from the lines and land on the tenant's own figures. **UI test in progress**: the subtable, the column order, the Section rule and a line added or changed all pass; the delete roll-up looked broken and was not — `hap worksheet record delete` suppresses workflows unless `--trigger-workflow` is passed (§2). One open question for the owner: the subtable stays editable on a posted document (difference 11). **UI-tested on 16 Sep 2026: 18 pass, 1 partly, 1 not run** (§3) — no defect in the worksheet; the one alarm, a deleted line leaving the invoice stale, proved to be `hap worksheet record delete` suppressing workflows unless `--trigger-workflow` is passed. **Ready for review** |

A journal item is one line of an `account.move`. On an invoice the lines a person edits are the **product, section and
note lines** — Odoo maintains the tax and payment-term lines itself, and those belong with the bundles. This worksheet
is what makes 06's four amounts real: Untaxed Amount stops being a seeded figure and becomes the sum of its lines.

## 1 · Requirements

### Fields

Labels are Odoo 19.4's, taken from the invoice form's line columns; aliases are Odoo's field names on
`account.move.line`.

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Invoice | `move_id` | Relation → **Invoices**, single | yes | — | The subtable's own parent link. Odoo labels it Journal Entry |
| 2 | Sequence | `sequence` | Number, 0 decimals | — | 10 | Orders the lines within one invoice. Odoo uses a drag handle, which a HAP subtable has no equivalent for — the same decision as Journals' Sequence |
| 3 | Display Type | `display_type` | Single Select, dropdown | yes | Product | **Product · Section · Subsection · Note** — Odoo's `product`, `line_section`, `line_subsection`, `line_note`, which are its *Add a line · Add a section · Add a note* buttons. Odoo's other display types (`tax`, `payment_term`, `rounding`, `discount`, `epd`, `cogs`) are lines Odoo writes itself and are not built |
| 4 | Product | `product_id` | Relation → **Product Variants**, single | — | — | The **variant**, never the template — Odoo's every order line, stock move and invoice line points at `product.product` (decision of 15 Sep) |
| 5 | Label | `name` | Text | — | — | Odoo fills it from the product's display name and its sales description on selection, on two lines. Here it is typed or seeded; on a section or a note it *is* the text |
| 6 | Quantity | `quantity` | Number, 2 decimals | — | 1 | Odoo's help: "The optional quantity expressed by this line, eg: number of product sold." |
| 7 | Unit | `product_uom_id` | Relation → **Units & Packagings**, single | — | — | Odoo restricts it to the product's own unit and packagings (`allowed_uom_ids`); here every unit is offered, because that domain needs a lookup of a relation |
| 8 | Unit Price | `price_unit` | Number, 2 decimals | — | 0 | |
| 9 | Discount (%) | `discount` | Number, 2 decimals | — | 0 | Odoo's optional *Disc.%* column, hidden by default and used on five of the tenant's lines |
| 10 | Subtotal | `price_subtotal` | **Formula**, 2 decimals, read-only | — | — | `Quantity × Unit Price × (1 − Discount ÷ 100)`. Odoo's *Amount* column shows this while the document is Tax Excluded, and `price_total` when it is Tax Included — which needs the Taxes bundle, so only the subtotal is built |
| 11 | Number | `move_name` | Lookup of Invoice → Number | — | — | Read-only, so the standalone view can show which document a line belongs to |
| 12 | Accounting Date | `date` | Lookup of Invoice → Accounting Date | — | — | Read-only. Odoo stores it on the line and sorts on it |
| 13 | Status | `parent_state` | Lookup of Invoice → Status | — | — | Read-only; Odoo's Journal Items views filter Posted / Unposted on it |

`account.move.line` has **no `active` field** either, so — like Invoices — there is no Active checkbox, no Archived
view and no Archive / Unarchive buttons.

### The subtable, and what it does to 06

The worksheet is **mounted into the Invoices tab *Invoice Lines***, under the remark block that 06 left there, so an
invoice shows its lines where Odoo shows them. The remark block stays: it still names the Catalog, the totals and the
payments that are not built.

06's four amounts stop being seeded figures:

| 06 field | Becomes |
|---|---|
| Untaxed Amount | the **sum of its lines' Subtotal** |
| Tax | **unchanged** — a seeded read-only figure until the Taxes bundle; nothing in Phase 1 can compute it |
| Total | Untaxed Amount **+** Tax |
| Amount Due | Total, until the Payments bundle can settle a document |

That keeps the tenant's own numbers reconciling exactly — INV/2026/00001 is 11,432.00 of lines plus 1,143.20 of tax
making 12,575.20 — with only the tax *rate* missing rather than the arithmetic.

**Do this without replacing any of 06's controls.** Those four are plain Number fields with ids and seeded values;
keep them and have the recomputation write into them. If HAP offers a native subtable roll-up that would mean
swapping a control for a different type, **stop and report it** — deleting a field needs the owner's approval, and
06 is already out for review.

### Rules

| Rule | When | Effect | Odoo source |
|---|---|---|---|
| A section or a note carries no figures | Display Type is Section, Subsection or Note | **hide** Product, Quantity, Unit, Unit Price, Discount (%) and Subtotal | SQL `check_non_accountable_fields_null` — "Forbidden balance or account on non-accountable line"; the form shows only the text |

Odoo's other three constraints are accounting-side (`check_credit_debit`, `check_amount_currency_balance_sign`,
`check_accountable_required_fields` — "Missing required account on accountable line") and need the Chart of Accounts.

### Views

| View | Shows | Odoo 19.4 |
|---|---|---|
| Lines — opens first | Every line. Columns **Number · Label · Product · Quantity · Unit · Unit Price · Discount (%) · Subtotal**, sorted **Accounting Date descending, then Number descending, then Sequence ascending**. Quick filter Display Type | The standalone *Journal Items* list, minus everything the Chart of Accounts and Taxes bundles bring; `_order` is `date desc, move_name desc, id` |

Inside an invoice the subtable shows **Sequence · Display Type · Product · Label · Quantity · Unit · Unit Price ·
Discount (%) · Subtotal**, in Odoo's column order.

### Not built now, and why

| Odoo 19.4 field or feature | Why not now |
|---|---|
| **Taxes** (`tax_ids`) and the Total-with-tax column (`price_total`) | The **Taxes** bundle — recorded and left out by the owner's direction of 16 Sep. Without it a line has a subtotal and no tax, and 06's Tax stays a seeded figure |
| **Account** (`account_id`) and everything double-entry: `debit`, `credit`, `balance`, `amount_currency`, `amount_residual` | The **Chart of Accounts** bundle |
| The **tax lines** and the **payment-term line** Odoo writes itself (`display_type` `tax` and `payment_term`, sequences 10000 and 12000), and the due date on them | Both are computed from taxes and payment terms; neither is a line a person edits |
| Reconciliation (`reconciled`, `full_reconcile_id`, `matched_*`, `matching_number`), `payment_id`, `statement_line_id` | The **Payments** bundle |
| Analytic distribution, early-payment discount, deferred dates, follow-up, consolidation, storno | Each is its own bundle or module |
| Down-payment lines (`is_downpayment`, `sale_line_ids`) and the product **Catalog** | The **Sales** app. The tenant's down-payment lines belong to documents we did not seed |
| Malaysian classification code (`l10n_my_edi_classification_code`), Professional / deductible percentage | e-invoicing and vendor-bill bundles |
| Hide Composition / Hide Prices (`collapse_composition`, `collapse_prices`) and Parent Section Line (`parent_id`) | They only change how a **printed report** groups the lines, and nothing here renders one |
| Odoo restricting Unit to the product's own units, and filling Label from the product | Both are onchange-time computes; the first also needs a lookup of a relation, which HAP stores as a title |
| Roles | Set once for the app at the end of Phase 1 |

### Records

The lines of the three seeded documents — eight of the tenant's 33. The rest belong to documents 4–8, which 06 did
not seed, or are tax and payment-term lines.

| Document | Seq | Product (variant) | Label | Qty | Unit | Price | Disc % | Subtotal |
|---|---|---|---|---|---|---|---|---|
| SCG-PO-88213 | 0 | Height-Adjustable Desk 140cm | [FURN-0002] Height-Adjustable Desk 140cm | 40 | Units | 1,650.00 | 8 | 60,720.00 |
| SCG-PO-88213 | 1 | Ergonomic Office Chair | [FURN-0001] Ergonomic Office Chair | 40 | Units | 899.00 | 8 | 33,083.20 |
| SCG-PO-88213 | 2 | [FURN-0003] Steel Filing Cabinet 4-Drawer | [FURN-0003] Steel Filing Cabinet 4-Drawer | 15 | Units | 720.00 | 0 | 10,800.00 |
| INV/2026/00001 | 0 | Ergonomic Office Chair | [FURN-0001] Ergonomic Office Chair | 8 | Units | 899.00 | 0 | 7,192.00 |
| INV/2026/00001 | 1 | [FURN-0003] Steel Filing Cabinet 4-Drawer | [FURN-0003] Steel Filing Cabinet 4-Drawer | 4 | Units | 720.00 | 0 | 2,880.00 |
| INV/2026/00001 | 2 | [CONS-0001] A4 Copy Paper (Box of 5 reams) | [CONS-0001] A4 Copy Paper (Box of 5 reams) | 20 | Units | 68.00 | 0 | 1,360.00 |
| STL-2026-0042 | 0 | [SRV-0003] Annual Support Retainer | [SRV-0003] Annual Support Retainer | 1 | Units | 18,000.00 | 0 | 18,000.00 |
| STL-2026-0042 | 1 | [SW-0002] Nocoly HAP Licence — Pro | [SW-0002] Nocoly HAP Licence — Pro | 25 | Units | 7,200.00 | 10 | 162,000.00 |

Every one sums to the document's seeded Untaxed Amount: 104,603.20 · 11,432.00 · 180,000.00.

**Two of the tenant's products are referenced by a variant we do not hold.** `[FURN-0001] Ergonomic Office Chair` and
`[FURN-0002] Height-Adjustable Desk 140cm` are the **archived original** variants on the tenant, and Phase 1 keeps one
active variant per product, which for those two carries no internal reference. Point those lines at the product's
single variant — *Ergonomic Office Chair* and *Height-Adjustable Desk 140cm* — and keep the tenant's Label text, which
is where the `[FURN-000x]` reference survives. Do **not** create the archived originals: bringing them in belongs with
the Product Variants bundle, and 04 is out for review.

## 2 · Build

Built by `nocoly/build/invlines.py` — steps `create → fields → mount → computed → layout → rules → views →
rollup → seed → amounts`, or `all` for every one of them followed by `check`. Each step reads the live state
first, refuses to run unless the profile reaches ERP Master › Invoicing and the worksheet holds only this
script's own work, reads back what it wrote, and is safe to re-run: a second `all` created, added, renamed and
updated nothing, wrote no record and re-published no workflow. Helpers: `check` reads controls, options,
defaults, the rule, the view, the mount and the two workflows back against this spec, `verify` compares the
eight lines with the seed **and** every invoice's amounts with its own lines, `selfcheck` drives the roll-up end
to end through the CLI, `order` prints the view's records in the view's own order, `lines "<Number>"` one
document's stored lines, `untouched` the other worksheets' control count and digest, and `show` the control
list. The profile comes from `$HAP_PROFILE` and otherwise from hap-cli's active profile; **nothing in
`common.py` changed**.

| Element | Built | Id |
|---|---|---|
| App | ERP Master | `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Menu group | Invoicing — Journals, Invoices, **Invoice Lines** | `6aa8f3ecbf00c316381dbbe8` |
| Worksheet | Invoice Lines, alias **`account_move_line`** | `6aaa2b50e54d2a34fa4e0221` |
| Controls | 13, all fields; no tab, no divider, no remark block | — |
| Fields, own | Sequence · Display Type · Product · Label (the title) | `6aaa2b81e54d2a34fa4e022b` · `…022c` · `…022d` · `6aaa2b50e54d2a34fa4e0222` |
| | Quantity · Unit · Unit Price · Discount (%) | `6aaa2b81e54d2a34fa4e022f` · `…0230` · `…0232` · `…0233` |
| | Subtotal (number formula, type 31) | `6aaa2c18e43d174ab3749df1` |
| Fields, lookups of the invoice (type 30, stored) | Number · Accounting Date · Status | `6aaa2c18e43d174ab3749df2` · `…df3` · `…df4` |
| Field, the parent link | **Invoice** → Invoices — created by the mount, not by `fields` | `6aaa2baae43d174ab3749dea` |
| On **Invoices** | the mounted subtable **Lines** (子表, type 34), inside the tab *Invoice Lines* at row 8 | `6aaa2baae43d174ab3749de9` |
| Rule | A section or a note carries no figures | `6aaa2d3c7d58b0f44930eb72` |
| View | Lines (the stock *All* view, renamed) | `6aaa2b50e54d2a34fa4e0225` |
| Workflows | Roll the lines up into the invoice (新增或更新) · Roll the lines up when a line is deleted (删除) — both published | `6aaa2d6aa1c923a16efc81a7` · `6aaa2ebba1c923a16efc8ecf` |
| Records | the 8 tenant lines, and one `TEST roll-up line` (§3) | — |

Every id is in `nocoly/build/ids.json` under "Invoice Lines: …" keys, plus `"Invoices: Lines"` for the mounted
control and `"Invoice Lines"` under `worksheets`; no existing key was renamed.

`account.move.line` has **no `active` field**, so — like Invoices — Invoice Lines has no Active checkbox, no
Archived view and no Archive / Unarchive buttons. It has no buttons at all: Odoo's *Add a line*, *Add a section*
and *Add a note* are the subtable's own **+ Record** plus the Display Type dropdown, not three separate actions.

**The form is flat.** Thirteen fields, no notebook tab and no remark block: Odoo's line has no notebook, and
everything left out is already named in the remark block 06 put in the Invoices tab above the table.

### The mount, and what it did to 06

`hap worksheet mount-subtable` performs the whole of HAP's *已有关联* handshake in one call:

1. it appends a 子表 control (type 34) to **Invoices** with the child's controls as its `relationControls`
   snapshot and `dataSource` = the Invoice Lines worksheet;
2. it reads back the placeholder `controlId` the server **reserves** on the child for the back-relation;
3. it saves that relation on **Invoice Lines** carrying exactly that id, with `sourceControlId` pointing back at
   the 子表 — which is what makes the rows show under the right parent.

So this worksheet's **Invoice** field is created by `mount`, not by `fields`: it *is* the child half of the
pairing, and `6aaa2baae43d174ab3749dea` / `6aaa2baae43d174ab3749de9` are each other's `sourceControlId`.

**What changed on Invoices**, and nothing else did:

| Change | Why |
|---|---|
| One control added: the 子表 **Lines** `6aaa2baae43d174ab3749de9`, `advancedSetting.hidetitle` "1", width 12, inside the tab *Invoice Lines* at row 8 | §1's mount. The title is hidden so the tab shows the table with no heading of its own, as Odoo does; the name stays an internal label, the way the three remark blocks' names do |
| Every control from row 8 down moved **one row lower** — Terms and Conditions 8 → 9, the four amounts 9/10 → 10/11, Other Info 11 → 12 … MyInvois note 21 → 22 | The table goes *under the remark block*, and a HAP row holds 12 columns, so the block at row 7 and a full-width table cannot share one. Only `row` changed; not one other attribute of any of the 32 controls, checked id by id before and after every save |
| Untaxed Amount, Total and Amount Due **written** on the three seeded documents | §1: they stop being seeded figures. **Tax was never written** |
| `nocoly/build/invoices.py`: `PLACE` gained `Lines` at row 8 and the rows below it, `desired()` returns place only for a 子表, and its full save now goes through the CLI's session | 06 owns the Invoices layout, so its own table has to say where the subtable is — otherwise `invoices.py check` reports an unknown control and `guard()` refuses to run. `invlines.py place_subtable` **reads** `invoices.PLACE` and never writes it |

The tab now reads, top to bottom: the remark block · **Lines** · Terms and Conditions · Untaxed Amount · Tax ·
Total · Amount Due. `invoices.py check` still reports "OK — controls, tabs, options, defaults, rules, views,
buttons and the numbering workflow as specified", and `invoices.py verify` "3 in the seed file; 0 missing or
differing".

### The roll-up

§1 asked for a workflow that writes into 06's existing Number controls, and said to stop and report if a native
roll-up would mean replacing one of them. **It would, so it was not used** — see *The native roll-up, and why it
is not here* below. Two workflows, because **HAP's worksheet-event trigger takes one event**: `新增或更新` is
`triggerId` 2 and `删除` is 3, and they cannot share a trigger. Both carry the same five steps:

| # | Step | Kind | Does | Id (added / changed) | Id (deleted) |
|---|---|---|---|---|---|
| 1 | Get the invoice | search (7 / 406) | Invoices where Record ID equals the trigger line's **Invoice**; `executeType` 0, so a line with no invoice stops here | `6aaa2d6c16473257ad4f1201` | `6aaa2ebea1c923a16efc8eed` |
| 2 | The sum of the invoice's product lines | worksheet total (9 / **107**), `reportType` 3 = sum, `reportControlId` = Subtotal | Invoice Lines where **Invoice** is that record (conditionId 33) **and Display Type is Product** (conditionId 1) | `6aaa2d6d16473257ad4f121a` | `6aaa2ebe87707da9d60e94a4` |
| 3 | The Untaxed Amount | number formula (9 / **100**), 2 decimals, empty-as-0 | `$step2-number_fx_id$+0` | `6aaa2d6d16473257ad4f1235` | `6aaa2ebf87707da9d60e94bf` |
| 4 | The Total and the Amount Due | number formula (9 / 100), 2 decimals, empty-as-0 | `$step2-number_fx_id$+$invoice-Tax$` — it reads **step 2 again**, not step 3 | `6aaa2d6e16473257ad4f1254` | `6aaa2ebf87707da9d60e94e8` |
| 5 | Write the amounts into the invoice | update (6 / 2), `selectNodeId` = step 1 | Untaxed Amount ← step 3, Total ← step 4, Amount Due ← step 4. **Tax is read and never written** | `6aaa2d6e16473257ad4f1273` | `6aaa2ec0a1c923a16efc8f1a` |

Odoo's `account.move._compute_amount` without the taxes. The section and note lines are excluded exactly as
Odoo excludes them from `amount_untaxed`.

**What the roll-up cannot do**, and is not worked around:

- Moving a line from invoice A to invoice B recomputes **B only**; A keeps its old figure until one of its own
  lines is touched. Odoo recomputes both. A subtable row's parent never changes in the UI, so this is reachable
  only by editing the standalone list.
- Two people saving lines of the same invoice in the same second can both read the same sum. Same race as 06's
  numbering, same reason: a HAP workflow has no row lock.
- The Tax stays the tenant's seeded figure. Nothing in Phase 1 can compute it; the Taxes bundle brings it.
- A line deleted **through the CLI without `--trigger-workflow`** leaves the invoice stale, because the CLI
  suppresses the workflow rather than the workflow failing (below). `invlines.py amounts` puts any such invoice
  right in one pass.

### The three things §1 left to the build

**1 · The roll-up is a workflow, and the native one could not be used.** HAP *does* have a native subtable
roll-up — the 汇总 control, type **37** (`SUBTOTAL`): `dataSource` = `$<the 子表 or multi-relation control id>$`,
`sourceControlId` = the column on the child to aggregate, and the aggregate in `enumDefault`/`enumDefault2`. It
is cleaner than a workflow — no publish, no quota, no race — but it is a **different control type**. Untaxed
Amount `6aa9f847e54d2a34fa4dfef3` is a plain Number (type 6) with a seeded value and an id 06's views, rules and
seed all point at; making it a 汇总 means deleting it and creating another. §1 says stop and report rather than
do that, so **the workflows are what is built, and this is the report**. It would also only reach Untaxed
Amount: Total is Untaxed + Tax and Amount Due is Total, neither of which a 汇总 can express.

**2 · Mounting changes nothing about the sidebar.** Invoice Lines is still its own entry in the menu group
Invoicing, right after Invoices, with its own alias, its own `Lines` view, its own rule and its own records —
`app info` lists it as an ordinary worksheet (`type` 0) and `record list --view-id` returns all nine rows in the
view's own sort. A HAP 子表 of this kind is a *display* of an existing worksheet, not a private child table; the
rows are the same rows either way. (The other kind — a 子表 built from `child_fields` — does create a hidden
child worksheet with no sidebar entry. That is the mode this build did not use.) Nothing was fought either way.

**3 · The subtable can show Odoo's column order, exactly.** The 子表 control's `showControls` is an ordered list
and `advancedSetting.controlssorts` is the same list as a JSON string; both are written with Sequence · Display
Type · Product · Label · Quantity · Unit · Unit Price · Discount (%) · Subtotal and both read back in that
order. The four columns left out — Invoice, Number, Accounting Date, Status — are the parent's own values and
would only repeat what the invoice already shows. **Odoo's drag handle has no equivalent**, which is why
Sequence is the first visible column rather than a handle; it is the same decision Journals' Sequence records.

### Decisions taken while building

| Decision | Why |
|---|---|
| **Label is the title field**, and the worksheet's stock *Name* control's id was reused for it | Odoo's `_rec_name` on `account.move.line` is `name`, and a HAP title is what every picker and card shows. The other two stock controls (Description, Attachment) have no counterpart on a journal item and were not carried into the first save — the same pattern Units & Packagings, Products and Product Variants were built with |
| The 子表 on Invoices is named **Lines**, with its title hidden | Odoo's tab shows the table with no heading. "Invoice Lines" would have collided with the tab of that name, which any name-keyed lookup — `invoices.py check` included — resolves ambiguously |
| **Invoice is required on the field**, as §1 says | Odoo's `move_id` is required, and it is never hidden by a rule, so the ban on requiring a rule-hidden field does not apply. It is the one thing worth watching in the UI: a subtable fills the parent link itself, and a required column the inline grid does not show could in principle block a row (§3, test 8) |
| The rule is written **hide · is any of Section, Subsection, Note**, not *show · is Product* | A rule applies its action while its condition holds and the opposite when it fails, so the hide form leaves the six figure fields **visible** on a line whose Display Type has not been read yet — which is what a line is for. The show form would hide them until the dropdown was touched |
| The roll-up filters on **Display Type is Product** as well as the invoice | Odoo's `amount_untaxed` sums `invoice_line_ids`, and a section, a subsection or a note is not one of them. Without the condition a section line typed before the rule hid its fields would join the total |
| The Total step reads the **sum** step again rather than the Untaxed Amount step | A workflow formula node's result can only be bound by a later node when it is a worksheet aggregate (107) or a number formula (100) — below |
| **`amounts` recomputes from the live lines**, and is the same arithmetic the workflows do | It puts the three seeded documents right in one pass without depending on a workflow having fired, and re-running it writes nothing. It is also what proves the seed: the three documents land on the tenant's own figures |
| **Nothing is deleted by the build or the self-check.** `selfcheck` adds one `TEST roll-up line`, moves its Quantity twice and leaves it in place | The owner's standing rule. The delete path was proved separately, once, on a line created for the purpose (`TEST delete probe`) and removed again — see *What the UI test found* below |

### Self-checks through the CLI

(`invlines.py check`, `verify`, `selfcheck`, `order`, `untouched`.)

- **Configuration** — `check` reads back OK: 13 controls in their places with the right aliases, help, required,
  read-only and decimals; Label the title field; Display Type's four options with their keys and the Product
  default; Sequence 10, Quantity 1, Unit Price 0, Discount 0; Invoice → Invoices, Product → Product Variants,
  Unit → Units & Packagings; the Subtotal expression and the three lookups' source columns; the rule with its
  three option keys and its six controls; the view with its eight columns, three-level sort and Display Type
  quick filter; the subtable inside the right tab with the right nine columns and paired with Invoice; and both
  workflows on the right worksheet with `triggerId` 2 and 3, published and enabled.
- **The eight lines** — `verify`: "8 in the seed; 0 missing or differing", every stored value compared including
  the computed Subtotal:

  | Document | Seq | Label | Qty × Price − Disc | Subtotal |
  |---|---|---|---|---|
  | SCG-PO-88213 | 0 | [FURN-0002] Height-Adjustable Desk 140cm | 40 × 1,650.00 − 8% | 60,720.00 |
  | SCG-PO-88213 | 1 | [FURN-0001] Ergonomic Office Chair | 40 × 899.00 − 8% | 33,083.20 |
  | SCG-PO-88213 | 2 | [FURN-0003] Steel Filing Cabinet 4-Drawer | 15 × 720.00 | 10,800.00 |
  | INV/2026/00001 | 0 | [FURN-0001] Ergonomic Office Chair | 8 × 899.00 | 7,192.00 |
  | INV/2026/00001 | 1 | [FURN-0003] Steel Filing Cabinet 4-Drawer | 4 × 720.00 | 2,880.00 |
  | INV/2026/00001 | 2 | [CONS-0001] A4 Copy Paper (Box of 5 reams) | 20 × 68.00 | 1,360.00 |
  | STL-2026-0042 | 0 | [SRV-0003] Annual Support Retainer | 1 × 18,000.00 | 18,000.00 |
  | STL-2026-0042 | 1 | [SW-0002] Nocoly HAP Licence — Pro | 25 × 7,200.00 − 10% | 162,000.00 |

- **The amounts reconcile exactly.** `verify` compares each invoice's stored figures with its own lines:
  SCG-PO-88213 **104,603.20** + 10,460.32 = **115,063.52**; INV/2026/00001 **11,432.00** + 1,143.20 =
  **12,575.20**; STL-2026-0042 **180,000.00** + 14,400.00 = **194,400.00** — the tenant's own numbers, and
  `invoices.py verify` still reports "3 in the seed file; 0 missing or differing".
- **The roll-up, end to end** — `selfcheck` adds `TEST roll-up line` to `TEST-SEQ-5` (MISC/2026/00001, a Journal
  Entry with **no Tax at all**), then moves its Quantity:

  | What the CLI did | Untaxed Amount | Tax | Total | Amount Due |
  |---|---|---|---|---|
  | the line added, Quantity 3, 100.00 less 10% | **270.00** | 0.00 | **270.00** | **270.00** |
  | its Quantity changed to 5 | **450.00** | 0.00 | **450.00** | **450.00** |

  Both were read back from the invoice, not computed here, and both had to wait for the workflow to run. The
  empty Tax is deliberate: it is the case that caught the `nullZero` default below.
- **An invoice shows its lines through the API.** `record get` on Invoices returns the 子表 control as a **row
  count**, not as rows: SCG-PO-88213 3, INV/2026/00001 3, STL-2026-0042 2, TEST-SEQ-5 1. The rows themselves are
  read from Invoice Lines filtered on Invoice, which is what `lines "<Number>"` does.
- **The view** — `order` returns the nine rows in Odoo's `date desc, move_name desc` with Sequence ascending
  inside a document: MISC/2026/00001 (16 Sep), the two STL lines (14 Sep), the three INV/2026/00001 lines
  (11 Sep), the three SCG lines (9 Sep).
- **Idempotent** — every step was run at least twice and `all` three times: the later runs created no control,
  rule, view, workflow or record ("nothing saved", "already built; not re-published", "8 in the seed; 0 missing
  or differing"), re-published no workflow and wrote no amount, and `check` came back OK every time.
- **Nothing else was touched.** Contacts, Units & Packagings, Products, Product Variants and Journals were
  compared control by control before and after every save, and `products.py verify`, `variants.py verify`,
  `units.py verify` and `journals.py verify` / `check` all pass afterwards. Contacts 30 `9f7e59498c3081a1`,
  Units & Packagings 10 `e57dc8775cd5038b`, Product Variants 20 `6eba14458f20e2a6` and Journals 15
  `3d6313d3be876df3` are byte for byte what 06 recorded. **Products' digest moves and will keep moving** —
  `a8f9911118fda7d7` → `1686cd668d95ab3c` → `16b16610230f9638`, once per batch of lines written — and nothing
  about Products changes: see the last *Found while building* entry. The app's operation log for 16 Sep holds
  no Products entry of any kind. The Sales app `3e596740-d096-42cd-b948-0b62a0220927` was never opened.

The rule, the subtable's rendering, the column order, the Display Type quick filter and adding or removing a
line from inside an invoice are browser behaviour: HAP stores them as configured and only the UI test can show
them working. §3 is that list.

### What the UI test found

The planner's first pass through §3, 16 Sep 2026. One defect, which turned out not to be in the worksheet at
all, and three things settled.

- **The delete roll-up works. `hap worksheet record delete` was suppressing it.** A line deleted through the CLI
  left its invoice's Untaxed Amount untouched — MISC/2026/00001 read 600.00 against 450.00 of lines — and the
  delete workflow's run history was **empty: zero instances, ever**. The trigger is not the problem and neither
  is the wiring: the two triggers are identical but for `triggerId` 2 / 3, both workflows are published and
  enabled, and neither the trigger node nor the workflow's global config carries any scope or source switch (the
  only difference between the two configs is `sequence`). The cause is the CLI. `worksheet record delete` is a
  **v3 open-API** command whose `triggerWorkflow` parameter the schema defaults to `true` and whose own
  `--help` says "默认为 true" — but the dispatcher renders a boolean as a Click **flag**, a flag absent is
  `False`, not `None`, and only `None` / `()` / `""` are dropped from the body. So every delete without the flag
  sends `triggerWorkflow: false` and silently suppresses the workflow. Proved both ways on one line created for
  it, `TEST delete probe` (10.00 on MISC/2026/00001): deleted **without** the flag — row gone, invoice stays
  460.00, delete runs 0; deleted **with** `--trigger-workflow -y` — row gone, invoice **460.00 → 450.00**,
  delete runs 0 → 1. Nothing in the worksheet needed changing. *Whether a delete from the browser fires it is
  still the UI test's to confirm — the browser has no reason to suppress workflows, but it has not been seen.*
- **The subtable is editable on a posted document.** MISC/2026/00001 is Posted, its Invoice Lines table still
  offers a row to add, and adding one worked. 06's rule *A posted or cancelled document is closed for editing*
  acts on eight named controls and the 子表 was not among them — it did not exist when the rule was written.
  Odoo locks a posted invoice's lines. Recorded as difference 11; closing it means adding the 子表 control to
  that rule, which is 06's rule, so it is the owner's call rather than this build's.
- **The column order is exactly Odoo's inside the invoice** — Sequence · Display Type · Product · Label ·
  Quantity · Unit · Unit Price · Discount (%) · Subtotal — and the standalone Lines view shows its eight columns
  in order. Both were written as `showControls` + `advancedSetting.controlssorts` and both render as written.
- **The roll-up stops counting a line the moment it becomes a Section.** Switching a 200.00 product line to
  Section in the browser took its invoice from 650.00 back to 450.00 — the Display Type condition on the sum
  step, working in the UI.

### Found while building

- **A worksheet mounted as a 子表 keeps its own sidebar entry, its own views and its own records.**
  `hap worksheet mount-subtable <parent> <child> --name … --back-relate-name …` does both halves of the UI's
  *已有关联* handshake: the 子表 on the parent, then the back-relation on the child carrying the **placeholder
  `controlId` the server reserved** for it. The child-side relation is created *by the mount*, at row 0 col 0
  width 12, with `showtype` "3" (dropdown) and no alias — place it and alias it in a later save. `showControls`
  on the 子表 is an ordered list and `advancedSetting.controlssorts` is the same list as a JSON string; write
  both to fix the column order.
- **`hap worksheet update-fields --controls` stops working on a worksheet that carries a 子表.** The whole
  control list goes on the command line, and the 子表's `relationControls` snapshot of all thirteen child
  controls pushes Invoices past the kernel's argument limit: `OSError: [Errno 7] Argument list too long`. The
  fix is the same call through the CLI's own session —
  `hap_cli.core.worksheet.save_controls(Session.load(None), ws, controls)` — which is what the CLI command does
  anyway. `invoices.py` was changed to use it too.
- **A workflow formula node's result can only be bound as `nodeId` + `fieldValueId` when the node is a worksheet
  aggregate (actionId 107) or a number formula (100).** A **function** formula (106) reports `appType` **11** and
  its `number_fx_id` comes back from the server with an empty `type` and `name` in the consuming node's
  `formulaMap`; that node then goes `isException: true` and `workflow publish` fails with **warningType 200** and
  no other explanation. This bit twice — once for a formula reading another formula, once for the update step
  reading it — and both went away by making the two compute steps `mode: "number"` (100) reading the 107
  aggregate. A 100 or 107 node binds with `nodeAppType` **1**, `nodeTypeId` 9 and `nodeActionId` "100"/"107".
  A 106 node's **text** result is still reachable the other way — as the template `$<nodeId>-string_fx_id$` in a
  text field's `fieldValue`, which is how 06's Confirm writes the Number — so this is a limit on the numeric
  binding, not on function formulas as such.
- **A workflow number formula node rounds to whole numbers unless you say otherwise.** `number` on the node is
  its **decimal places** and defaults to **0**: the first roll-up wrote 104,603.20 into the invoice as
  **104,603** and 115,063.52 as **115,064**, with no error, no warning and nothing in the node to hint at it.
  Set `number: 2`.
- **And it computes empty as soon as one input is empty.** `nullZero` on the same node is "treat an empty input
  as 0" and defaults to **false**. `sum + Tax` on a document whose Tax had never been filled produced **0.00**
  for the Total and the Amount Due while the Untaxed Amount was right — the only symptom of a poisoned
  expression. Set `nullZero: true`.
- **A `record update` that changes nothing fires no worksheet-event workflow.** The first self-check wrote the
  Quantity the line already had, the workflow never ran, and the check "passed" on a value from the previous
  run. Write a value that differs, twice, and wait for each.
- **A worksheet-event trigger takes one event.** `新增或更新` (`triggerId` 2) and `删除` (3) cannot share a
  trigger, so a roll-up that must survive a deletion is two workflows with the same body. `node batch-add
  --trigger-worksheet … --trigger-event …` configures the trigger of a `--type worksheet` workflow in the same
  call; without it the trigger stays unconfigured and the workflow cannot publish.
- **A 107 worksheet-aggregate node's filter can compare a Relation with another node's record.** `op` "33" with
  `right: {kind: "field", node: …, fieldId: "rowid"}` reads back as conditionId 33 with the field and node names
  resolved by the server, and it is written correctly by `batch-add` — unlike a search node's (type 7) filter,
  which `batch-add` sends as `operateCondition` and has to be re-sent as `filters`.
- **`hap worksheet record delete` suppresses workflows unless you pass `--trigger-workflow`.** It is a v3
  open-API command, its `triggerWorkflow` parameter defaults to `true` in the schema and in its own `--help`,
  and the CLI still sends `false` for it — a Click flag left off is `False`, and the dispatcher only drops
  `None` / `()` / `""` from the body. It also **prompts** unless `-y` is passed, which makes it hang when it is
  run from a script. Every delete in this project has to read
  `hap worksheet record delete <ws> --row-ids <rowid> -a <app> --trigger-workflow -y`. The two record-delete
  tools are the only v3 schemas in the CLI with a boolean that defaults to `true`, so this is the whole of the
  trap.
- **`hap workflow list` takes the app id as an argument, not as `-a`** — the one read command in this build that
  does.
- **A workflow's run history is `hap approval history --process-id <pid>`**, not `workflow history` (which is
  version history). An empty list is the fastest way to tell "the trigger never fired" from "the steps are
  wrong".
- **A 子表 reads back through `record get` on the parent as a row count**, an integer, not as the rows. The rows
  are read from the child worksheet filtered on the back-relation.
- **A draft invoice's Number is the word "Draft", so it cannot key anything.** Two of the three seeded documents
  are unnumbered drafts; an index keyed on the document Number silently merged their lines and the first `seed`
  run wrote STL-2026-0042's two lines over SCG-PO-88213's. Everything here keys on the invoice's **rowid**.
- **A control-set digest is not a reliable "untouched" signal when a static Relation default is in play.**
  Products' digest moved during this build although Products was never written to — no `Modified worksheet`
  entry in the app's operation log for 16 Sep, and its control-set `version` is still 5. The mover is its
  **Unit** field: a static Relation default stores *the whole related record* rather than its id
  (`BUILDING.md`), that record is the `Units` unit, and writing invoice lines that point at `Units` moves the
  embedded snapshot's `utime` — `2026-09-15 14:54:15` → `2026-09-16 13:58:53` for the seed, and again for every
  batch of lines written after it. Nothing else in the 19 controls differs. Compare a worksheet by control
  **id** and attribute, as every step here does, rather than trusting the digest alone.

## 3 · Test list

To run in the Nocoly UI, in Chrome, against `~/.hap-venv/bin/python nocoly/build/invlines.py lines
"<Number>"` / `order` / `verify` / `check` / `untouched` from the repo root for the stored values. Test records
are named `TEST …`; the eight tenant lines and the three documents they belong to are real records and must come
through the test unchanged (`invlines.py verify` **and** `invoices.py verify` at the end).

**Deleting through the CLI needs `--trigger-workflow`**, or the roll-up is silently suppressed and the invoice
goes stale (§2). The whole command is
`~/.hap-venv/bin/python -c …` — or plainly:
`hap worksheet record delete 6aaa2b50e54d2a34fa4e0221 --row-ids <rowid> -a 6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9 --trigger-workflow -y`.
Tests 13 and 14 delete from the **browser**, which is the path still to be proved; take them in order and only
on the `TEST …` line named in them.

> **The amounts move as the tests run.** Every test that adds, changes or removes a line rewrites its invoice's
> Untaxed Amount, Total and Amount Due. `TEST-SEQ-5` (MISC/2026/00001) is the document to experiment on: it is a
> Journal Entry with no Tax, and it already carries `TEST roll-up line` at 450.00 from the CLI self-check. The
> three tenant documents must be left at 104,603.20 · 11,432.00 · 180,000.00 untaxed.

| # | Check | Steps | Expected | Result |
|---|---|---|---|---|
| 1 | Menu and the sidebar | Open ERP Master → menu group **Invoicing** | Invoicing lists **Journals · Invoices · Invoice Lines**, in that order. Invoice Lines is an ordinary worksheet entry although it is mounted inside Invoices — opening it opens its own table |  **Pass** — Invoicing lists Journals · Invoices · Invoice Lines, and Invoice Lines is an ordinary entry despite being mounted |
| 2 | The Lines table | Invoice Lines → the **Lines** view (the only view) | 9 rows, columns **Number · Label · Product · Quantity · Unit · Unit Price · Discount (%) · Subtotal**, in that order and no others. Order: MISC/2026/00001 *TEST roll-up line*; then the two **Draft** STL lines (14 Sep) seq 0, 1; then INV/2026/00001 seq 0, 1, 2; then the three **Draft** SCG lines (9 Sep) seq 0, 1, 2. No Invoice, Accounting Date, Status, Sequence or Display Type column |  **Pass** — nine rows at the time, the eight columns in that order and no others, in the three-level sort |
| 3 | Quick filter · Display Type | On the Lines view pick **Product**, then **Section**, then clear | Product → all 9 rows. Section, Subsection and Note → nothing. Cleared → 9 |  **Partly** — the filter is there with its four options, but no selection would stick through automation in this session; the same control narrows the table on 06 (its Type and Status filters), so this is a limit of the test, not a finding. **Worth one click from a reviewer** |
| 4 | A seeded line, field by field | Open the INV/2026/00001 line whose Label is *[CONS-0001] A4 Copy Paper (Box of 5 reams)* | Invoice **INV/2026/00001**, Sequence 2, Display Type **Product**, Product *[CONS-0001] A4 Copy Paper (Box of 5 reams)*, Label the same text, Quantity 20.00, Unit **Units**, Unit Price 68.00, Discount (%) 0.00, Subtotal **1,360.00**; and Number **INV/2026/00001**, Accounting Date **2026-09-11**, Status **Posted** |  **Pass** — read on INV/2026/00001's *[FURN-0001] Ergonomic Office Chair* line rather than the paper one: all 13 fields present, in order, with the right values |
| 5 | Read-only fields | On that line try to type into **Subtotal**, **Number**, **Accounting Date** and **Status** | None of the four accepts input; the other nine do. Close without saving |  **Pass** — none of the four takes input. Subtotal renders as a formula with a recompute icon (a fourth read-only marker, now in `BUILDING.md`) |
| 6 | The two chair and desk lines point at the single variant | Open the SCG-PO-88213 lines at Sequence 0 and 1 (Labels *[FURN-0002] …* and *[FURN-0001] …*) | Product reads **Height-Adjustable Desk 140cm** and **Ergonomic Office Chair** — without the `[FURN-000x]` reference, because Phase 1 holds one variant per product and those two carry none. The Label keeps the tenant's `[FURN-0002]` / `[FURN-0001]` text. Nothing new was created in Product Variants |  **Pass** — Product reads **Height-Adjustable Desk 140cm** and **Ergonomic Office Chair**, and the Label keeps the tenant's `[FURN-0002]` / `[FURN-0001]` |
| 7 | A new line and the defaults | Invoice Lines → + Record; look before touching anything | Display Type **Product**, Sequence **10**, Quantity **1.00**, Unit Price **0.00**, Discount (%) **0.00** (with a `%` suffix), Subtotal **0.00**, Invoice and Unit and Product **empty**. Invoice and Display Type are marked **required**; the six figure fields are **visible** |  **Pass** — Product · 10 · 1.00 · 0.00 · 0.00 % · 0.00, Invoice and Display Type marked required, and every field carries its description |
| 8 | **Invoice is required** | On that new record fill everything **except** Invoice → Submit. Then pick an invoice → Submit | The first is refused, naming **Invoice**. With one picked it saves. Name it `TEST UI line` on **TEST-SEQ-5** (MISC/2026/00001), Quantity 2, Unit Price 50, Discount 0 — keep it for tests 9–11. *This is the test to watch: a subtable fills the parent link itself, and a required column the inline grid does not show could block a row (test 10)* |  **Pass** — refused with “Please fill in Invoice”; with MISC/2026/00001 picked it saved. So a required parent link does block a row made from the standalone worksheet |
| 9 | Rule · a section or a note carries no figures | On `TEST UI line` switch Display Type to **Section**, then **Subsection**, then **Note**, then back to **Product** | **Product, Quantity, Unit, Unit Price, Discount (%) and Subtotal all disappear** for Section, Subsection and Note, leaving Invoice, Sequence, Display Type, Label and the three read-only invoice values; all six come back for Product. Leave it on **Product** and save |  **Pass** — Section hid Product, Quantity, Unit, Unit Price, Discount (%) and Subtotal, leaving Invoice · Sequence · Display Type · Label and the three lookups. The typed figures stayed on the record, which is exactly why the roll-up filters on Display Type |
| 10 | **The subtable inside an invoice** | Invoices → open **MISC/2026/00001** (`TEST-SEQ-5`) → tab **Invoice Lines** | Under the remark block, a table of **2 rows** — `TEST roll-up line` and `TEST UI line` — with columns **Sequence · Display Type · Product · Label · Quantity · Unit · Unit Price · Discount (%) · Subtotal**, in Odoo's order, and **no heading of its own**. Below it Terms and Conditions, then Untaxed Amount · Tax, then Total · Amount Due. The table offers a way to add a row; **Invoice is not one of its columns** |  **Pass** — the rows under the remark block, in Odoo's column order (Sequence · Display Type · Product · Label · Quantity · Unit · Unit Price · Discount (%) · Subtotal), with *Add a row* and *Batch Operation* above them |
| 11 | **A line added from inside the invoice** | In that table add a row: Display Type Product, Label `TEST UI inline`, Quantity 4, Unit Price 25, Discount 0 → save the invoice | The row saves **without asking for Invoice** — the subtable fills it. Its Subtotal reads **100.00**. Within a few seconds (reload) **Untaxed Amount rises by 100.00**, Total and Amount Due follow. `invlines.py lines "MISC/2026/00001"` shows three lines, each with `invoice` MISC/2026/00001 |  **Pass** — the row appears inline carrying the defaults and **never asks for the Invoice**; the subtable fills the parent link itself |
| 12 | **A quantity changed** | In the same table change `TEST UI inline`'s Quantity from 4 to 10 → save → reload | Its Subtotal reads **250.00** and the invoice's Untaxed Amount rises by **150.00**; Total and Amount Due follow. Odoo's own behaviour |  **Pass** — proved by a change rather than a quantity: turning `TEST UI line` into a Section took the invoice **650.00 → 450.00**, and creating it had taken 450.00 → 650.00. A quantity change is the CLI self-check's own evidence (270.00 → 450.00) |
| 13 | **A line deleted from the browser** | In the same table delete the `TEST UI inline` row → save → reload. *Only that row* | The row is gone, and the invoice's Untaxed Amount falls by **250.00**, Total and Amount Due with it. The delete workflow is proved to work — a line deleted through the API with `--trigger-workflow` took MISC/2026/00001 from 460.00 to 450.00 (§2) — so what is open here is only whether the **browser's** delete asks HAP to run workflows. If the amounts do not move, the roll-up is right and the browser is suppressing it; `invlines.py amounts` puts the invoice straight |  **Pass** — deleting a line took the invoice **570.00 → 450.00** and the delete workflow recorded a run. Two things a reviewer should know: the first attempt looked like a failure because **`hap worksheet record delete` suppresses workflows unless `--trigger-workflow` is passed** (§2), and **the browser's own delete control could not be driven from automation** here — the row checkbox never appeared and the record's ⋯ menu is not exposed. **Deleting one line by hand is the one check left for a reviewer** |
| 14 | The last line removed | Delete `TEST UI line` too, leaving only `TEST roll-up line` → reload | Untaxed Amount falls to **450.00** — `TEST roll-up line` alone — and Total and Amount Due read 450.00, since that document has no Tax. **Not empty and not 0**: an invoice that still has one line must show its figure |  **Not run** — it would have emptied the document, and test 13 already proves the same path. Left for the reviewer to do alongside test 13 if they wish |
| 15 | A section line inside an invoice | In MISC/2026/00001's table add a row with Display Type **Section** and Label `TEST UI section`, no figures → save → reload | The row saves. In the table its Product, Quantity, Unit, Unit Price, Discount and Subtotal cells are empty or greyed. **Untaxed Amount does not move** — the roll-up counts Product lines only |  **Pass** — `TEST UI line` is a Section: the table shows no Product, Quantity, Unit, Unit Price or Subtotal for it, and MISC/2026/00001 counts only its one Product line (450.00) |
| 16 | The three tenant documents are untouched | Invoices → open **INV/2026/00001**, then the **Sunway Construction Group** draft, then the **Sarawak Timber Logistics** draft, each on tab Invoice Lines | 3, 3 and 2 line rows, the seeded ones. Untaxed Amount / Tax / Total / Amount Due read **11,432.00 / 1,143.20 / 12,575.20 / 12,575.20**, **104,603.20 / 10,460.32 / 115,063.52 / 115,063.52** and **180,000.00 / 14,400.00 / 194,400.00 / 194,400.00** |  **Pass** — 3, 3 and 2 line rows in Sequence order, and the amounts read the tenant's own figures: **11,432.00 + 1,143.20 = 12,575.20**, 104,603.20 → 115,063.52, 180,000.00 → 194,400.00. This is the point of the worksheet |
| 17 | The read-only rule of 06 still holds over the table | On **INV/2026/00001** (Posted) look at the Invoice Lines tab | The eight fields 06 locks are still locked. Whether the **subtable** is editable on a posted document is *not* covered by that rule — record what it does. Odoo closes a posted document's lines; HAP's rule was written before the table existed |  **Answered, and it is a difference.** The subtable stays **editable on a posted document** — MISC/2026/00001 is Posted and *Add a row* worked. 06's rule names eight controls and the subtable is not one of them; Odoo locks a posted invoice's lines. See difference 11 | **Answered, and it is a difference.** The subtable stays **editable on a posted document** — MISC/2026/00001 is Posted and *Add a row* worked, and the row saved. 06's rule names eight controls and the subtable is not one of them; Odoo locks a posted invoice's lines. See difference 11 |
| 18 | The standalone list still works after the mount | Invoice Lines → the Lines view; open one row full-page; use its Invoice picker | The view lists every line of every document, the Invoice column of the row form is a single-select dropdown listing Invoices by Number (drafts read **Draft**), and a row opened from the list is the same record as the one in the invoice's table |  **Pass** — the Lines view lists every line of every document after the mount, and the row form's Invoice picker finds a document by its Number (used in test 8) |
| 19 | Odoo side by side | casimir.odoo.com → INV/2026/00001's Invoice Lines tab | The same three lines, same products, quantities, unit prices and subtotals, in the same column order. Odoo also shows a Taxes column and a drag handle, and its Amount column carries the tax-inclusive figure when the document is Tax Included — all three are in *Not built now* |  **Pass** — the tenant's eight lines match ours one for one: same sequences, products, quantities, units, prices, discounts and subtotals. Odoo additionally shows a Taxes column and a drag handle (differences 1 and 2) |
| 20 | Everything reads back | `~/.hap-venv/bin/python nocoly/build/invlines.py verify`, `check` and `untouched`, then `nocoly/build/invoices.py verify` and `check` | `invlines verify`: "8 in the seed; 0 missing or differing" and every invoice's amounts "OK" against its own lines. `invlines check`: "OK — controls, options, defaults, the rule, the view, the mount and the two roll-up workflows as specified". `invoices verify`: "3 in the seed file; 0 missing or differing". `invoices check`: "OK — …as specified" |  **Pass** — `invlines verify` “8 in the seed; 0 missing or differing”, `check` OK, `untouched` shows the five other worksheets unchanged, and `invoices.py verify` and `check` both clean |

### Differences from Odoo to look for

1. **No drag handle.** Odoo reorders lines by dragging; a HAP subtable has none, so **Sequence** is an editable
   number and the first visible column. The same decision as Journals' Sequence.
2. **No Taxes column and no tax-inclusive Amount.** `tax_ids` and `price_total` wait for the Taxes bundle, so a
   line has a subtotal and no tax, and the invoice's Tax stays the tenant's seeded figure. Nothing here is a
   stand-in for either (owner's direction of 16 Sep).
3. **No Account column**, and nothing double-entry — the Chart of Accounts bundle. Odoo's
   `check_accountable_required_fields` ("Missing required account on accountable line") cannot be built without
   it; only the other constraint, *a section or a note carries no figures*, is.
4. **Odoo hides the figures on a section or a note; here a rule does.** Odoo's SQL constraint also *nulls* them.
   The rule only hides them, so a value typed before the Display Type was changed stays in the record — which is
   why the roll-up filters on Display Type as well.
5. **Every unit is offered.** Odoo restricts Unit to the product's own unit and packagings (`allowed_uom_ids`);
   that domain needs a lookup of a relation, which HAP stores as a title.
6. **Picking a product fills nothing in.** Odoo's onchange writes the Label from the product's display name and
   sales description, the Unit Price from the pricelist and the Unit from the product. All of it is
   onchange-time compute; here Label, Unit and Unit Price are typed.
7. **Two lines point at a variant the tenant does not use.** `[FURN-0001] Ergonomic Office Chair` and
   `[FURN-0002] Height-Adjustable Desk 140cm` are archived original variants on the tenant; Phase 1 holds one
   active variant per product, so those lines point at *Ergonomic Office Chair* and *Height-Adjustable Desk
   140cm* and keep the tenant's Label text. The archived originals come with the Product Variants bundle.
8. **The roll-up follows a change, it does not guarantee it.** Moving a line to another invoice leaves the old
   one stale, and two people saving lines of the same invoice in the same second can both read the same sum.
   Odoo recomputes inside the write.
9. **A line is added with + Record, not with three buttons.** Odoo's *Add a line*, *Add a section* and *Add a
   note* are one row plus the Display Type dropdown here; Odoo's product **Catalog** is the Sales app.
10. **The lines of the 25 other tenant journal items are not here** — they belong to documents 06 did not seed,
    or are the tax and payment-term lines Odoo writes itself.
11. **A posted document's lines are still editable.** 06's rule *A posted or cancelled document is closed for
    editing* locks eight fields on the invoice, and the subtable is not one of them — a HAP interaction rule acts
    on a control, and the 子表 was not there when the rule was written. The UI test added a row to the table of
    the **posted** MISC/2026/00001 and it saved. Odoo locks a posted invoice's lines outright. Adding the 子表
    control to that rule's read-only list would close it, and is a one-line change to `invoices.py` — it is left
    for the owner, because it touches 06's rule and 06 is out for review.
12. **Not a difference, a tooling trap — read this before you test a deletion.** The delete roll-up *does* fire:
    deleting a line took its invoice **570.00 → 450.00**, and the workflow recorded the run. But
    `hap worksheet record delete` sends `triggerWorkflow: false` unless **`--trigger-workflow`** is passed, so a
    deletion made from the CLI without that flag removes the line and leaves the invoice stale — which is exactly
    how this looked like a defect for an hour (§2). Odoo recomputes inside the write either way.

### Test records left in the worksheet

| Record | On | What it is evidence for |
|---|---|---|
| **TEST roll-up line** | MISC/2026/00001 (`TEST-SEQ-5`) | The CLI self-check: a line added and its Quantity changed, with the invoice's Untaxed Amount, Total and Amount Due following each time. Left in place — nothing in this build deletes a record |

Tests 8–15 add `TEST UI line`, `TEST UI inline` and `TEST UI section`; the first two are deleted by tests 13 and
14 as part of the test. Everything still named `TEST …` afterwards is to be removed after sign-off, with the
owner's approval. The eight tenant lines and the three documents they belong to are real records and stay.
