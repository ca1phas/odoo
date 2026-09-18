# 13 · Taxes

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Invoicing** |
| Worksheet | Taxes |
| Odoo model | `account.tax` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: fields, the raw arch of every view *and of the three modules that extend the form*, the actions and their menus, the access list, all 35 taxes, all 10 tax groups, all 36 repartition lines, the company's tax settings, the taxes of all 14 products, the `tax_ids` of every account and of all 31 invoice lines — extracted read-only to `nocoly/reference/odoo-19.4/account.tax.md`; the records themselves are `nocoly/data/casimir-taxes.json`. Behaviour the tenant cannot show is read from the Odoo 19.0 source in this repo: `addons/account/models/account_tax.py`, `account_tax_views.xml`, `account_account.py`, `account_move_line.py`, `product.py`, `addons/account/security/ir.model.access.csv`, `account_security.xml` |
| Phase | 1 — **bundle 6 of 6, the last** (Product Categories · Chart of Accounts · Payment Terms · Countries · States · **Taxes**) |
| Status | §1 written 18 Sep 2026 · built and self-checked 18 Sep 2026 (`nocoly/build/taxes.py`) · **UI-tested 18 Sep 2026: 19 pass, 3 fixed during the test, 1 not isolated** (§3) — the three fixes were the five Dropdowns' display style, the missing **Taxes** column inside an invoice, and 06's now-false remark block · ready for review |

The figure five worksheets have been deferring. Odoo's taxes are what turn a line's subtotal into a total: a line
carries some taxes, each tax a percentage, and the document's Tax is the sum of what they add. This tenant ships
Malaysia's SST — **35 taxes, ten of them active, and only two ever used** — and every one of the ten is a plain
percentage, so the arithmetic Phase 1 has to reproduce is `subtotal × rate ÷ 100`, rounded per line.

This bundle adds the worksheet, seeds all 35, and then **goes back to four worksheets that left a hole for it**:
Products gains Sales Taxes and Purchase Taxes, Chart of Accounts gains Default Taxes, Invoice Lines gains Taxes
and Total, and **Invoices' Tax stops being a seeded figure** — the last of 06's four amounts to become real.

## 1 · Requirements

### Fields

Labels are Odoo 19.4's; aliases are Odoo field names on `account.tax`.

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Tax Name | `name` | Text · **title field** | yes | — | **Not *No duplicates*.** Odoo's constraint is the five-way (company, name, type, scope, country) — *0% NA* is both a Sales tax and a Purchase tax, and **eight** of the 27 distinct names are shared by two records apiece, sixteen records in all. See *Rules* |
| 2 | Tax Type | `type_tax_use` | Dropdown | yes | **Sales** | Sales · Purchases · None. Odoo's help as the description: "Determines where the tax is selectable. Note: 'None' means a tax can't be used by itself, however it can still be used in a group." |
| 3 | Tax Scope | `tax_scope` | Dropdown | — | — | Goods · Services. **Empty means both** — five of the 35 leave it empty |
| 4 | Tax Computation | `amount_type` | Dropdown | yes | **Percentage** | Group of Taxes · Fixed · Percentage · Percentage Tax Included · **Custom Formula**. The last is `account_tax_python`, installed on this tenant; three archived taxes use it |
| 5 | Amount | `amount` | Number, **4 decimals** | yes | 0 | Odoo's `float(16, 4)`: 10% G reads **10.0000** on the form, with a `%` after it unless the computation is Fixed. Platform thousands separator (`thousandth` "0"), as Odoo formats a float |
| 6 | Formula | `formula` | Text | — | `price_unit * 0.10` | `account_tax_python`. Odoo shows it only when Tax Computation is Custom Formula and requires it there — a rule, below. Every tax carries the module default whether it reads it or not |
| 7 | Description | `description` | Text | — | — | **Odoo's is Html; ours is Text.** Every one of the 35 holds a single short plain line inside one `<div>` — *SST 10%*, *Not Applicable* — and it is a list column, where a rich-text cell is unreadable. Recorded as a difference |
| 8 | Label on Invoices | `invoice_label` | Text | — | — | What prints on the document. Odoo falls back to the name when it is empty (`tax_label`); **seven** of the 35 are empty |
| 9 | Tax Group | `tax_group_id` | Dropdown | yes, unless Group of Taxes | — | **Odoo's is a relation to `account.tax.group`.** Built as a Dropdown of the tenant's ten group names — see *Not built now* |
| 10 | Country | `country_id` | **Relation → Countries** (single, dropdown) | yes | **Malaysia** | One-way, as Products' Unit is. All 35 are Malaysia. Odoo's help as the description: "The country for which this tax is applicable." |
| 11 | Included in Price | `price_include_override` | Dropdown | — | — (placeholder *Default*) | Tax Included · Tax Excluded. Empty means the company's own setting, which on this tenant is **Tax Excluded**; no tax overrides it |
| 12 | Affect Base of Subsequent Taxes | `include_base_amount` | Checkbox | — | unchecked | Odoo's help as the description |
| 13 | Base Affected by Previous Taxes | `is_base_affected` | Checkbox | — | **checked** | Odoo's help as the description. On Odoo's form it sits behind `base.group_no_one`; here it is simply visible — the app has no developer mode |
| 14 | Active | `active` | Checkbox | — | **checked** | **25 of the 35 are archived.** Odoo's help: "Set active to false to hide the tax without removing it." |
| 15 | Sequence | `sequence` | Number, 0 decimals | yes | 1 | `_order = 'sequence,id'`. All 35 are 1, so the list reads in creation order — Payment Terms' arrangement exactly |
| 16 | Legal Notes | `invoice_legal_notes` | RichText | — | — | Its own group at the foot of Odoo's Advanced Options. Empty on all 35 |
| — | Duplicate name | — | Checkbox, read-only, hidden on create | — | — | **Not an Odoo field.** Ticked by workflow **G** when another tax already holds this tax's key — what a person sees in place of Odoo's refusal. The same control States gained on 18 Sep 2026 (`12-states.md` §1 › Rules) |
| — | Tax key | — | **Text**, hidden and read-only, **No duplicates** | — | — | `<country code>\|<tax type>\|<tax scope>\|<tax name>` — *MY\|sale\|consu\|10% G*. Written by **G**, never typed |

**No Amount for a group.** Odoo hides the Amount field whenever the computation is not Fixed, Percentage or
Percentage Tax Included — so for Group of Taxes **and** for Custom Formula. A rule, below.

**No reverse field on any of the four worksheets that point here.** Odoo's tax form lists neither the products
nor the accounts nor the lines that use it; it has only the computed `is_used` flag, which is *Not built now*.
Every relation this bundle adds is therefore **one-way**, as Products' Unit is.

### Form layout

Odoo 19.4's form is a header group plus a two-page notebook. **The 19.0 source in this repo is out of date here**
— 19.4 moved Description up into the header, moved Tax Scope down into Advanced Options and moved Active down
beside it — so this layout follows the tenant's own `arch_db`, not the source
(`reference/odoo-19.4/account.tax.md` › *Views*).

| Odoo 19.4 (casimir) | Nocoly |
|---|---|
| Header left: Tax Name · Tax Computation · *Formula* · *Malaysian Tax Type* · Amount % · Description | Tax Name \| Tax Type · Tax Computation \| Amount · Formula \| Sequence · Description \| Label on Invoices |
| Header right: Tax Type · Fiscal Position · Replaces | Fiscal Position and Replaces — (*Not built now*) |
| Tab *Definition*: Distribution for Invoices · Distribution for Refunds, or Children Taxes | — (*Not built now*) — which empties the tab, so there is none |
| Tab *Advanced Options* left: Label on Invoices · Tax Scope · Tax Group · *Analytic* · *Company* · Country · *Tax Category Code* | After the divider: Tax Scope \| Tax Group · Country \| Included in Price |
| Tab *Advanced Options* right: Included in Price · Affect Base of Subsequent Taxes · Base Affected by Previous Taxes · Active | Affect Base of Subsequent Taxes \| Base Affected by Previous Taxes · Active |
| Group *Legal Notes* | **Legal Notes**, full width |
| Chatter | HAP's record discussion |

| Row | Left (6) | Right (6) |
|---|---|---|
| 1 | **Tax Name** | **Tax Type** |
| 2 | **Tax Computation** | **Amount** |
| 3 | Formula | **Sequence** |
| 4 | Description | Label on Invoices |
| 5 | **Divider *Advanced Options*** (12) | |
| 6 | Tax Scope | **Tax Group** |
| 7 | **Country** | Included in Price |
| 8 | Affect Base of Subsequent Taxes | Base Affected by Previous Taxes |
| 9 | Active | Duplicate name (read-only) |
| 10 | **Legal Notes** (12) | |
| — | **Tax key** — hidden and read-only, off the grid | |

**One divider, no tab.** Odoo's *Definition* page holds only the distribution lists, none of which is built, so
it would be empty; its *Advanced Options* page then stands alone, and a single tab is worse than none — the same
call Chart of Accounts made (`09-chart-of-accounts.md` § Form layout). The divider keeps the boundary visible.

### Rules

**Uniqueness follows bundle 5's proved pattern, not Odoo's refusal.** Odoo's `_constrains_name` is a **five-way**
key — company, name, Tax Type, Tax Scope, Country — skipped entirely when Tax Type is *None*. HAP's *No
duplicates* is one field, and 12 measured what it does and does not do: on a **Text** control a person types into
it is real (a refusal and API `resultCode 11`); on a **function formula** it is decoration; and **a workflow's own
write ignores it** (`BUILDING.md` › *No duplicates: where it is real*). So the pair that worked for States works
here, with a four-part key instead of two:

| | What |
|---|---|
| **Tax key** | Text, hidden, **No duplicates**, read-only. `<country code>\|<tax type>\|<tax scope>\|<tax name>` — *MY\|sale\|consu\|10% G*, and *MY\|sale\|\|0% NA* where the scope is empty. Written by **G**, never typed |
| **Duplicate name** | Checkbox, read-only, on the form. Ticked by **G** when another tax already holds that key |
| **G** | *Taxes: the key and the duplicate check*. On create, and when Tax Name, Tax Type, Tax Scope or Country changes: work out the key, look for another tax that already has it, **tick Duplicate name and stop** if there is one, otherwise untick and write the key. Quiet (`triggerType` 2), self-excluding (`Record ID ≠ the trigger`, conditionId 10), ending on an abort node (type 30) exactly as States' G does |

