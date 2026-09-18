# 13 · Taxes

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Invoicing** |
| Worksheet | Taxes |
| Odoo model | `account.tax` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: fields, the raw arch of every view *and of the three modules that extend the form*, the actions and their menus, the access list, all 35 taxes, all 10 tax groups, all 36 repartition lines, the company's tax settings, the taxes of all 14 products, the `tax_ids` of every account and of all 31 invoice lines — extracted read-only to `nocoly/reference/odoo-19.4/account.tax.md`; the records themselves are `nocoly/data/casimir-taxes.json`. Behaviour the tenant cannot show is read from the Odoo 19.0 source in this repo: `addons/account/models/account_tax.py`, `account_tax_views.xml`, `account_account.py`, `account_move_line.py`, `product.py`, `addons/account/security/ir.model.access.csv`, `account_security.xml` |
| Phase | 1 — **bundle 6 of 6, the last** (Product Categories · Chart of Accounts · Payment Terms · Countries · States · **Taxes**) |
| Status | §1 written 18 Sep 2026 |

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
| 1 | Tax Name | `name` | Text · **title field** | yes | — | **Not *No duplicates*.** Odoo's constraint is the five-way (company, name, type, scope, country) — *0% NA* is both a Sales tax and a Purchase tax, and fourteen of the 35 names are shared by two records. See *Rules* |
| 2 | Tax Type | `type_tax_use` | Dropdown | yes | **Sales** | Sales · Purchases · None. Odoo's help as the description: "Determines where the tax is selectable. Note: 'None' means a tax can't be used by itself, however it can still be used in a group." |
| 3 | Tax Scope | `tax_scope` | Dropdown | — | — | Goods · Services. **Empty means both** — five of the 35 leave it empty |
| 4 | Tax Computation | `amount_type` | Dropdown | yes | **Percentage** | Group of Taxes · Fixed · Percentage · Percentage Tax Included · **Custom Formula**. The last is `account_tax_python`, installed on this tenant; three archived taxes use it |
| 5 | Amount | `amount` | Number, **4 decimals** | yes | 0 | Odoo's `float(16, 4)`: 10% G reads **10.0000** on the form, with a `%` after it unless the computation is Fixed. Platform thousands separator (`thousandth` "0"), as Odoo formats a float |
| 6 | Formula | `formula` | Text | — | `price_unit * 0.10` | `account_tax_python`. Odoo shows it only when Tax Computation is Custom Formula and requires it there — a rule, below. Every tax carries the module default whether it reads it or not |
| 7 | Description | `description` | Text | — | — | **Odoo's is Html; ours is Text.** Every one of the 35 holds a single short plain line inside one `<div>` — *SST 10%*, *Not Applicable* — and it is a list column, where a rich-text cell is unreadable. Recorded as a difference |
| 8 | Label on Invoices | `invoice_label` | Text | — | — | What prints on the document. Odoo falls back to the name when it is empty (`tax_label`); four of the 35 are empty |
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
over `name|type|scope|computation|amount|active|description|label|group` and the sum of the amounts — **35
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