**Taxes whose Tax Type is None are exempt**, as they are in Odoo: G writes no key for them and never marks them.
No tax on this tenant has that type, so nothing in the seed exercises it.

As on States, **HAP cannot refuse the save**: a workflow runs after it. A duplicate is created, then within a few
seconds loses its key, gains a tick and appears in the *Duplicate names* view until it is mended. That is the
ceiling and the reason the checkbox exists.

The rest of the rules are Odoo's own visibility, read off the 19.4 arch:

| # | Rule | Odoo |
|---|---|---|
| 1 | **Amount** hidden unless Tax Computation is Fixed, Percentage or Percentage Tax Included | `invisible="amount_type not in ('fixed', 'percent', 'division')"` |
| 2 | **Formula** shown, and **required**, only when Tax Computation is Custom Formula | `account_tax_python`'s `invisible="amount_type != 'code'" required="amount_type == 'code'"` |
| 3 | **Tax Group** hidden when Tax Computation is Group of Taxes, required otherwise | `invisible="amount_type == 'group'" required="amount_type != 'group'"` |
| 4 | **Included in Price**, **Affect Base of Subsequent Taxes** and **Base Affected by Previous Taxes** hidden when Tax Computation is Group of Taxes | the three `invisible="amount_type == 'group'…"` |
| 5 | **Duplicate name** read-only, and off the create form | ours; States' rule verbatim |

### Buttons

**Archive** and **Unarchive**, the house pair, each with its one-step workflow — the seventh worksheet to carry
them. `active` is a real Odoo field here and 25 of the 35 records use it.

### Views

| View | Kind | Odoo | Nocoly |
|---|---|---|---|
| **Taxes** | table — opens first | The action opens `list` with `active_test: False` **and** the *Sale or Purchase* facet, so it shows **all 35**, inactive ones drawn muted. Columns Tax Name · Description · Tax Type · Tax Scope · Label on Invoices · Active, with Replaces, Country and Company switched off | The same six columns, **all 35 rows** — Odoo's own choice, so no Active filter on the view — sorted **Sequence ascending, then created**, which is `_order = 'sequence,id'`. Quick filters **Tax Type** (any of), **Tax Scope** (any of) and **Active**, standing in for Odoo's facets |
| **Archived** | table | Odoo has no such view — its inactive taxes sit in the main list | The house's seventh Archived view: the 25 with Active unticked, same columns. Kept for the Unarchive button, not because Odoo has one |
| **Duplicate names** | table | none — Odoo's database refuses the second tax | **Ours.** The taxes Duplicate name is ticked on — nothing, unless something went in twice. Tax Name · Tax Type · Tax Scope · Country · **Duplicate name**. States' *Duplicate codes* verbatim |

### Automations

| # | Workflow | Fires when | Does |
|---|---|---|---|
| **G** | *Taxes: the key and the duplicate check* | a tax is created, or its Tax Name, Tax Type, Tax Scope or Country changes | The key-and-mark body described under *Rules*. Quiet |
| — | *Taxes: Archive* / *Taxes: Unarchive* | the buttons | The house pair |

### What this bundle changes on Products (03)

Odoo's product form carries the taxes in the right column of *General Information*: Sales Price · **Sales
Taxes** · Cost · **Purchase Taxes** · Category · Reference (`03-products.md` › Form layout, and the note in
`08-product-categories.md` that put Category there).

| | |
|---|---|
| New field **Sales Taxes** (`taxes_id`) | Relation → Taxes, **multiple**, one-way, not required. Picker filtered to **Tax Type is Sales**, which is Odoo's own `domain=[('type_tax_use','=','sale')]`. Placed after Sales Price |
| New field **Purchase Taxes** (`supplier_taxes_id`) | Relation → Taxes, **multiple**, one-way, not required. Picker filtered to **Tax Type is Purchases**. Placed after Cost |
| Values | Every one of the 14 products carries exactly one of each: the **8 goods** take *10% G* and *0% NA*, the **6 services** take *8% S* and *0% NA*. Written from `casimir-taxes.json` |
| Columns | Neither joins a table — Odoo's product list shows no tax column |

Odoo defaults both from the company (`account_sale_tax_id` 10% G, `account_purchase_tax_id` 0% NA). **No default
is built**: HAP defaults a Relation to a fixed record, and a company-level setting is not one of the six.
Recorded under *Not built now*.

### What this bundle changes on Chart of Accounts (09)

09 § *Not built now* named this as the one field the Taxes bundle must come back for.

| | |
|---|---|
| New field **Default Taxes** (`tax_ids`) | Relation → Taxes, **multiple**, one-way, not required. On the form under Type, where Odoo's *Accounting* tab puts it (Type · Default Taxes · Fiscal Category · Tags · Deferred) |
| Values | **None.** Not one of the tenant's accounts has a Default Tax, so the field is added empty and the seed writes nothing |
| Column | Stays switched off, as it is on Odoo's own list and as 09's *Chart of Accounts* view already records |

The *Taxes* stat button (`related_taxes_amount`) that 09 also listed stays out — see *Not built now*.

### What this bundle changes on Invoice Lines (07) and Invoices (06)

This is where the bundle earns its place. 07 § *Not built now* left the taxes and `price_total` here, and 06's
**Tax** has been a seeded read-only figure since 16 September.

**On Invoice Lines:**

| | |
|---|---|
| New field **Taxes** (`tax_ids`) | Relation → Taxes, **multiple**, one-way, not required. **Unfiltered** — Odoo's own context on this field is `{'active_test': False}`, so its picker offers archived taxes too, and it carries no Tax Type domain: a line takes whatever the product put there |
| New helper **Tax rate** | 汇总 (roll-up, type 37) over the **Taxes** relation, `sourceControlId` = Taxes' **Amount**, aggregate **sum**, filtered to **Tax Computation is Percentage**. Read-only; hidden. The filter is what keeps a Fixed or Custom Formula tax from adding its amount as if it were a rate |
| New field **Total** (`price_total`) | Number **formula**, 2 decimals: `Subtotal × (1 + Tax rate ÷ 100)`. Odoo's own field — the line's amount with tax — and the only new *number* on the line, so no per-line tax figure is invented that Odoo does not have |
| Column | **Total** joins the *Lines* view and the standalone list after Subtotal |
| Values | The 8 seeded lines take the tenant's taxes: SCG-PO-88213's three and INV/2026/00001's three take **10% G**, STL-2026-0042's two take **8% S** |

**On Invoices:** nothing is added — **Tax** (`6aa9f847e54d2a34fa4dfef4`) already exists and keeps its id. What
changes is the pair of roll-up workflows 07 built (*Roll the lines up into the invoice* and *…when a line is
deleted*, five steps each):

| Step | Now | After this bundle |
|---|---|---|
| 2 | sum of the product lines' **Subtotal** (汇总 node, 107) | unchanged |
| **2b** | — | **new**: sum of the same lines' **Total**, same filter (Invoice is this record **and** Display Type is Product) |
| 3 | Untaxed Amount = `$step2$+0` | unchanged |
| **3b** | — | **new**: Tax = `$step2b$-$step2$` |
| 4 | Total and Amount Due = `$step2$+$invoice-Tax$` — it reads the invoice's **stored** Tax | **`$step2b$+0`** — the sum of the lines' Total *is* the document total, so it stops reading the stored figure |
| 5 | writes Untaxed Amount, Total, Amount Due; **Tax read and never written** | **writes Tax too**, from step 3b |

Σ Total − Σ Subtotal is the document's tax **exactly**, because each line's Total is itself rounded to two
decimals and the company rounds per line (`tax_calculation_rounding_method = round_per_line`). The three seeded
documents must land on the tenant's own figures:

| Document | Untaxed | **Tax** | Total |
|---|---|---|---|
| SCG-PO-88213 | 104,603.20 | **10,460.32** | 115,063.52 |
| INV/2026/00001 | 11,432.00 | **1,143.20** | 12,575.20 |
| STL-2026-0042 | 180,000.00 | **14,400.00** | 194,400.00 |

**And automation B gains the tax fill.** 09 built two workflows — *fill the account of a new line* and *fill the
account when the Product changes* — that already fetch the invoice, the variant, the product, the category and
the journal, and branch on customer document versus vendor document. The tax fill is the same journey: on a
**customer** branch write the product's **Sales Taxes** into the line's Taxes, on a **vendor** branch its
**Purchase Taxes**, and on the journal-default branches (no product) write nothing. That is Odoo's
`_compute_tax_ids` without the fiscal position. **If it will not fit inside B's existing gateway, stop and
report** rather than rebuild B — see *Open questions*.

### Roles

**`account.tax` has exactly the access shape of `account.account`** — rows 74–77 and 68–72 of the same
`ir.model.access.csv`: `account.group_account_manager` reads, writes, creates and deletes; every other group,
including `group_account_invoice` and `group_account_readonly`, reads and no more. So Taxes takes **Chart of
Accounts' row unchanged**, and no new decision is needed:

| Role | Odoo group | Taxes |
|---|---|---|
| Accounting Administrator | `account.group_account_manager` | **full** |
| Accountant | `account.group_account_user` | view |
| Invoicing | `account.group_account_invoice` | view |
| Accounting Read-only | `account.group_account_readonly` | view |

Odoo's *menu* is stricter than its model — `menu_finance_configuration` is `groups="account.group_account_manager"`,
so only an administrator reaches the Taxes screen — but every internal user can **read** a tax, which is exactly
what lets an invoice line show one. Chart of Accounts sits under the same menu and was given view to all four for
the same reason; Taxes follows it.

**No field is hidden from a role.** The two fields Odoo puts behind a group — `analytic`
(`analytic.group_analytic_accounting`) and `is_base_affected` (`base.group_no_one`) — are one that is not built
and one that is developer mode, which is not a business role. `HIDDEN_FIELDS` is untouched.

The three fields added to **Products**, **Chart of Accounts** and **Invoice Lines** are ordinary fields of those
worksheets and inherit their rows; none of them is an account field, so `ACCOUNT_READONLY_FIELDS` and
`ACCOUNT_USER_FIELDS` are untouched too.

### Not built now, and why

| Left out | Why |
|---|---|
| **`account.tax.group` as a worksheet** — Tax Group is a Dropdown of the ten names | Odoo hides its menu behind `base.group_no_one`, so it is a developer-mode screen, not one a user reaches; and the tenant's ten groups **differ only in the name** — same country, same sequence 10, same SST Payable and SST Receivable, no advance account, no preceding subtotal. A Dropdown carries everything that varies. If it is ever wanted as a worksheet, the Dropdown becomes a Relation the way Contacts' Country and State did in bundles 4 and 5 — that path is already walked twice |
| **Distribution for Invoices / Refunds** (`invoice_repartition_line_ids`, `refund_repartition_line_ids`) and their **Tax Grids** (`tag_ids`) | All 36 lines on the tenant are the default — base 100 %, tax 100 %, sale taxes to SST Control Account, purchase taxes to none. Nothing varies, and the grids are `account.account.tag`, a model behind the tax reports |
| **Fiscal Position** (`fiscal_position_ids`) and **Replaces** (`original_tax_ids`) | `account.fiscal.position` is not one of the six. The five positions are recorded in the reference file |
| **Group of Taxes** (`children_tax_ids`) | The option stays in the Tax Computation dropdown because Odoo has it, but **no tax on this tenant is a group**, so there is nothing to seed and no children list to build |
| **Tax Exigibility** and **Cash Basis Transition Account** | The company has cash basis **off**, so Odoo hides both on every tax form here |
| **Include in Analytic Cost** (`analytic`) | Analytic accounting is not in Phase 1, and the tenant's own user cannot see the field |
| **Malaysian Tax Type**, **Tax Category Code** and the UBL exemption reasons | e-invoicing localisation — the same call 01 made for SST, TTx and the Malaysian TIN. The values are in the reference file and in `casimir-taxes.json` for the day it is built |
| **Tax used** (`is_used`) and the accounts' **Taxes** stat button (`related_taxes_amount`) | Computed counters over documents. 09 already deferred the stat button once |
| **A default tax on a new product** | Odoo takes it from the company (`account_sale_tax_id`, `account_purchase_tax_id`). Company settings are not one of the six, and a HAP Relation defaults to a fixed record, which would hard-code *10% G* into the app rather than read a setting |
| **Price-included taxes** | `account_price_include` is **tax_excluded** on this tenant and no tax overrides it, so the field is carried as data and nothing computes from it |
| **Odoo's refusal of a duplicate name** | See *Rules*: a workflow marks, it cannot refuse |

### Records

**All 35**, as the tenant holds them — the owner's standing instruction on Countries and States ("Seed all
2,102"), and 35 is nothing beside those. Ten active, 25 archived; every one Malaysia, sequence 1, with the
description, label, computation, amount, scope and group of `nocoly/data/casimir-taxes.json`.

The data file was **read straight out of the tenant** and then checked back against it by count, FNV-1a digest
over `name|type|scope|computation|amount|active|description|label|group` — one line per tax with the amount as `%.4f` and Active as 0/1, the 35 lines **sorted** and joined with newlines — and the sum of the amounts — **35
records, `0x4d7cffdc`, 139.0, 10 active on both sides**. The digest reconciliation that Countries and States
needed was not: 35 records fit through the browser.

Three seeds follow the worksheet: the **14 products'** sales and purchase taxes, the **8 invoice lines'** taxes,
and the **three documents'** recomputed amounts.

### Open questions for the build

1. **Does a 汇总 over a multi-relation follow the relation, and can a formula read it?** 10 §3 found that a 汇总
   over a **子表** holds the *saved* rows only, which is why Payment Terms' two roll-up rules had to be disabled.
   A 汇总 over a **Relation** may behave the same — the rate would then lag by one save while the form is open,
   which is acceptable and must be recorded — but if a number formula cannot read a 汇总 at all, *Total* has to
   be written by a workflow on the line instead. **Measure before building, and say which it is.**
2. **Can that 汇总 carry a filter on a Dropdown of the related worksheet?** `BUILDING.md` records a 汇总 filter
   with `filterType` 51 on a *single select*; Tax Computation is a **Dropdown** (type 11). If the filter will not
   take, the fallback is to let every tax's Amount into the sum and record the limit — harmless on this tenant,
   where every active tax is a Percentage.
3. **Does the tax fill fit inside automation B?** B is 25 nodes and already branches customer/vendor. Adding two
   writes to existing update steps is small; rebuilding B is not. **Stop and report rather than rebuild it.**
4. **Nothing is deleted.** No control, view, workflow or record is removed by this bundle — Chart of Accounts,
   Products, Invoice Lines and Invoices are all *added to*. The house rule stands: deleting anything needs the
   owner's approval.

## 2 · Build

Built by `nocoly/build/taxes.py` — steps `create → fields → rules → views → dupview → buttons → automations →
roles → seed → products → accounts → lines → rollup → amounts`, or `all` for every one of them followed by
`check`. Each step reads the live state first, refuses to run unless the profile reaches ERP Master › Invoicing
› Taxes and the worksheet holds only this script's own work, reads back what it wrote, and is safe to re-run:
**a second `all` ran all fourteen steps and created nothing, wrote no record, rewrote no workflow node,
changed no role and changed no control** — `rules already as specified; nothing saved` · `updated: nothing
(already as specified)` · `Archive: exists …; not re-created` · `0 taxes written` · `Products: the two
relations are already in place; nothing saved` · `0 products written` · `layout already as specified` · `the
subtable is already in its place` · `already built; not re-published` (both roll-ups) · `the tax fill is
already in; not re-published` (both halves of automation B) · `0 invoices driven through the roll-up` ·
`check: OK`.

Helpers: `check` reads the controls, the six rules, the three views and their order, the buttons, the roles,
workflow G and everything this bundle put on the other three worksheets against §1; `verify` compares all 35
taxes with the 19.4 extract field by field and prints the digests; `keys` reads every **Tax key** back one
record at a time and backfills anything a run of G missed; `selfcheck` drives the duplicate check and the
roll-up through the CLI on TEST records; **`measure` answers §1's two roll-up questions**; `order` prints each
view's records in its own order; `untouched` every other worksheet's control count and digest; `show` the
control list. The profile comes from `$HAP_PROFILE` and otherwise from hap-cli's active profile; **nothing in
`common.py` changed**.

| Element | Built | Id |
|---|---|---|
| App | ERP Master | `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Menu group | Invoicing — Chart of Accounts, **Taxes**, Journals, Payment Terms, Payment Term Lines, Invoices, Invoice Lines | `6aa8f3ecbf00c316381dbbe8` |
| Worksheet | Taxes, alias **`account_tax`**, icon `sys_percentage_finance` | `6aad1034805aef703286ac2f` |
| Controls | **19** — sixteen Odoo fields, the *Advanced Options* divider and the two duplicate-check helpers | — |
| Fields | Tax Name (Text, **title**, required) · Tax Type (Dropdown, required, default Sales) | `6aad104e7d58b0f4493141f9` · `6aad104e7d58b0f4493141fa` |
| | Tax Computation (Dropdown, required, default Percentage) · Amount (Number, **4 decimals**, required, default 0) | `6aad104e7d58b0f4493141fb` · `6aad104e7d58b0f4493141fc` |
| | Formula (Text, default `price_unit * 0.10`) · Sequence (Number, 0 decimals, required, default 1) | `6aad104e7d58b0f4493141fd` · `6aad104e7d58b0f4493141fe` |
| | Description (Text — the stock control's id, reused) · Label on Invoices (Text) | `6aad1034805aef703286ac31` · `6aad104e7d58b0f4493141ff` |
| | **Divider *Advanced Options*** (type 22) | `6aad104e7d58b0f449314200` |
| | Tax Scope (Dropdown) · Tax Group (Dropdown of the ten group names) | `6aad104e7d58b0f449314201` · `6aad104e7d58b0f449314202` |
| | Country (Relation → Countries, single, **one-way**, required, default **Malaysia**) · Included in Price (Dropdown, placeholder *Default*) | `6aad104e7d58b0f449314203` · `6aad104e7d58b0f449314205` |
| | Affect Base of Subsequent Taxes (checkbox, default off) · Base Affected by Previous Taxes (checkbox, default **on**) | `6aad104e7d58b0f449314206` · `6aad104e7d58b0f449314207` |
| | Active (checkbox, default on) · **Duplicate name** (checkbox, read-only and hidden on create — `fieldPermission` "100") | `6aad104e7d58b0f449314208` · `6aad104e7d58b0f449314209` |
| | Legal Notes (RichText, full width) | `6aad104e7d58b0f44931420a` |
| Hidden helper | **Tax key** (**Text**, `fieldPermission` "001" — hidden *and* read-only — carrying **No duplicates**) | `6aad104e7d58b0f44931420b` |
| Rules | six interaction rules, Odoo's own visibility | below |
| Views | Taxes (the stock *All*, renamed) — opens first · Archived · **Duplicate names** | `6aad1034805aef703286ac33` · `6aad11d1e54d2a34fa4e584b` · `6aad11e77d58b0f449314258` |
| Buttons | Archive (`btnId` `6aad11fbbd43f55762c7587f`, workflow `6aad11fb8e75db182e9dccf4`) · Unarchive (`6aad11fd805aef703286ac59`, `6aad11fd87707da9d62ab172`) | — |
| Workflow **G** | *Taxes: the key and the duplicate check* — published, **quiet**, 16 nodes | `6aad12174f2a99acac2d4f4c` |
| Records | the tenant's **35 taxes**, every one carrying its **Tax key**, plus four `TEST` taxes (below) | — |
| On **Products** | **Sales Taxes** (`taxes_id`) · **Purchase Taxes** (`supplier_taxes_id`) — Relation → Taxes, multiple, one-way, picker-filtered | `6aad156dbd43f55762c758c2` · `6aad156dbd43f55762c758c4` |
| On **Chart of Accounts** | **Default Taxes** (`tax_ids`) — Relation → Taxes, multiple, one-way, added empty | `6aad160f805aef703286ace4` |
| On **Invoice Lines** | **Taxes** (`tax_ids`, multiple, unfiltered) · **Tax rate** (汇总, hidden) · **Total** (`price_total`, number formula) | `6aad1419bd43f55762c758ab` · `6aad1428e43d174ab374fb98` · `6aad1437bd43f55762c758b0` |
| On the two roll-ups | step **2b** and step **3b** in each | `6aad1783a2c872a5c113c860` / `6aad1784a2c872a5c113c89e` (create-or-update) · `6aad1791a2c872a5c113cadf` / `6aad1792a2c872a5c113cb1d` (delete) |
| On **Invoices** | **nothing** — Tax `6aa9f847e54d2a34fa4dfef4` keeps its id and stops being a seeded figure | — |

Every id is in `nocoly/build/ids.json`: the nineteen controls, the three views, the six rules, the two buttons
and the three workflows under `"Taxes: …"`; the 35 taxes under `"Taxes: <country code>|<tax type>|<tax
scope>|<tax name>"` — Odoo's own natural key, the four its constraint is on — with the four TEST taxes beside
them; `"Products: Sales Taxes"`, `"Products: Purchase Taxes"`, `"Chart of Accounts: Default Taxes"` and
`"Invoice Lines: Taxes" / "Tax rate" / "Total"` for the controls added to other worksheets; and `"Taxes"` under
`worksheets`. **No existing key was renamed.** Two keys this bundle wrote itself were corrected during the
build and are named in *Found while building*.

### The form

Nineteen controls, §1's layout exactly — one divider and no tab, because Odoo's *Definition* page holds only
the distribution lists, none of which is built:

```
r0  c0 s6   2 Tax Name                 6aad104e7d58b0f4493141f9  name                    title required
r0  c1 s6  11 Tax Type                 6aad104e7d58b0f4493141fa  type_tax_use            required  opts=Sales/Purchases/None
r1  c0 s6  11 Tax Computation          6aad104e7d58b0f4493141fb  amount_type             required  opts=Group of Taxes/Fixed/Percentage/Percentage Tax Included/Custom Formula
r1  c1 s6   6 Amount                   6aad104e7d58b0f4493141fc  amount                  required dot=4
r2  c0 s6   2 Formula                  6aad104e7d58b0f4493141fd  formula
r2  c1 s6   6 Sequence                 6aad104e7d58b0f4493141fe  sequence                required dot=0
r3  c0 s6   2 Description              6aad1034805aef703286ac31  description
r3  c1 s6   2 Label on Invoices        6aad104e7d58b0f4493141ff  invoice_label
r4  c0 s12 22 Advanced Options         6aad104e7d58b0f449314200                          ← the divider
r5  c0 s6  11 Tax Scope                6aad104e7d58b0f449314201  tax_scope               opts=Goods/Services
r5  c1 s6  11 Tax Group                6aad104e7d58b0f449314202  tax_group_id            opts=the tenant's ten
r6  c0 s6  29 Country                  6aad104e7d58b0f449314203  country_id              required → Countries, default Malaysia
r6  c1 s6  11 Included in Price        6aad104e7d58b0f449314205  price_include_override  hint='Default'
r7  c0 s6  36 Affect Base of Subseq…   6aad104e7d58b0f449314206  include_base_amount
r7  c1 s6  36 Base Affected by Prev…   6aad104e7d58b0f449314207  is_base_affected
r8  c0 s6  36 Active                   6aad104e7d58b0f449314208  active
r8  c1 s6  36 Duplicate name           6aad104e7d58b0f449314209  duplicate_name          perm=100
r9  c0 s12 41 Legal Notes              6aad104e7d58b0f44931420a  invoice_legal_notes
r10 c0 s6   2 Tax key                  6aad104e7d58b0f44931420b  tax_key                 perm=001 unique
```

**The controls went in in three saves.** Nothing here is a formula, so no id had to be re-minted between
passes — but a new worksheet comes with three stock controls and one of them, **Description**, is a field of
this form: (1) `add-fields` appended the other **eighteen**, the stock Description control
`6aad1034805aef703286ac31` being kept for Description because the name and the type match; (2) one full save
dropped the stock **Name** `6aad1034805aef703286ac30` and **Attachment** `6aad1034805aef703286ac32`, which this
form has no use for and which held nothing — `drop_stock` refuses to run once the worksheet has a record, and
refuses to touch any control this form does use; (3) one placing save for rows, sizes, aliases, descriptions,
hints, permissions, decimals, the options, the defaults and the title field. **Tax Name was the only control
carrying `attribute` 1 in that save**, so the title was not the coin toss `BUILDING.md` warns of.

Defaults are HAP static defaults, which only the **form** applies: Tax Type *Sales*, Tax Computation
*Percentage*, Amount 0, Sequence 1, Formula `price_unit * 0.10`, Affect Base off, Base Affected **on**, Active
on, and **Country → Malaysia** (`6aacb67d7d58b0f449312f04` / rowid `3a554a3a-b46a-4e7a-8a36-91c029161bb8`, a
static Relation default, which the server stores as the whole country record). The API applies none of them,
which is why `seed` writes every one of those fields explicitly.

**Country is one-way** (`bidirectional` "0"): Odoo's tax form lists neither the products nor the accounts nor
the lines that use it. The server reserved a reverse id `6aad104e7d58b0f449314204` in `sourceControlId` and, as
`BUILDING.md` says it does, created nothing on Countries — **Countries still has its eight controls**.

### The rules — Odoo's visibility, six interaction rules

§1 lists five; HAP needs six, because a field a rule **hides** must not be required on the field itself (a
required field nobody can see blocks the save), so "required otherwise" is a second rule with the opposite
condition. All six condition on **Tax Computation**, and all six are *is any of* (`filterType` 2 in the
business-rule enum, several option keys in one condition).

| Id | Rule | Condition — Tax Computation is | Does |
|---|---|---|---|
| `6aad10bfbd43f55762c7585a` | Amount is not offered for a group of taxes or a custom formula | Group of Taxes · Custom Formula | **hide** Amount |
| `6aad10bfe54d2a34fa4e583a` | Formula is only for a custom formula | Custom Formula | **show** Formula |
| `6aad10c0e43d174ab374fb57` | Formula is required for a custom formula | Custom Formula | **require** Formula |
| `6aad10c0e43d174ab374fb59` | Tax Group is not offered for a group of taxes | Group of Taxes | **hide** Tax Group |
| `6aad10c1bd43f55762c7585c` | Tax Group is required unless the computation is a group of taxes | Fixed · Percentage · Percentage Tax Included · Custom Formula | **require** Tax Group |
| `6aad10c17d58b0f44931421f` | A group of taxes carries no price or base settings | Group of Taxes | **hide** Included in Price, Affect Base of Subsequent Taxes, Base Affected by Previous Taxes |

The *form* of each rule is chosen by what a **new** tax should show, which is the house rule `BUILDING.md`
records: a rule applies its action while its condition holds and the opposite when it fails. Tax Computation is
required and defaults to Percentage, so Amount and the three Advanced Options fields are written as **hide · is
any of**, which leaves them visible from the start, and Formula as **show · is Custom Formula**, which keeps it
hidden until the computation asks for it.

**§1's rule 5 is a field permission, not a rule.** *Duplicate name read-only and off the create form* is
`fieldPermission` "100" on the control — which is exactly how States built the same checkbox (12 § *The
duplicate check, rebuilt*: States has **no** rules at all). Recorded as a departure below.

### The three views

**Taxes**, the stock *All* renamed, opens first. Odoo's own six columns, **all 35 rows** — the window action
turns `active_test` off, so its list shows the archived taxes too and draws them muted, and §1 therefore asks
for no Active filter. Sorted **Sequence ascending, then created**: all 35 share sequence 1, so the list reads
in creation order, which is the arrangement Payment Terms already uses (`ctime` as the second `moreSort` key).

```
Taxes            6aad1034805aef703286ac33  sortCid=Sequence/2  moreSort=[(Sequence, asc), (Created, asc)]
                 columns=[Tax Name, Description, Tax Type, Tax Scope, Label on Invoices, Active]
                 filters=[]  fastFilters=[Tax Type {allowitem 2, direction 2}, Tax Scope {allowitem 2,
                                          direction 2}, Active {}]
Archived         6aad11d1e54d2a34fa4e584b  same columns and sort, filters=[(Active, filterType 6, ['1'])]
Duplicate names  6aad11e77d58b0f449314258  columns=[Tax Name, Tax Type, Tax Scope, Country, Duplicate name]
                 filters=[(Duplicate name, filterType 2, ['1'])]  fastFilters=[]
```

The three quick filters stand in for Odoo's search facets: **Tax Type** and **Tax Scope** as *is any of*
dropdowns, written as the spec adapter's object (`{fieldId, selectionType: "multiple", displayType:
"dropdown"}`), which lowers to `allowitem` "2" / `direction` "2" and is written identically on every run; and
**Active** as a plain checkbox filter, which takes neither setting and is sent as a bare `{controlId}`.

*Duplicate names* is States' *Duplicate codes* with this form's five columns, and `dupview` never touches the
other two: it sends only its own view to `upsert_views`, names the three to `sort_views` (which leaves every
view it is not given where it is) and then compares the other two views' `showControls`, `sortCid`, `sortType`,
`moreSort`, `filters`, `fastFilters` and `advancedSetting` before and after. A second run reports *Taxes and
Archived: unchanged*. It lists **nothing**, which is the point of it.

### The buttons

The house pair, the seventh worksheet to carry them, each with its one-step workflow: **Archive** (shown while
Active is checked, batch, confirm *Are you sure that you want to archive this record?*) writing Active 0, and
**Unarchive** (shown while it is not) writing Active 1.

### Workflow G — the key and the duplicate check

§1's *Rules* as a workflow, States' G with a four-part key instead of two. Worksheet event **新增或更新** on
Taxes, narrowed to **Tax Name, Tax Type, Tax Scope and Country**, with a trigger **condition** — and it is the
condition that makes §1's "taxes whose Tax Type is None are exempt" real:

| # | Node | Id | Does |
|---|---|---|---|
| — | trigger *When a tax's Name, Type, Scope or Country is written* | `6aad12174f2a99acac2d4f4d` | 新增或更新, four fields, **Tax Type is any of Sales, Purchases** (conditionId 1) |
| 1 | Get the country | `6aad12184f2a99acac2d50b6` | the trigger's Country, so the code is read from the country record |
| 2 | Work out the key | `6aad12184f2a99acac2d50cb` | a text function formula (106) — below |
| 3 | Another tax with this key? | `6aad12184f2a99acac2d50e0` | a search of Taxes: Tax key = that **and Record ID ≠ the trigger** (conditionId 10), oldest first, carrying on when nothing is found |
| 4 | Is there one? | `6aad12194f2a99acac2d50f1` | an exclusive gateway |
| 4a | *Yes — another tax already holds this key* | `6aad12194f2a99acac2d50f2` | conditioned: the found tax's Tax key **is not empty** |
| | → Tick Duplicate name | `6aad12194f2a99acac2d5111` | |
| | → Clear the Tax key | `6aad121987707da9d62ab28d` | `isClear`, the editor's 清空 |
| | → **Stop — a duplicate gets no key** | `6aad121b87707da9d62ab329` | **中止流程, node type 30** |
| 4b | *No — this key is free* | `6aad12194f2a99acac2d50f3` | no condition: the default path |
| | → Untick Duplicate name | `6aad121a87707da9d62ab2d7` | |
| 5 | Write the Tax key | `6aad121a87707da9d62ab2ec` | `$<step 2>-string_fx_id$` |

The key is

```
CONCAT($<country>-<Country Code>$,"|",
       IF($<trigger>-<Tax Type>$=="Sales","sale",IF($<trigger>-<Tax Type>$=="Purchases","purchase","none")),"|",
       IF($<trigger>-<Tax Scope>$=="Goods","consu",IF($<trigger>-<Tax Scope>$=="Services","service","")),"|",
       $<trigger>-<Tax Name>$)
```

— `MY|sale|consu|10% G`, and `MY|sale||0% NA` where the scope is empty. **A workflow formula renders a dropdown
as its *label***, so the two selections are translated back to Odoo's own keys with `IF`; a workflow formula
compares with `==`, never `=`, and `CONCAT` is the only way to join text (`+` would be read as an octal
literal). The country's code is read from the **country record** step 1 fetched rather than from a lookup on
the tax, because a lookup is a value HAP recomputes on save and the run would be reading it while it is being
written.

**The tick comes before the key write, they are two steps, and the duplicate path ends in an abort.** That is
not belt and braces: a workflow's update step is **not** subject to *No duplicates* (measured on States, 18
Sep), so nothing but this workflow's shape keeps the key unique. A branch converges, so an empty path is not a
stop; only the abort is. G is **quiet** (`triggerType` 2 · 不允许触发), the standing rule for a workflow writing
its own record.

**G wrote all 35 keys itself.** The seed's 35 creates each carry Tax Name, Tax Type, Tax Scope and Country, so
each started one run; `keys` then read every key back one record at a time and found **35 of 35 correct, 0
empty, 0 carrying Duplicate name**, with nothing to backfill. (States backfilled its 2 102 keys through the API
instead, because 2 100 runs would have been an hour of the organisation's quota; 35 is a rounding error.) With
the four TEST taxes it now reads *39 taxes: 38 carried a Tax key, 1 did not, 0 carry Duplicate name* — the one
without a key is **`TEST Type None`**, which is right, and `keys` says so rather than repairing it.

### The roles

`roles.py` owns the app's roles; its `ORDER` and its four matrices now carry **Taxes with Chart of Accounts'
row unchanged** — `account.tax` has exactly the access shape of `account.account` in the same
`ir.model.access.csv`, so no new decision was needed and none was asked for:

| Role | Taxes |
|---|---|
| Accounting Administrator | **full** (read · edit · delete · add) |
| Accountant · Invoicing · Accounting Read-only | **view** |

`VIEW_ONLY` is untouched (it still holds Countries alone), `HIDDEN_FIELDS` is untouched — the two fields Odoo
puts behind a group are one that is not built (`analytic`) and one that is developer mode (`is_base_affected`)
— and `roles.py check` reads back **OK**. The CRM worksheets another administrator is building keep appearing
in the four roles at HAP's own defaults; `roles.py` prints them as *not in the owner's table* and writes
nothing to them, exactly as it did in bundle 5.

### The records — all 35

Matched by Odoo's own natural key (country, type, scope, name), so a re-run writes nothing; every field of §1
written explicitly, **Active included**, because the API applies no defaults. `verify` compares all 35 with the
extract field by field:

```
35 taxes in the extract; 0 missing []; 0 differing {}; 4 live records outside it
    ['MY|none||TEST Type None', 'MY|sale||TEST Duplicate Probe', 'MY|sale||TEST Fixed 7',
     'MY|sale||TEST Percent 3']
OK  count       live 35          extract 35     §1 35
OK  active      live 10          extract 10     §1 10
OK  amount_sum  live 139.0       extract 139.0  §1 139.0
OK  names       live 27          extract 27
OK  fnv         live 0x8bd7e5da  extract 0x8bd7e5da
```

The four outside the extract are this build's own TEST taxes, below. `names` and `fnv` are printed with no §1
column on purpose — see *Where the build departed from §1*.

Four **TEST** taxes are left in the worksheet beside them, all Malaysia / Not Applicable:

| Name | What it is for | Id |
|---|---|---|
| `TEST Percent 3` | a Percentage of 3 — the 汇总 must count it | `69b4125e-56c7-4de6-a1e0-370a95876781` |
| `TEST Fixed 7` | a **Fixed** of 7 — the 汇总's filter must leave it out | `bbd4a602-1656-45c9-9aa5-b568a4e2f160` |
| `TEST Type None` | Tax Type **None** — G must never run on it | `6314a3cd-5f6b-41f7-b05e-08a602907dc1` |
| `TEST Duplicate Probe` | the duplicate check's own record | `1e930dc4-44fe-48e4-984d-0b4e2adf8a8b` |

and one TEST invoice line, `TEST Tax rate probe` `13c07e50-b2aa-4e11-9060-3644dd8e4da2`, on the TEST document
*TEST PT D probe* — 1 × 100.00, **no Product**, so that automation B's tax fill cannot touch its Taxes and the
probe measures the 汇总 alone.

### What this bundle put on Products

**Sales Taxes** after Sales Price and **Purchase Taxes** after Cost, in the *General Information* tab, each a
full-width Relation → Taxes, multiple, one-way, not required, with a **picker filter** on Tax Type (Sales /
Purchases respectively) — Odoo's own `domain=[('type_tax_use','=','sale')]`. A picker filter runs in the
browser only, so §3 is what proves it.

```
r5  Product Type | Sales Price
r6  Sales Taxes       6aad156dbd43f55762c758c2  taxes_id            picker: Tax Type is Sales
r7  Unit | Cost
r8  Purchase Taxes    6aad156dbd43f55762c758c4  supplier_taxes_id   picker: Tax Type is Purchases
r9  Category | Internal Reference
r10 Internal Notes
```

**`products.py` was not run**, as the hand-off asks — its `PLACE` predates another administrator's edits (see
*Found while building*). This step does its own placing save, pinned to the control set's `version` so that an
edit made between the read and the save is **refused** rather than overwritten, and it computes the new rows
from the form's **own existing row groups** rather than from any spec: each relation is inserted as a group of
its own straight after the group holding the control it follows, and the groups are renumbered. Every
pre-existing control kept its column, size, tab and everything else; only the rows below the insertions moved
(Unit and Cost by one, everything under them by two).

**Values.** All 14 products: the **8 goods** take *10% G* / *0% NA*, the **6 services** *8% S* / *0% NA*,
written from the extract and read back one product at a time. No default is built — Odoo takes both from the
company, and a HAP Relation defaults to a fixed record, which would hard-code *10% G* into the app (§1 › *Not
built now*).

### What this bundle put on Chart of Accounts

**Default Taxes** (`tax_ids`) `6aad160f805aef703286ace4` — Relation → Taxes, multiple, one-way, not required,
at **row 3**, straight under Type, where Odoo's *Accounting* tab puts it; Payment Reconciliation and everything
under it moved down one row. **No values**: the step reads every account back and confirms **0 carry one**, as
§1 says. The column stays switched off on both views.

The placing is **`accounts.py layout`'s own**, whose `PLACE` now carries the field with a comment — the same
arrangement `products.py`'s PLACE has for the two account fields bundle 2 added to it. `accounts.py check` and
`accounts.py check-b` were both run afterwards (below).

### What this bundle put on Invoice Lines

| | |
|---|---|
| **Taxes** `6aad1419bd43f55762c758ab` | `tax_ids`, Relation → Taxes, **multiple**, one-way, **unfiltered** — Odoo's own context on the field is `{'active_test': False}` and it carries no Tax Type domain |
| **Tax rate** `6aad1428e43d174ab374fb98` | 汇总 (type 37), `dataSource` `$Taxes$`, `sourceControlId` = the Taxes worksheet's **Amount**, `enumDefault` **5** (sum), `dot` 4, `fieldPermission` **"001"** (hidden *and* read-only), filtered **Tax Computation is Percentage** (`filterType` 51) |
| **Total** `6aad1437bd43f55762c758b0` | `price_total`, number formula, 2 decimals, read-only: `$Subtotal$*(1+$Tax rate$/100)` |

```
r6  Unit Price | Discount (%)
r7  Taxes        6aad1419bd43f55762c758ab  tax_ids
r8  Subtotal     6aaa2c18e43d174ab3749df1  price_subtotal   perm=101
r9  Total        6aad1437bd43f55762c758b0  price_total      perm=101  = $Subtotal$*(1+$Tax rate$/100)
r10 Number | Accounting Date
r11 Status
r12 Tax rate     6aad1428e43d174ab374fb98  tax_rate         perm=001  (汇总, hidden)
```

Odoo's own column order — the taxes between the price and the amount, and `price_total` straight after
`price_subtotal`. The **placing, the rule and the two column lists are `invlines.py`'s own steps**, whose spec
was extended with a `BUNDLE_6` tuple the way `countries.py` was given `BUNDLE_5` in bundle 5:

- **Taxes and Total joined the rule** *A section or a note carries no figures*, which now hides Product,
  Account, Quantity, Unit, Unit Price, Discount (%), **Taxes**, Subtotal and **Total** — Odoo's
  `check_non_accountable_fields_null` covers the taxes too, and a section showing a tax picker and a total is
  wrong. This is beyond §1's letter and is recorded as a departure;
- **Total joined both column lists**, after Subtotal: the standalone *Lines* view and the **Lines subtable
  inside an invoice**, which now reads Sequence · Display Type · Product · Label · Account · Quantity · Unit ·
  Unit Price · Discount (%) · Subtotal · **Total**;
- `invlines.py check` reads back **OK**.

**Values.** All three seeded documents are **Customer Invoices**, so all three take the **Sales** tax:
SCG-PO-88213's three and INV/2026/00001's three take `MY|sale|consu|10% G`, STL-2026-0042's two take
`MY|sale|service|8% S`. Every line's Total was read back against `Subtotal × (1 + Tax rate ÷ 100)`.

### The roll-up

07's two workflows — one per worksheet event, because HAP's trigger takes one — each gained **two steps**, one
formula changed and the write gained a field. Nothing was deleted and no node was moved.

| # | Step | Kind | Does | create-or-update `6aaa2d6aa1c923a16efc81a7` | delete `6aaa2ebba1c923a16efc8ecf` |
|---|---|---|---|---|---|
| 1 | Get the invoice | search (7 / 406) | unchanged | `6aaa2d6c16473257ad4f1201` | `6aaa2ebea1c923a16efc8eed` |
| 2 | The sum of the invoice's product lines | 汇总 (9 / **107**), sum of **Subtotal** | unchanged | `6aaa2d6d16473257ad4f121a` | `6aaa2ebe87707da9d60e94a4` |
| **2b** | **The sum of the same lines' Total** | 汇总 (9 / 107), sum of **Total**, the same filter | **new** | `6aad1783a2c872a5c113c860` | `6aad1791a2c872a5c113cadf` |
| 3 | The Untaxed Amount | number formula (9 / 100) | `$2$+0`, unchanged | `6aaa2d6d16473257ad4f1235` | `6aaa2ebf87707da9d60e94bf` |
| **3b** | **The Tax** | number formula (9 / 100) | **`$2b$-$2$`** | `6aad1784a2c872a5c113c89e` | `6aad1792a2c872a5c113cb1d` |
| 4 | The Total and the Amount Due | number formula (9 / 100) | **`$2b$+0`** — was `$2$+$the invoice's stored Tax$` | `6aaa2d6e16473257ad4f1254` | `6aaa2ebf87707da9d60e94e8` |
| 5 | Write the amounts into the invoice | update (6 / 2) | Untaxed ← 3, **Tax ← 3b**, Total ← 4, Amount Due ← 4 | `6aaa2d6e16473257ad4f1273` | `6aaa2ec0a1c923a16efc8f1a` |

Both new formulas carry `number: 2` and `nullZero: true`, the two settings `BUILDING.md` records as silent
traps. `batch-add` can only append, so the two steps went in **in the middle of the chain** with
`workflow node add --type 9 --after <the step they follow>`, the 107 carrying `--app-id` at create time.

**Σ Total − Σ Subtotal is the document's tax exactly**, because each line's Total is itself rounded to two
decimals and the company rounds per line. The three seeded documents land on the tenant's own figures, and the
**Tax is now computed** rather than seeded:

| Document | Untaxed | **Tax** | Total | Amount Due |
|---|---|---|---|---|
| SCG-PO-88213 | 104,603.20 | **10,460.32** | 115,063.52 | 115,063.52 |
| INV/2026/00001 | 11,432.00 | **1,143.20** | 12,575.20 | 12,575.20 |
| STL-2026-0042 | 180,000.00 | **14,400.00** | 194,400.00 | 194,400.00 |

`amounts` writes nothing into an invoice by hand. It starts each document's own roll-up on one of its lines —
`hap workflow trigger <processId> -s <rowid>`, which turns out to run a **worksheet-event** workflow on one
record just as it runs a button's — and reads the four amounts back. (A `record update` that changes nothing
fires no workflow, so the alternative would have been writing a value and writing it back.) It also checks
every other invoice that has lines: nine documents, all consistent.

### Automation B's tax fill — §1's third open question

**It fits. Nothing was rebuilt** — no node, path, gateway or condition was added, moved or re-conditioned in
either of 09's two workflows. Four of the seven paths' update steps gained **one entry** in their `fields`
list: the line's **Taxes**, taken from the *Get the product* step, the product's **Sales Taxes** on a customer
document and its **Purchase Taxes** on a vendor one — Odoo's `_compute_tax_ids` without the fiscal position.

| Path | Step | Now also writes |
|---|---|---|
| Customer document — the product's Income Account | Take the product's Income Account | Taxes ← the product's **Sales Taxes** |
| Customer document — the category's Income Account | Take the category's Income Account | Taxes ← the product's **Sales Taxes** |
| Vendor document — the product's Expense Account | Take the product's Expense Account | Taxes ← the product's **Purchase Taxes** |
| Vendor document — the category's Expense Account | Take the category's Expense Account | Taxes ← the product's **Purchase Taxes** |

The taxes always come from the **product**, never the category, because Odoo's do. The three **journal-default**
paths write no tax, as §1 says: they are the paths the product and its category gave no account on, and on this
tenant every product and every category carries both accounts, so in practice they are reached only by a line
with **no product at all** — which has no tax to take.

`accounts.py`'s own spec was extended to match (`B_TAX_FILL_STEPS`, `b_tax_fill`, `b_tax_entry`), so
`automation_b_differences` still reads both workflows back in full; it reports **no differences**, and
`accounts.py check-b` is discussed below.

### §1's open questions, answered

**1 · A 汇总 over a multi-Relation follows the relation, and a number formula can read it.** Measured on the
TEST line, which carries no Product, through the API alone (`taxes.py measure`):

| The line's Taxes | Tax rate | Total (subtotal 100.00) |
|---|---|---|
| none | 0.0 | 100.00 |
| TEST Percent 3 | **3.0** | **103.00** |
| TEST Percent 3 + TEST Fixed 7 | **3.0** | **103.00** |
| TEST Fixed 7 alone | 0.0 | 100.00 |

So **Total is a formula, not a workflow** — §1's fallback was not needed. What a 汇总 does while a **form** is
open is a different question: 10 §3 found that a 汇总 over a **子表** holds only the *saved* rows, and whether
the same is true of one over a Relation is a §3 test (below). Nothing in Phase 1 gates a save on this roll-up,
so even the lagging answer would be acceptable.

**2 · The 汇总's filter does take on a Dropdown (type 11) of the related worksheet.** Rows three and four of
that table are the proof: a **Fixed** tax of 7 added **nothing** to the rate, alone or beside a percentage.
`filterType` **51** — the filter editor's *is* on a single select, which bundle 3 had only ever proved on a
子表's own single select — works over a multi-Relation and against the related worksheet's Dropdown. §1's
fallback (let every Amount into the sum and record the limit) was not needed.

**3 · The tax fill fits inside automation B**, above: four field entries, no rebuild.

**4 · Nothing was deleted** — no control, view, rule, workflow, button or record of any worksheet, and the
Sales app was never opened. The only two controls that went are the **stock Name and Attachment of the Taxes
worksheet this build created minutes earlier**, in the first-save pattern every worksheet here was built with;
they held nothing and the worksheet had no records.

### Where the build departed from §1

| § | §1 says | Built | Why |
|---|---|---|---|
| Rules | five rules | **six** | A field a rule hides must not be required on the field itself, so "Tax Group required otherwise" and "Formula required" are rules of their own (`BUILDING.md`, Journals' two Payment Communications) |
| Rules 5 | *Duplicate name read-only, off the create form — States' rule verbatim* | a **field permission**, `fieldPermission` "100" | That *is* States' mechanism — 12's §1 gives States no rules at all |
| Fields 5 | Amount "with a `%` after it unless the computation is Fixed" | **no suffix** | A HAP Number's `advancedSetting.suffix` is static. It would read *10.0000 %* on the 32 percentage taxes and wrongly on a Fixed one; rule 1 already hides Amount for the other two computations. Recorded as a difference, not built |
| Invoice Lines | Taxes and Total are not named in 07's hide rule | **both added to it** | Odoo's `check_non_accountable_fields_null` forbids them on a section, subsection or note, and a section showing a tax picker and a Total is wrong |
| Records | "fourteen of the 35 names are shared by two records" | **eight** names are shared, by sixteen records — **27 distinct names** | Measured from the data file. Nothing built depends on it |
| Fields 8 | "four of the 35 [Labels on Invoices] are empty" | **seven** — ids 9, 10, 11, 28, 29, 30, 31 | Measured from `casimir-taxes.json`, which agrees with the reference file's own table. The seed writes what the file has, so nothing built depends on it either |
| Records | FNV-1a `0x4d7cffdc` | not reproduced; **`0x8bd7e5da`** live **and** in the extract | §1 does not say how the 35 per-record digests are combined, so its number cannot be recomputed. What `verify` proves instead is that the **live records and the extract give the same digest**, which is the claim that matters |
| Products | picker "filtered to Tax Type is Sales" | exactly that — **and nothing else** | Odoo's product field has no `active_test` override, so its own picker also hides the 25 archived taxes. §1 names only the Tax Type domain, so only that is built. One line of `taxes.py` (`tax_picker`) adds *Active is checked* if the owner wants it — see *For the UI test* |

### Found while building

- **`hap workflow trigger <processId> -s <rowid>` starts a worksheet-event workflow on one record**, not just a
  button's. That is the only way to re-run a roll-up over a record without writing to it, since a `record
  update` that changes nothing fires nothing. Added to `BUILDING.md`.
- **`batch-add` can only append**, so both roll-ups' new steps went in with `workflow node add --type 9 --after
  <the step they follow>` — `-a 107` for the 汇总 (with `--app-id` at create time, as any data node needs) and
  `-a 100` for the formula. Added to `BUILDING.md`.
- **A single select reads back as its option *key* through `GetRowDetail`** and as `[{key, value}]` through the
  v3 `record get`. The first `verify` reported all 35 taxes missing because the reader expected the label.
  Added to `BUILDING.md`.
- **A field write taking a formula node's result reads `nodeAppType` back as 11**, whatever it was sent as; a
  step that compares what it sent with what came back must leave that key out.
- **A control-set signature compared as a *string* is not stable across a change to another worksheet.** Giving
  Chart of Accounts its Default Taxes control changed the record embedded inside **Contacts'** two static
  account defaults — the server re-serialises that snapshot on every read and the new column appears inside it
  — and `accounts.check_untouched` stopped the run over a worksheet nothing had touched. `accounts.signature`
  and `invlines.signature_of` now compare through `accounts.control_state`, which parses `advancedSetting` and
  reduces a Relation default to record ids, exactly as `BUILDING.md` already prescribed for digests. Added
  there as the second half of that bullet.
- **A by-name index over the whole control list is a trap, not only for `common.fields`.** Products carries a
  *Sales* **checkbox** and a *Sales* **tab**; a row map keyed by `controlName` put the checkbox on the tab's
  row and moved it out of the form header. Caught by the read-back, repaired in a save of its own
  (`taxes_products_controls_pre_sales_repair`), and the map is keyed by `controlId` now. Added to
  `BUILDING.md`.
- **Inserting two controls into a form is not a single shift.** The first insertion moves the row it lands on
  by **one**, the second moves everything under it by **two**; a blanket "+2 from row 6 down" put Purchase
  Taxes on Unit's row. `place_product_taxes` renumbers the form's own row groups instead, which is also what
  makes it idempotent.
- **`products.py`'s `PLACE` was already stale before this bundle** — measured from the backup taken before the
  first write: **15 of its controls** were out of place (Active at row 3 against its 15, Product Type 5 against
  4, Unit 6 against 5, Category 7 against 6, Income and Expense Account 16 against 14, and the *Sales*
  name clash again). Running `products.py layout` would therefore already have rewritten the live form, which
  is why the hand-off forbids it and why this bundle placed its own two fields. Two consequences a reviewer
  will see and should not chase:
  - **`accounts.py check-b` reports Products out of place** — it did before this bundle for the same fifteen
    controls; everything else in `check-b` is clean;
  - **`prodcat.py check` reports `Products / Category: {'row': (9, 6)}`** — it reported `(7, 6)` before.
  One fix closes all three: bring `products.py`'s `PLACE` (and `prodcat.CATEGORY_PLACE`) up to the live form,
  which means adopting the other administrator's edits into 03's spec — the owner's call, not this build's.
- **`payterms.py check` asserts the Invoicing menu group's exact contents**, so adding Taxes to it broke that
  one line. `payterms.py` was told about Taxes and reads **OK** again; nothing else in it changed.
- **`hap app sort-worksheets` is safe here**: the Invoicing group is entirely this build's, and Taxes was moved
  in front of Journals where Odoo's Accounting configuration menu has it. The app's **menu groups** were never
  re-sorted (`common.ensure_section` is not called), so the CRM group another administrator is building stayed
  where it is.
- **Two ids.json keys this bundle wrote itself were corrected during the build**, before the hand-off: the 35
  record keys were first written as `Taxes: MY|||<name>` (the option-key reading bug above) and were rewritten
  to the four-part natural key, and the two stock controls dropped by `fields` are now filed as `Taxes: Name
  (stock control, dropped by \`fields\`)` and `Taxes: Attachment (stock control, dropped by \`fields\`)`, the
  way ids.json already annotates a deleted id. **No key belonging to another bundle was touched.**

### The self-check

`taxes.py selfcheck`, seven probes through the CLI, all OK:

```
OK  0b. a tax created through the API with no Tax key in the write: accepted, 1e930dc4-… — nothing in HAP
        refuses the record itself, and a form sends no hidden read-only control either
        G on the create: status 2 :: trigger[2] → Get the country[2] → Work out the key[2] →
        Another tax with this key?[2] → Is there one?[2] → Untick Duplicate name[2] → Write the Tax key[2]
OK  0a. a Tax key another tax holds, written through the API: refused (resultCode 11)
OK  0d. renamed to TEST Percent 3: Tax key '' Duplicate name True, run status [3]
        G: status 3 cause 6666 中止 :: … → Tick Duplicate name[2] → Clear the Tax key[2] →
        Stop — a duplicate gets no key[3]
OK  0c. renamed back to TEST Duplicate Probe: Tax key 'MY|sale||TEST Duplicate Probe' Duplicate name False,
        run status [2]
OK  0e. an unchanged Tax Name re-sent with a new Description: key kept, Duplicate name False — the search
        excludes the record that started the run
OK  0f. a tax whose Tax Type is None: Tax key '' Duplicate name False, 0 runs in 40 s
OK  0g. the roll-up with no tax:  the line is 100.00 at 0%, total 100.00; the invoice reads 100.00 / 0.00 /
        100.00 / 100.00
OK  0g. the roll-up with TEST Percent 3: the line is 100.00 at 3%, total 103.00; the invoice reads 100.00 /
        3.00 / 103.00 / 103.00
```

**0f is the new one.** Odoo skips `_constrains_name` when `type_tax_use = 'none'`, and G's trigger condition
does the same: a None-typed tax started **no run at all** in forty seconds, holds no key and is not marked.

### For the UI test (§3)

1. **The form.** Nineteen controls in §1's order; the *Advanced Options* divider renders as a heading; Tax Name
   is the title; **Duplicate name** is read-only and absent from the create form; **Tax key** is invisible.
2. **The defaults on a new tax**: Tax Type *Sales*, Tax Computation *Percentage*, Amount `0.0000`, Sequence 1,
   Formula `price_unit * 0.10`, Base Affected by Previous Taxes **ticked**, Active **ticked**, Country
   **Malaysia**, Included in Price showing the placeholder *Default*. The API applies none of these, so this is
   the first sight of any of them.
3. **Amount's four decimals and its thousands separator** — 10% G must read `10.0000`. §1 also describes a `%`
   suffix, which is **not built**: confirm the reviewer is content without it.
4. **The six rules**, one computation at a time: *Group of Taxes* hides Amount, Tax Group, Included in Price,
   Affect Base and Base Affected; *Custom Formula* hides Amount and **shows Formula, required** (try to save
   without it); *Fixed* / *Percentage* / *Percentage Tax Included* show Amount and require Tax Group.
5. **The Taxes view**: 35 rows, six columns, the archived ones visible (Odoo draws them muted — HAP will not);
   sorted Sequence then created; the three quick filters — Tax Type and Tax Scope as *any of* dropdowns, Active
   as a checkbox (which has two states once used, and then looks empty while still filtering).
6. **Archive / Unarchive** on a tax, and the *Archived* view's 25 rows.
7. **Duplicate names** is empty. Then create a second *10% G* by hand — Sales, Goods, Malaysia — and watch it
   appear there within a few seconds with **Duplicate name** ticked and no Tax key, and the record log showing
   G's run. Mend it (rename) and watch it leave the view. **This is the one thing a person sees of §1's
   uniqueness rule.**
8. **A tax whose Tax Type is None** is never marked, whatever its name (`TEST Type None` is there).
9. **Products**: Sales Taxes under Sales Price, Purchase Taxes under Cost, both showing the seeded chips.
   **Open each picker** — a picker filter is browser-side only, so this is the only place it can be proved:
   Sales Taxes must offer **only Sales taxes**, Purchase Taxes only Purchases taxes. **Note whether the
   archived taxes are offered** — they will be, because §1's domain names only Tax Type; if the reviewer wants
   Odoo's behaviour, `tax_picker` takes one more condition (*Active is checked*).
10. **Chart of Accounts**: Default Taxes under Type, empty on every account, its picker offering all 35.
11. **Invoice Lines / an invoice's Lines tab**: the **Total** column after Subtotal, in the subtable *and* in
    the standalone list. Open INV/2026/00001 and read its three lines: 7,192.00 → 7,911.20, 2,880.00 →
    3,168.00, 1,360.00 → 1,496.00.
12. **§1's open question 1, the half the CLI cannot answer**: on an **open** invoice, add a tax to a line and
    watch whether **Tax rate** and **Total** move before the record is saved. 10 §3 found a 汇总 over a **子表**
    holds only the saved rows; if the same is true here, Total lags by one save while the form is open and
    catches up on save. Nothing gates a save on it, so either answer is acceptable — but it belongs in the
    record.
13. **The roll-up, in the browser**: add a product line to a draft invoice and watch Untaxed Amount, **Tax**,
    Total and Amount Due all follow — including **Tax**, which has been a frozen seeded figure since 16
    September. Then delete the line and watch them follow back (the delete workflow is the second roll-up).
14. **Automation B's tax fill**: create a line on a **customer** invoice with a product and no account, and
    confirm it is given both the Account *and* the product's **Sales Taxes**; the same on a **vendor bill** for
    **Purchase Taxes**; and a line with **no product** on a journal entry, which must take the journal's
    default account and **no tax**. Then change an existing line's Product and confirm the taxes change with
    the account.
15. **A section and a note** on an invoice must show neither Taxes nor Total (the rule now hides both).
16. **Roles** (Select Role at the foot of the sidebar): Taxes is **visible to all four** and writable only by
    Accounting Administrator — the other three see no **+ Record** button, and a tax opens as plain text. The
    Taxes picker on a line must offer **no + Record** for them either.
17. **The sidebar**: Taxes sits between Chart of Accounts and Journals, with the percent icon.

## 3 · Test list

Run in the Nocoly UI on **18 September 2026**, reading every stored value back with the hap CLI. **19 pass, 3
fixed during the test, 1 not isolated.** The three fixes were made and re-checked the same day; nothing was left
broken and nothing was deleted.

| # | Test | Result |
|---|---|---|
| 1 | **The sidebar** — Taxes sits in **Invoicing**, between Chart of Accounts and Journals | **Pass.** The group reads Chart of Accounts · **Taxes** · Journals · Payment Terms · Payment Term Lines · Invoices · Invoice Lines, which is Odoo's own Configuration ▸ Accounting order |
| 2 | **The *Taxes* table** — Odoo's six columns, three views, three quick filters | **Pass.** Tax Name · Description · Tax Type · Tax Scope · Label on Invoices · Active; tabs *Taxes · Archived · Duplicate names*; filters Tax Type, Tax Scope, Active. `Total 39 record(s)` — the 35 seeded and four `TEST` |
| 3 | **The order** — `_order = 'sequence, id'` | **Pass.** 0% NA · 0% NA · 5% G · 6% S · 8% S · 8% S H · 10% G · 25 Per Card · X Per Litre G … — the tenant's list read screen-for-screen |
| 4 | **Active** matches the tenant | **Pass.** Ten ticked, 25 clear; *6% S*, *25 Per Card* and the schedule taxes archived, *EX* active |
| 5 | **The form** reads in §1's order, with the *Advanced Options* divider | **Pass.** Tax Name \| Tax Type · Tax Computation \| Amount · Sequence · Description \| Label on Invoices — divider — Tax Scope \| Tax Group · Country \| Included in Price · Affect Base \| Base Affected · Active \| Duplicate name · Legal Notes. **Tax key is not on it** |
| 6 | **Amount** carries Odoo's four decimals | **Pass.** 10% G reads **10.0000**, as it does on casimir |
| 7 | **Tax Group** offers the tenant's ten group names | **Pass.** SST 5% · SST 6% · SST 8% · SST 10% · SST 25 Per Card · SST X Per Litre · SST X Per Kilogram · SST X % · Not Applicable · Exempt |
| 8 | **Country** is a Relation to Countries, required, defaulting to Malaysia | **Pass.** Every seeded tax reads *Malaysia*; a new record starts there |
| 9 | **Rule 1** — Amount hidden unless the computation is Fixed, Percentage or Percentage Tax Included | **Pass.** Switching a new record to *Group of Taxes* takes Amount off the form; *X Per Kilogram G*, a Custom Formula tax, has no Amount either |
| 10 | **Rule 2** — Formula shown and required only for Custom Formula | **Pass.** Hidden on 10% G; on *X Per Kilogram G* it is present, starred and reads **`quantity * 0.01`** — the tenant's own formula |
| 11 | **Rule 3** — Tax Group hidden for a Group of Taxes | **Pass.** Advanced Options drops to Tax Scope alone |
| 12 | **Duplicate name** is read-only, and off the create form | **Pass.** Greyed on the record; the Create Record dialog does not carry it |
| 13 | **A duplicate typed into the form** | **Pass, within §1's stated ceiling.** A second *TEST Duplicate Probe* (Sales, no scope, Malaysia) **saved** — "Submitted successfully" — and within fifteen seconds had **no Tax key** and **Duplicate name ticked**, while the first kept `MY\|sale\|\|TEST Duplicate Probe` and its clear box. HAP cannot refuse the save; it marks it |
| 14 | **The *Duplicate names* view** | **Pass.** One row — the record from test 13 — with Tax Name · Tax Type · Tax Scope · Country · Duplicate name. It was empty before the test and is the only thing in it after |
| 15 | **The *Archived* view** | **Pass.** Exactly the **25** archived taxes, and none of the four `TEST` records, which are active |
| 16 | **Products** carry the tenant's taxes in Odoo's order | **Pass.** Ergonomic Office Chair reads Product Type · Sales Price · **Sales Taxes 10% G** · Unit · Cost · **Purchase Taxes 0% NA**; Implementation Consulting reads **8% S** / **0% NA**. All 14 read back correct |
| 17 | **The Sales Taxes picker** is filtered to Sales taxes | **Pass.** It offers 10% G SC, 5% G SC, 8% S OU, the two TEST probes … and no purchase tax. It **also offers archived taxes** — a difference, below |
| 18 | **Chart of Accounts** has Default Taxes, empty | **Pass.** Under Type, `tax_ids`, `[]` on every account — as on the tenant, where not one account has a default tax |
| 19 | **The arithmetic, end to end** | **Pass.** A line's **Taxes → Tax rate (汇总) → Total → the invoice's four amounts** all follow. On INV/2026/00001's chair line: Taxes *10% G*, Tax rate **10.0000**, Subtotal 7 192.00, Total **7 911.20**. On a `TEST` line: adding *10% G* to a 10.00 line moved it to 11.00 and its invoice from untaxed 110.00 / tax — / total 110.00 to **110.00 / 1.00 / 111.00**; taking the tax off moved it back |
| 20 | **The three seeded documents** land on the tenant's own figures | **Pass.** SCG-PO-88213 104 603.20 / **10 460.32** / 115 063.52 · INV/2026/00001 11 432.00 / **1 143.20** / 12 575.20 · STL-2026-0042 180 000.00 / **14 400.00** / 194 400.00. Read on screen and through the CLI. **06's Tax is no longer a seeded figure** |
| 21 | **Setting a tax from a line's own panel inside the invoice** | **Not isolated.** Before the fix in test 23 the field was not on the panel at all; after it the browser could not be steered to the row panel twice running (screenshot timeouts, and a click that opened the row menu instead). The arithmetic it would prove was driven through the CLI in test 19 and is sound. Worth one pass by the reviewer |
| 22 | The five Dropdowns' display style | **Fixed during the test.** Tax Type and Tax Scope drew in the table as **progress-bar sliders**, not text. `advancedSetting.showtype` was `"2"` — on a type 11 that is the progress style, not "a dropdown list" as the builder's comment claimed. All thirteen Dropdowns elsewhere in the app carry `"0"`; the five were set to `"0"` and now read as plain text, like Chart of Accounts' Type and like Odoo |
| 23 | The Taxes column inside an invoice | **Fixed during the test.** The *Lines* subtable and the standalone *Lines* view had gained **Total** but not **Taxes**, so the Invoice Lines tab showed a line's tax-inclusive amount with no way to see or change the tax that made it — and the line's row panel, which draws the subtable's columns, had no Taxes field. Odoo's own tab has the column. Added to both lists between Discount (%) and Subtotal, which is Odoo's order |
| 24 | The remark block on the Invoices tab | **Fixed during the test.** It still read *"Untaxed Amount, Tax, Total and Amount Due are read-only figures seeded from the tenant … Taxes themselves need the Taxes bundle"* — false on both counts since 07 and this bundle. Rewritten by a new `taxes.py note` step, with `invoices.py`'s own spec brought into line so its check stays honest |

### The self-check, re-run after the fixes

`taxes.py selfcheck` was re-run at the end of the UI test and **reported three DIFFs that were not defects**. The
cause is worth recording, because it will happen again to any worksheet whose duplicate check is exercised
through the UI:

The selfcheck finds its probe record **by name**, and test 13 left a *second* record called `TEST Duplicate
Probe` behind — which is exactly what the house rule asks for. A `{name: rowid}` map then keeps whichever record
came last, so the run drove the **marked** record instead of its own probe, and probes 0c and 0e read that
record's `('', True)` and called it a difference. **Workflow G behaved correctly in every probe**; only the
harness was confused about which record it was looking at.

`rowid_of` now resolves the probe to **the record that holds its key** and prints a note when the name is
shared. Re-run, the self-check is **OK on all seven probes**:

```
note: 2 taxes are named 'TEST Duplicate Probe'; the probe is the one holding its key
OK  0a. a Tax key another tax holds, written through the API: refused (resultCode 11)
OK  0c. renamed back to TEST Duplicate Probe, a free name: key 'MY|sale||TEST Duplicate Probe', Duplicate name False, status [2]
OK  0d. renamed to TEST Percent 3: Duplicate name ticked, the key cleared, the run stopped at the abort, status [3]
OK  0e. an unchanged Tax Name re-sent with a new Description: key kept, not marked — the search excludes its own record
OK  0f. a tax whose Tax Type is None: no key, not marked, 0 runs in 40 s
OK  0g. the roll-up with no tax: 100.00 at 0.0%, total 100.00; the invoice reads 100.00 / 0.00 / 100.00 / 100.00
OK  0g. the roll-up with TEST Percent 3: 100.00 at 3.0%, total 103.00; the invoice reads 100.00 / 3.00 / 103.00 / 103.00
```

### Differences from Odoo seen in testing

| # | Difference | Why |
|---|---|---|
| 1 | **A duplicate name is marked, not refused.** Odoo raises *"Tax names must be unique!"* and the record never exists; here it saves and is marked a few seconds later | §1's stated ceiling. HAP's *No duplicates* is one field and Odoo's key is five; a workflow runs after the save, so it can catch but not refuse. Bundle 5 measured this and the owner took it |
| 2 | **The Sales Taxes and Purchase Taxes pickers on a product offer archived taxes.** Odoo's product domain is `[('type_tax_use','=','sale')]` on an `active_test`-on field, so an archived tax is not offered | §1 named only the Tax Type domain, so only that was built. One more condition on the picker would close it — the owner's call, since the same behaviour is **right** on an invoice line, where Odoo's own context is `{'active_test': False}` |
| 3 | **A roll-up writes `0.00` where Tax used to be empty.** A document whose lines carry no tax now reads *0.00* rather than a blank | The workflow always writes the figure. Odoo shows a blank tax line rather than a zero. Harmless, and arguably more honest than an empty amount |
| 4 | **Only a Percentage tax contributes.** A Fixed, Percentage-Tax-Included or Custom Formula tax on a line adds **nothing** to the rate | §1, and the 汇总's own filter. Every active tax on this tenant is a Percentage, so nothing real is lost; a Fixed tax would need `quantity × amount`, which is a different formula, and Percentage Tax Included a different one again |
| 5 | **Tax Group is a Dropdown, not a relation** | §1 › *Not built now*. Odoo's Tax Groups menu is `base.group_no_one`, and the tenant's ten groups differ only in the name |

### Test records left in the worksheet

| Worksheet | Record | Why |
|---|---|---|
| Taxes | `TEST Duplicate Probe` ×2 — one with its key, one marked | Test 13. The marked one is what the *Duplicate names* view is for; deleting it needs the owner's approval |
| Taxes | `TEST Fixed 7`, `TEST Percent 3` | The build's own `measure` probes for §1's two roll-up questions |
| Invoice Lines | `TEST B category account` | Test 19 put *10% G* on it and **took it off again**; the line and its invoice read exactly as bundle 2 left them (110.00 / 0.00 / 110.00 — the Tax was blank before, see difference 3) |
